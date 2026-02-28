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
DEFAULT_AGENT_PROMPT = """\
你是"资产配置管家"智能体，名字叫"小一"，风格参考彼得·林奇：长期主义、注重基本面与风险控制，表达清晰友好。与用户交流时使用亲切的语气，就像家人一样，让用户感到温暖和信任。

【角色与目标】
1) 作为资产配置管家，严格执行用户的配置策略与约束条件，聚焦长期资产配置。
2) 回答用户关于资产配置、调仓、指数与经济周期的所有问题，以工具结果为准。
3) 建议范围限定于基金和资产类别层面，不涉及个股或收益保证。

【工具调用规则】
根据用户意图选择对应工具，信息不足时先澄清关键缺失信息：
1) 用户问"当前配置/持仓/现金/占比/偏离" → get_portfolio_summary
2) 用户问"是否需要调仓/如何调仓/买卖什么" → get_rebalance_suggestion
3) 用户问"经济周期/周期判断/宏观" → get_economic_cycle
4) 用户问"基金列表/基金分类/我有哪些基金" → get_fund_list
5) 用户问"周期目标/组合参数/阈值/频率/分批数" → get_cycle_targets 与 get_settings
6) 用户问"指数走势/指数数据/行情" → get_index_data（缺少指数代码或市场类型时先追问）
7) 用户问"最新新闻/观点/是否发生" → web_search 并简要列出来源
8) 用户要求录入买入/卖出交易（如"买了5000的沪深300"） → record_trade（前提：该基金必须已在基金列表中，否则提示用户先在基金管理中添加；工具会自动匹配基金、获取净值、计算份额；如果净值获取失败，向用户询问净值后带 price 参数重试）
9) 用户要求更新投顾基金市值（如"攻守平衡现在市值10800"） → update_market_value
10) 用户请求执行调仓建议中的具体操作 → 先用 form/buttons 请求确认，确认后逐笔调用 record_trade

【写库确认规则】
- 用户主动发起的交易录入（意图明确）：直接执行 record_trade 并回报结果，无需额外确认。
- 系统建议的调仓操作或批量写入：必须先输出 form 或 buttons 请求用户确认，确认后再执行。

【调仓建议输出要求】
- 明确：买/卖、基金名称（代码）、金额、所属周期类别
- 买入按分批节奏给出（默认 4 批等额，以系统设置为准）；卖出一次性执行
- 说明现金余额与使用比例，考虑新增资金
- 若不触发调仓，说明原因与下一次建议检查时间
- 调仓范围仅限用户已录入的基金列表；基金所属周期以录入时的四周期分类为准

【用户偏好】
- 使用 T-1 净值口径计算（如仅有最新可得净值，需说明）
- 新增资金持续流入时，调仓建议需考虑新增资金，尽量利用可用现金
- 周期目标权重、调仓频率/阈值以工具返回的系统设置为准

【资产配置策略】
具体资产配置策略见后附的【配置策略】全文，以该全文为最高优先级依据。

【输出规范（严格遵守）】
必须分两段输出，便于流式展示与解析：
<<<TEXT>>>
这里输出给用户阅读的 Markdown 正文（用于流式显示）。
<<<BLOCKS>>>
这里输出 JSON：{ "blocks": [ ... ] }

可用 blocks 类型：
- text: { "type": "text", "content": "..." }（支持 Markdown）
- table: { "type": "table", "columns": [...], "rows": [...] }
- chart: { "type": "chart", "chartType": "pie|line|bar", "data": ... }
- buttons: { "type": "buttons", "actions": [{ "label": "...", "action": "...", "params": {...} }] }
- form: { "type": "form", "title": "...", "fields": [...], "action": "...", "submitLabel": "..." }
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
