"""Portfolio rebalance and DCA planning."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from .db import get_session
from .models import (
    CashAccount,
    Cycle,
    CycleTarget,
    Fund,
    FundCycleWeight,
    Holding,
    NavPrice,
    PortfolioSettings,
)


@dataclass
class FundSnapshot:
    fund_id: int
    code: str
    name: str
    fund_type: str
    shares: float
    nav: float
    value: float
    target_weight: float
    target_value: float
    delta_value: float
    cycle_weights: Dict[str, float]


@dataclass
class TradeSuggestion:
    action: str
    fund_id: int
    code: str
    name: str
    amount: float
    batch: Optional[int]
    cycle_weights: Dict[str, float]


def should_rebalance(
    settings: PortfolioSettings,
    fund_snapshots: List[FundSnapshot],
    now: Optional[datetime] = None,
) -> bool:
    if settings is None:
        return False

    now = now or datetime.utcnow()
    if settings.last_rebalance_at is None:
        return True

    elapsed_days = (now - settings.last_rebalance_at).days
    if elapsed_days >= settings.rebalance_frequency_days:
        return True

    threshold = float(settings.rebalance_threshold_ratio)
    total_value = sum(s.value for s in fund_snapshots)
    for snapshot in fund_snapshots:
        if snapshot.target_weight <= 0:
            continue
        current_weight = snapshot.value / max(1e-9, total_value)
        if abs(current_weight - snapshot.target_weight) >= threshold:
            return True
    return False


def generate_rebalance_plan(
    recalc_each_batch: bool = True,
    dca_batches_override: Optional[int] = None,
) -> Dict:
    session = get_session()
    try:
        settings = session.query(PortfolioSettings).first()
        if settings is None:
            raise RuntimeError("Portfolio settings not initialized")

        cash_account = session.query(CashAccount).first()
        cash_balance = float(cash_account.balance) if cash_account else 0.0

        cycle_map = {cycle.id: cycle.code for cycle in session.query(Cycle).all()}
        cycle_targets = _get_cycle_targets(session, cycle_map)
        fund_cycle_weights = _get_fund_cycle_weights(session, cycle_map)

        funds = session.query(Fund).filter(Fund.is_active.is_(True)).all()
        holdings = {h.fund_id: h for h in session.query(Holding).all()}
        navs = {p.fund_id: p for p in session.query(NavPrice).filter(NavPrice.is_latest.is_(True)).all()}

        fund_values = []
        for fund in funds:
            holding = holdings.get(fund.id)
            nav = navs.get(fund.id)
            shares = float(holding.shares) if holding else 0.0
            nav_value = float(nav.nav) if nav else 0.0
            value = shares * nav_value
            fund_values.append((fund, shares, nav_value, value))

        total_assets = cash_balance + sum(value for _, _, _, value in fund_values)

        fund_targets = _compute_fund_targets(cycle_targets, fund_cycle_weights)
        fund_snapshots = []
        for fund, shares, nav_value, value in fund_values:
            target_weight = fund_targets.get(fund.id, 0.0)
            target_value = total_assets * target_weight
            delta_value = target_value - value
            cycle_weights = fund_cycle_weights.get(fund.id, {})
            fund_snapshots.append(
                FundSnapshot(
                    fund_id=fund.id,
                    code=fund.code,
                    name=fund.name,
                    fund_type=fund.fund_type,
                    shares=shares,
                    nav=nav_value,
                    value=value,
                    target_weight=target_weight,
                    target_value=target_value,
                    delta_value=delta_value,
                    cycle_weights=cycle_weights,
                )
            )

        plan = {
            "total_assets": total_assets,
            "cash_balance": cash_balance,
            "cash_target": total_assets * float(settings.cash_target_ratio),
            "cycle_allocations": _compute_cycle_allocations(fund_snapshots),
            "funds": fund_snapshots,
            "trades": [],
            "should_rebalance": should_rebalance(settings, fund_snapshots),
        }

        if not plan["should_rebalance"]:
            return plan

        dca_batches = dca_batches_override or settings.dca_batches
        trades = _build_trade_plan(
            fund_snapshots,
            cash_balance=cash_balance,
            cash_target=plan["cash_target"],
            dca_batches=dca_batches,
            recalc_each_batch=recalc_each_batch,
        )
        plan["trades"] = trades
        return plan
    finally:
        session.close()


def _get_cycle_targets(session, cycle_map: Dict[int, str]) -> Dict[str, float]:
    targets = (
        session.query(CycleTarget)
        .filter(CycleTarget.is_active.is_(True))
        .all()
    )
    cycle_targets: Dict[str, float] = {}
    for target in targets:
        cycle_code = cycle_map.get(target.cycle_id, str(target.cycle_id))
        cycle_targets[cycle_code] = float(target.target_weight)
    return cycle_targets


def _get_fund_cycle_weights(session, cycle_map: Dict[int, str]) -> Dict[int, Dict[str, float]]:
    weights = session.query(FundCycleWeight).all()
    result: Dict[int, Dict[str, float]] = {}
    for weight in weights:
        cycle_code = cycle_map.get(weight.cycle_id, str(weight.cycle_id))
        result.setdefault(weight.fund_id, {})[cycle_code] = float(weight.weight)
    return result


def _compute_fund_targets(
    cycle_targets: Dict[str, float],
    fund_cycle_weights: Dict[int, Dict[str, float]],
) -> Dict[int, float]:
    if not cycle_targets:
        return {}

    target_by_fund: Dict[int, float] = {}
    for fund_id, cycle_weights in fund_cycle_weights.items():
        total = 0.0
        for cycle_code, weight in cycle_weights.items():
            total += cycle_targets.get(cycle_code, 0.0) * weight
        target_by_fund[fund_id] = total

    return _normalize_weights(target_by_fund)


def _normalize_weights(weights: Dict[int, float]) -> Dict[int, float]:
    total = sum(weights.values())
    if total <= 0:
        return weights
    return {key: value / total for key, value in weights.items()}


def _compute_cycle_allocations(fund_snapshots: List[FundSnapshot]) -> Dict[str, float]:
    cycle_values: Dict[str, float] = {}
    for snapshot in fund_snapshots:
        for cycle_code, weight in snapshot.cycle_weights.items():
            cycle_values[cycle_code] = cycle_values.get(cycle_code, 0.0) + snapshot.value * weight
    return cycle_values


def _build_trade_plan(
    fund_snapshots: List[FundSnapshot],
    cash_balance: float,
    cash_target: float,
    dca_batches: int,
    recalc_each_batch: bool,
) -> List[TradeSuggestion]:
    trades: List[TradeSuggestion] = []

    sells = [s for s in fund_snapshots if s.delta_value < 0]
    buys = [s for s in fund_snapshots if s.delta_value > 0]

    total_sell = sum(-s.delta_value for s in sells)
    total_buy = sum(s.delta_value for s in buys)
    cash_after_sell = cash_balance + total_sell
    available_cash = max(0.0, cash_after_sell - cash_target)
    buy_budget = min(total_buy, available_cash)

    for snapshot in sells:
        trades.append(
            TradeSuggestion(
                action="sell",
                fund_id=snapshot.fund_id,
                code=snapshot.code,
                name=snapshot.name,
                amount=abs(snapshot.delta_value),
                batch=None,
                cycle_weights=snapshot.cycle_weights,
            )
        )

    if buy_budget <= 0 or not buys:
        return trades

    batches = max(1, int(dca_batches))
    remaining = {s.fund_id: s.delta_value for s in buys}
    metadata = {s.fund_id: s for s in buys}
    for batch in range(1, batches + 1):
        remaining_total = sum(max(0.0, value) for value in remaining.values())
        if remaining_total <= 0:
            break

        budget = buy_budget / batches
        if budget > remaining_total:
            budget = remaining_total

        for fund_id, delta in list(remaining.items()):
            if delta <= 0:
                continue
            ratio = delta / remaining_total if remaining_total > 0 else 0
            amount = budget * ratio
            remaining[fund_id] = max(0.0, delta - amount)
            snapshot = metadata[fund_id]
            trades.append(
                TradeSuggestion(
                    action="buy",
                    fund_id=snapshot.fund_id,
                    code=snapshot.code,
                    name=snapshot.name,
                    amount=amount,
                    batch=batch,
                    cycle_weights=snapshot.cycle_weights,
                )
            )

        if recalc_each_batch:
            continue

    return trades
