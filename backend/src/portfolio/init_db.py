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

DEFAULT_PROMPT_NAME = "chat_extraction"
DEFAULT_PROMPT = (
    "你是资产配置系统的信息抽取器。"
    "从用户输入中抽取结构化信息，不做数学计算。"
    "返回严格符合 JSON schema 的 JSON。"
    "trade_date 使用 YYYY-MM-DD 格式；无法确认时留空字符串。"
    "如果无法判断 intent，返回 unknown 并说明 reason。"
)


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

        prompt = session.query(PromptTemplate).filter(PromptTemplate.name == DEFAULT_PROMPT_NAME).one_or_none()
        if prompt is None:
            session.add(PromptTemplate(name=DEFAULT_PROMPT_NAME, content=DEFAULT_PROMPT))

        cash_account = session.query(CashAccount).first()
        if cash_account is None:
            session.add(CashAccount(balance=0))

        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    init_db(seed=True)
