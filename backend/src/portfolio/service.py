"""Service layer for portfolio CRUD operations."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from .db import get_session
from .models import (
    CashAccount,
    ChatMessage,
    Cycle,
    CycleTarget,
    Fund,
    FundCycleWeight,
    Holding,
    NavPrice,
    PromptTemplate,
    PortfolioSettings,
    Transaction,
)


CYCLE_ALIAS = {
    "强复苏": "strong_recovery",
    "弱复苏": "weak_recovery",
    "弱衰退": "weak_recession",
    "强衰退": "strong_recession",
}


def normalize_cycle_code(code: str) -> str:
    if not code:
        return code
    return CYCLE_ALIAS.get(code, code)


def get_or_create_cash(session) -> CashAccount:
    cash = session.query(CashAccount).first()
    if cash is None:
        cash = CashAccount(balance=0)
        session.add(cash)
        session.flush()
    return cash


def upsert_fund(
    code: str,
    name: str,
    fund_type: str,
    currency: str,
    cycle_weights: Optional[Dict[str, float]] = None,
) -> Fund:
    session = get_session()
    try:
        fund = session.query(Fund).filter(Fund.code == code).one_or_none()
        if fund is None:
            fund = Fund(code=code, name=name, fund_type=fund_type, currency=currency)
            session.add(fund)
            session.flush()
        else:
            fund.name = name
            fund.fund_type = fund_type
            fund.currency = currency

        if cycle_weights is not None:
            _set_fund_cycle_weights(session, fund, cycle_weights)

        session.commit()
        return fund
    finally:
        session.close()


def update_fund(fund_id: int, updates: dict) -> Fund:
    session = get_session()
    try:
        fund = session.get(Fund, fund_id)
        if fund is None:
            raise ValueError("Fund not found")
        if "name" in updates and updates["name"]:
            fund.name = updates["name"]
        if "fund_type" in updates and updates["fund_type"]:
            fund.fund_type = updates["fund_type"]
        if "currency" in updates and updates["currency"]:
            fund.currency = updates["currency"]
        if "cycle_weights" in updates and updates["cycle_weights"] is not None:
            _set_fund_cycle_weights(session, fund, updates["cycle_weights"])
        session.commit()
        return fund
    finally:
        session.close()


def _set_fund_cycle_weights(session, fund: Fund, cycle_weights: Dict[str, float]) -> None:
    cycle_lookup = {cycle.code: cycle for cycle in session.query(Cycle).all()}
    incoming_cycle_ids = set()
    for raw_code, weight in cycle_weights.items():
        cycle_code = normalize_cycle_code(raw_code)
        cycle = cycle_lookup.get(cycle_code)
        if cycle is None:
            cycle = Cycle(code=cycle_code, name=cycle_code)
            session.add(cycle)
            session.flush()
            cycle_lookup[cycle_code] = cycle
        existing = (
            session.query(FundCycleWeight)
            .filter(FundCycleWeight.fund_id == fund.id, FundCycleWeight.cycle_id == cycle.id)
            .one_or_none()
        )
        if existing:
            existing.weight = weight
        else:
            session.add(
                FundCycleWeight(fund_id=fund.id, cycle_id=cycle.id, weight=weight)
            )
        incoming_cycle_ids.add(cycle.id)

    existing_weights = (
        session.query(FundCycleWeight)
        .filter(FundCycleWeight.fund_id == fund.id)
        .all()
    )
    for existing in existing_weights:
        if existing.cycle_id not in incoming_cycle_ids:
            session.delete(existing)


def find_fund(keyword: str) -> Fund:
    """Find an active fund by code or name (exact match first, then fuzzy)."""
    session = get_session()
    try:
        fund = (
            session.query(Fund)
            .filter(Fund.is_active.is_(True), Fund.code == keyword)
            .one_or_none()
        )
        if fund:
            return fund

        fund = (
            session.query(Fund)
            .filter(Fund.is_active.is_(True), Fund.name == keyword)
            .one_or_none()
        )
        if fund:
            return fund

        matches = (
            session.query(Fund)
            .filter(Fund.is_active.is_(True), Fund.name.contains(keyword))
            .all()
        )
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            names = ", ".join(f"{f.name}({f.code})" for f in matches)
            raise ValueError(f"匹配到多只基金: {names}，请提供更精确的名称或代码")

        raise ValueError(f"未找到基金: {keyword}")
    finally:
        session.close()


def record_trade(keyword: str, amount: float, trade_type: str = "buy", price: Optional[float] = None) -> dict:
    """Unified trade entry: find fund by keyword, auto-fetch NAV, record transaction.

    If *price* is provided, it is used directly; otherwise the latest NAV is
    looked up from DB or fetched from AKShare.
    """
    from .price_sync import get_or_fetch_nav

    fund = find_fund(keyword)
    trade_type_lower = trade_type.lower()
    is_buy = trade_type_lower in ("buy", "purchase", "申购", "买入")

    if fund.fund_type in MANUAL_FUND_TYPES:
        return _record_advisory_trade(fund, amount, is_buy)

    nav_value = price
    if nav_value is None:
        try:
            _, nav_value = get_or_fetch_nav(fund.code, fund.fund_type)
        except Exception as exc:
            raise ValueError(
                f"无法自动获取 {fund.name}({fund.code}) 的净值: {exc}。"
                f"请提供净值(price)后重试。"
            )

    tx = create_transaction(
        fund_code=fund.code,
        trade_type=trade_type_lower,
        amount=amount,
        shares=None,
        price=nav_value,
        trade_date=None,
        note=None,
    )
    shares = float(tx.shares) if tx.shares else amount / nav_value
    return {
        "fund_code": fund.code,
        "fund_name": fund.name,
        "trade_type": trade_type_lower,
        "amount": amount,
        "price": nav_value,
        "shares": round(shares, 4),
    }


def _record_advisory_trade(fund: Fund, amount: float, is_buy: bool) -> dict:
    from .price_sync import upsert_manual_nav
    from datetime import date as date_type

    session = get_session()
    try:
        holding = session.query(Holding).filter(Holding.fund_id == fund.id).one_or_none()
        if holding is None:
            holding = Holding(fund_id=fund.id, shares=1, avg_cost=0)
            session.add(holding)
            session.flush()

        nav_price = (
            session.query(NavPrice)
            .filter(NavPrice.fund_id == fund.id, NavPrice.is_latest.is_(True))
            .one_or_none()
        )
        current_value = float(nav_price.nav) if nav_price else 0.0
        current_cost = float(holding.avg_cost)

        if is_buy:
            new_cost = current_cost + amount
            new_value = current_value + amount
        else:
            new_cost = max(0, current_cost - amount)
            new_value = max(0, current_value - amount)

        holding.avg_cost = new_cost
        holding.shares = 1
        session.commit()
    finally:
        session.close()

    upsert_manual_nav(fund.code, new_value, date_type.today())

    return {
        "fund_code": fund.code,
        "fund_name": fund.name,
        "trade_type": "buy" if is_buy else "sell",
        "amount": amount,
        "total_cost": new_cost,
        "market_value": new_value,
    }


MANUAL_FUND_TYPES = {"advisory"}


def list_funds() -> list[Fund]:
    session = get_session()
    try:
        return session.query(Fund).all()
    finally:
        session.close()


def list_funds_with_cycles() -> list[dict]:
    session = get_session()
    try:
        funds = session.query(Fund).all()
        cycle_lookup = {cycle.id: cycle.code for cycle in session.query(Cycle).all()}
        weights = session.query(FundCycleWeight).all()
        weights_map: dict[int, list[dict]] = {}
        for weight in weights:
            weights_map.setdefault(weight.fund_id, []).append(
                {
                    "cycle": cycle_lookup.get(weight.cycle_id, str(weight.cycle_id)),
                    "weight": float(weight.weight),
                }
            )
        result = []
        for fund in funds:
            cycles = weights_map.get(fund.id, [])
            primary_cycle = None
            if cycles:
                primary_cycle = max(cycles, key=lambda item: item.get("weight", 0)).get("cycle")
            result.append(
                {
                    "id": fund.id,
                    "code": fund.code,
                    "name": fund.name,
                    "fund_type": fund.fund_type,
                    "currency": fund.currency,
                    "cycles": cycles,
                    "primary_cycle": primary_cycle,
                }
            )
        return result
    finally:
        session.close()


def upsert_holding(code: str, shares: float, avg_cost: float) -> Holding:
    session = get_session()
    try:
        fund = session.query(Fund).filter(Fund.code == code).one_or_none()
        if fund is None:
            raise ValueError("Fund not found")
        holding = session.query(Holding).filter(Holding.fund_id == fund.id).one_or_none()
        if holding is None:
            holding = Holding(fund_id=fund.id, shares=shares, avg_cost=avg_cost)
            session.add(holding)
        else:
            holding.shares = shares
            holding.avg_cost = avg_cost
        session.commit()
        return holding
    finally:
        session.close()


def adjust_cash(amount: float, note: Optional[str] = None) -> CashAccount:
    session = get_session()
    try:
        cash = get_or_create_cash(session)
        cash.balance = float(cash.balance) + amount
        session.commit()
        return cash
    finally:
        session.close()


def create_transaction(
    fund_code: str,
    trade_type: str,
    amount: float,
    shares: Optional[float],
    price: Optional[float],
    trade_date: Optional[datetime],
    note: Optional[str],
) -> Transaction:
    session = get_session()
    try:
        fund = session.query(Fund).filter(Fund.code == fund_code).one_or_none()
        if fund is None:
            raise ValueError("Fund not found")

        if shares is None and price:
            shares = amount / price

        holding = session.query(Holding).filter(Holding.fund_id == fund.id).one_or_none()
        if holding is None:
            holding = Holding(fund_id=fund.id, shares=0, avg_cost=0)
            session.add(holding)
            session.flush()

        cash = get_or_create_cash(session)
        trade_type_lower = trade_type.lower()
        if trade_type_lower in ("buy", "purchase", "申购", "买入"):
            if shares:
                total_cost = holding.shares * holding.avg_cost + amount
                new_shares = holding.shares + shares
                holding.avg_cost = total_cost / new_shares if new_shares > 0 else 0
                holding.shares = new_shares
            cash.balance = float(cash.balance) - amount
        elif trade_type_lower in ("sell", "redeem", "赎回", "卖出"):
            if shares:
                holding.shares = max(0, holding.shares - shares)
            cash.balance = float(cash.balance) + amount
        else:
            raise ValueError("Unsupported trade type")

        tx = Transaction(
            fund_id=fund.id,
            trade_type=trade_type_lower,
            amount=amount,
            shares=shares,
            price=price,
            trade_date=trade_date or datetime.utcnow(),
            note=note,
        )
        session.add(tx)
        session.commit()
        return tx
    finally:
        session.close()


def update_cycle_targets(targets: Dict[str, float]) -> None:
    session = get_session()
    try:
        cycle_lookup = {cycle.code: cycle for cycle in session.query(Cycle).all()}
        for raw_code, weight in targets.items():
            cycle_code = normalize_cycle_code(raw_code)
            cycle = cycle_lookup.get(cycle_code)
            if cycle is None:
                cycle = Cycle(code=cycle_code, name=cycle_code)
                session.add(cycle)
                session.flush()
                cycle_lookup[cycle_code] = cycle
            session.query(CycleTarget).filter(
                CycleTarget.cycle_id == cycle.id, CycleTarget.is_active.is_(True)
            ).update({"is_active": False})
            session.add(CycleTarget(cycle_id=cycle.id, target_weight=weight, is_active=True))
        session.commit()
    finally:
        session.close()


def update_settings(updates: Dict) -> PortfolioSettings:
    session = get_session()
    try:
        settings = session.query(PortfolioSettings).first()
        if settings is None:
            settings = PortfolioSettings(
                rebalance_frequency_days=180,
                rebalance_threshold_ratio=0.05,
                cash_target_ratio=0.05,
                dca_batches=4,
            )
            session.add(settings)
            session.flush()
        for key, value in updates.items():
            if value is not None and hasattr(settings, key):
                setattr(settings, key, value)
        session.commit()
        return settings
    finally:
        session.close()


def get_latest_nav(fund_id: int) -> Optional[NavPrice]:
    session = get_session()
    try:
        return session.query(NavPrice).filter(NavPrice.fund_id == fund_id, NavPrice.is_latest.is_(True)).one_or_none()
    finally:
        session.close()


def save_chat_message(text: str, parsed_json: Optional[dict], status: str, provider: Optional[str], model: Optional[str]) -> ChatMessage:
    session = get_session()
    try:
        msg = ChatMessage(
            text=text,
            parsed_json=parsed_json,
            status=status,
            provider=provider,
            model=model,
        )
        session.add(msg)
        session.commit()
        return msg
    finally:
        session.close()


def mark_chat_applied(chat_id: int) -> None:
    session = get_session()
    try:
        msg = session.get(ChatMessage, chat_id)
        if msg:
            msg.status = "applied"
            msg.applied_at = datetime.utcnow()
            session.commit()
    finally:
        session.close()


def list_chat_history(limit: int = 50) -> list[ChatMessage]:
    session = get_session()
    try:
        return (
            session.query(ChatMessage)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()


def get_chat_message(chat_id: int) -> Optional[ChatMessage]:
    session = get_session()
    try:
        return session.get(ChatMessage, chat_id)
    finally:
        session.close()


def upsert_prompt(name: str, content: str) -> PromptTemplate:
    session = get_session()
    try:
        prompt = session.query(PromptTemplate).filter(PromptTemplate.name == name).one_or_none()
        if prompt is None:
            prompt = PromptTemplate(name=name, content=content)
            session.add(prompt)
        else:
            prompt.content = content
            prompt.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(prompt)
        session.expunge(prompt)
        return prompt
    finally:
        session.close()


def get_prompt(name: str) -> Optional[PromptTemplate]:
    session = get_session()
    try:
        return session.query(PromptTemplate).filter(PromptTemplate.name == name).one_or_none()
    finally:
        session.close()
