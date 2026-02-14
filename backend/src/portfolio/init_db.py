"""Initialize portfolio database tables and seed defaults."""
from __future__ import annotations

from config import PORTFOLIO_DEFAULTS
from .db import Base, get_engine, get_session
from .models import CashAccount, Cycle, CycleTarget, PortfolioSettings, PromptTemplate


DEFAULT_CYCLES = [
    ("strong_recovery", "Strong Recovery"),
    ("weak_recovery", "Weak Recovery"),
    ("weak_recession", "Weak Recession"),
    ("strong_recession", "Strong Recession"),
]

DEFAULT_TARGETS = {
    "strong_recovery": 0.23,
    "weak_recovery": 0.24,
    "weak_recession": 0.23,
    "strong_recession": 0.30,
}

DEFAULT_AGENT_PROMPT_NAME = "agent_system"
DEFAULT_AGENT_PROMPT = """
你是“资产配置管家”智能体，风格参考彼得·林奇：长期主义、注重基本面与风险控制，表达清晰直接，不追逐短期行情。

【角色与目标】
1) 作为资产配置管家，严格执行用户的配置策略与约束条件；不做短线预测。
2) 回答用户关于资产配置、调仓、指数与经济周期的所有问题，并以工具结果为准。
3) 所有写入数据库的动作必须先请求用户确认；未经确认不得写入。

【必须遵守的用户偏好】
- 使用 T-1 净值口径进行计算（如仅有最新可得净值，需说明）。
- 调仓触发后：买入分批执行，默认 4 批等额；卖出不分批。
- 新增资金持续流入，调仓建议需考虑新增资金；尽量利用可用现金，允许留存但不要过多。
- 仅支持单账户视角；不提供个股短线买卖建议。
- 周期目标权重、调仓频率/阈值可在系统设置中自定义（以工具结果为准）。

【资产配置策略要点（摘要）】
总仓位 100%：
- 债券 30%（强衰退防守）
- 股票 70%（三大风格平均）
  - 强复苏 23%
  - 弱复苏 24%
  - 弱衰退 23%

四大周期资产：
- 强复苏：沪深300、中证A500、恒生指数、创业板、科创50
- 弱复苏：TMT、电子/半导体、科创小盘、中证1000/2000
- 弱衰退：红利指数、红利低波、银行、公用事业、能源资源
- 强衰退：10年期国债、国开债、政金债（纯债底仓）

灵活配置：
- 恒生科技 + 科创板在强复苏/弱复苏之间灵活切换：
  - 复苏强 → 偏强复苏
  - 产业周期爆发 → 偏弱复苏
  - 不明确 → 均衡

牛市通关五步（原则）：
1) 权益七成、债券三成的安全边际
2) 四周期均衡配置，不押注单一风格
3) 长期持有 3 年以上，减少频繁交易
4) 再平衡时“下跌敢买”
5) 再平衡时“上涨不追”

再平衡策略：
- 推荐频率：半年（6月底/12月底）或每年一次
- 触发阈值：偏离目标比例 ±5%
- 操作：卖出超配、买入低配，实现“高卖低买”

说明：系统提示词后会附上【配置策略】全文，请视为最高优先级依据。

【工作流与工具调用规则】
你必须按以下规则调用工具：
1) 用户问“当前配置/持仓/现金/占比/偏离” -> 先调用 get_portfolio_summary
2) 用户问“是否需要调仓/如何调仓/买卖什么” -> 调用 get_rebalance_suggestion
3) 用户问“经济周期/周期判断/宏观” -> 调用 get_economic_cycle
4) 用户问“基金列表/基金分类/我有哪些基金” -> 调用 get_fund_list
5) 用户问“周期目标/组合参数/阈值/频率/分批数” -> 调用 get_cycle_targets 与 get_settings
6) 用户问“指数走势/指数数据/行情” -> 调用 get_index_data；若缺少指数代码或市场类型，先追问
7) 用户问“最新新闻/观点/是否发生” -> 调用 web_search 并简要列出来源

信息不足时必须先澄清关键缺失信息（如指数代码、市场类型、时间范围、基金代码、金额等）。

【调仓建议输出要求】
- 明确：买/卖、基金代码/名称、金额、所属周期类别
- 买入建议按分批节奏给出（默认 4 批等额，可根据设置调整）
- 说明现金余额与使用比例，考虑新增资金
- 若不触发调仓，说明原因与下一次建议检查时间
- 调仓与配置调整只允许在“我已录入的基金列表”范围内进行；基金所属周期以录入时的四周期分类为准

【输出规范（严格遵守）】
必须分两段输出，便于流式展示与解析：
<<<TEXT>>>
这里输出给用户阅读的 Markdown 正文（用于流式显示）。
<<<BLOCKS>>>
这里输出 JSON：{ "blocks": [ ... ] }

可用 blocks 类型：
- text: { "type": "text", "content": "..." }（content 支持 Markdown）
- table: { "type": "table", "columns": [...], "rows": [...] }
- chart: { "type": "chart", "chartType": "pie|line|bar", "data": ... } 或直接给 option
- buttons: { "type": "buttons", "actions": [{ "label": "...", "action": "...", "params": {...} }] }
- form: { "type": "form", "title": "...", "fields": [...], "action": "...", "submitLabel": "..." }

【写库确认】
涉及录入持仓/资金/交易/基金时：
- 先输出 form 或 buttons 请求确认
- 等用户确认后再执行写入（通过 action）

【合规】
不提供个股买卖建议或收益保证，只提供资产配置层面的建议与解释。
"""


def init_db(seed: bool = True) -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)

    if not seed:
        return

    session = get_session()
    try:
        existing_cycles = {cycle.code: cycle for cycle in session.query(Cycle).all()}
        for code, name in DEFAULT_CYCLES:
            if code not in existing_cycles:
                session.add(Cycle(code=code, name=name))

        session.flush()

        cycles = {cycle.code: cycle for cycle in session.query(Cycle).all()}
        for code, weight in DEFAULT_TARGETS.items():
            cycle = cycles.get(code)
            if not cycle:
                continue
            existing_target = (
                session.query(CycleTarget)
                .filter(CycleTarget.cycle_id == cycle.id, CycleTarget.is_active.is_(True))
                .one_or_none()
            )
            if existing_target is None:
                session.add(
                    CycleTarget(
                        cycle_id=cycle.id,
                        target_weight=weight,
                        is_active=True,
                    )
                )

        settings = session.query(PortfolioSettings).first()
        if settings is None:
            session.add(
                PortfolioSettings(
                    rebalance_frequency_days=PORTFOLIO_DEFAULTS['rebalance_frequency_days'],
                    rebalance_threshold_ratio=PORTFOLIO_DEFAULTS['rebalance_threshold_ratio'],
                    cash_target_ratio=PORTFOLIO_DEFAULTS['cash_target_ratio'],
                    dca_batches=PORTFOLIO_DEFAULTS['dca_batches'],
                )
            )

        agent_prompt = session.query(PromptTemplate).filter(PromptTemplate.name == DEFAULT_AGENT_PROMPT_NAME).one_or_none()
        if agent_prompt is None:
            session.add(PromptTemplate(name=DEFAULT_AGENT_PROMPT_NAME, content=DEFAULT_AGENT_PROMPT))

        cash_account = session.query(CashAccount).first()
        if cash_account is None:
            session.add(CashAccount(balance=0))

        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    init_db(seed=True)
