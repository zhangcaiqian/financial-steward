"""Persisted rebalance plans and batch scheduling."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from .db import get_session
from .models import (
    CashAccount,
    Fund,
    Holding,
    NavPrice,
    PortfolioSettings,
    RebalanceBatch,
    RebalancePlan,
    RebalanceTrade,
)
from .rebalance import generate_rebalance_plan


def create_rebalance_plan(
    batch_interval_days: int = 7,
    recalc_each_batch: bool = True,
) -> RebalancePlan:
    session = get_session()
    try:
        plan_data = generate_rebalance_plan()
        settings = session.query(PortfolioSettings).first()
        if settings is None:
            raise RuntimeError("Portfolio settings missing")

        plan = RebalancePlan(
            total_assets=plan_data["total_assets"],
            cash_balance=plan_data["cash_balance"],
            cash_target=plan_data["cash_target"],
            should_rebalance=plan_data["should_rebalance"],
            status="pending",
            recalc_each_batch=recalc_each_batch,
        )
        session.add(plan)
        session.flush()

        batches = []
        for batch_no in range(1, settings.dca_batches + 1):
            due_at = datetime.utcnow() + timedelta(days=(batch_no - 1) * batch_interval_days)
            batch = RebalanceBatch(
                plan_id=plan.id,
                batch_no=batch_no,
                due_at=due_at,
                status="pending",
            )
            session.add(batch)
            batches.append(batch)
        session.flush()

        batch_lookup = {batch.batch_no: batch for batch in batches}
        for trade in plan_data["trades"]:
            batch = batch_lookup.get(trade.batch) if trade.batch else None
            session.add(
                RebalanceTrade(
                    plan_id=plan.id,
                    batch_id=batch.id if batch else None,
                    fund_id=trade.fund_id,
                    action=trade.action,
                    amount=trade.amount,
                    status="planned",
                )
            )

        settings.last_rebalance_at = datetime.utcnow()
        session.commit()
        return plan
    finally:
        session.close()


def get_plan(plan_id: int) -> RebalancePlan:
    session = get_session()
    try:
        plan = session.get(RebalancePlan, plan_id)
        if plan is None:
            raise ValueError("Plan not found")
        return plan
    finally:
        session.close()


def serialize_plan(plan_id: int) -> dict:
    session = get_session()
    try:
        plan = session.get(RebalancePlan, plan_id)
        if plan is None:
            raise ValueError("Plan not found")
        batches = (
            session.query(RebalanceBatch)
            .filter(RebalanceBatch.plan_id == plan_id)
            .order_by(RebalanceBatch.batch_no.asc())
            .all()
        )
        trades = (
            session.query(RebalanceTrade)
            .filter(RebalanceTrade.plan_id == plan_id)
            .all()
        )
        fund_lookup = {fund.id: fund for fund in session.query(Fund).all()}
        batch_lookup = {batch.id: batch for batch in batches}
        return {
            "id": plan.id,
            "status": plan.status,
            "total_assets": float(plan.total_assets),
            "cash_balance": float(plan.cash_balance),
            "cash_target": float(plan.cash_target),
            "should_rebalance": plan.should_rebalance,
            "recalc_each_batch": plan.recalc_each_batch,
            "created_at": plan.created_at.isoformat(),
            "batches": [
                {
                    "id": batch.id,
                    "batch_no": batch.batch_no,
                    "due_at": batch.due_at.isoformat(),
                    "status": batch.status,
                }
                for batch in batches
            ],
            "trades": [
                {
                    "id": trade.id,
                    "action": trade.action,
                    "amount": float(trade.amount),
                    "status": trade.status,
                    "batch_no": batch_lookup.get(trade.batch_id).batch_no if trade.batch_id else None,
                    "fund_code": fund_lookup.get(trade.fund_id).code if trade.fund_id in fund_lookup else "",
                    "fund_name": fund_lookup.get(trade.fund_id).name if trade.fund_id in fund_lookup else "",
                }
                for trade in trades
            ],
        }
    finally:
        session.close()


def list_due_batches(limit: int = 20):
    session = get_session()
    try:
        now = datetime.utcnow()
        return (
            session.query(RebalanceBatch)
            .filter(
                RebalanceBatch.status == "pending",
                RebalanceBatch.due_at <= now,
            )
            .order_by(RebalanceBatch.due_at.asc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()


def mark_due_batches_ready() -> int:
    session = get_session()
    try:
        now = datetime.utcnow()
        batches = (
            session.query(RebalanceBatch)
            .filter(
                RebalanceBatch.status == "pending",
                RebalanceBatch.due_at <= now,
            )
            .all()
        )
        count = 0
        for batch in batches:
            batch.status = "ready"
            session.query(RebalanceTrade).filter(
                RebalanceTrade.batch_id == batch.id,
                RebalanceTrade.status == "planned",
            ).update({"status": "ready"})
            count += 1
        session.commit()
        return count
    finally:
        session.close()


def execute_batch(plan_id: int, batch_no: int) -> int:
    session = get_session()
    try:
        batch = (
            session.query(RebalanceBatch)
            .filter(
                RebalanceBatch.plan_id == plan_id,
                RebalanceBatch.batch_no == batch_no,
            )
            .one_or_none()
        )
        if batch is None:
            raise ValueError("Batch not found")
        if batch.status not in ("ready", "pending"):
            return 0

        trades = (
            session.query(RebalanceTrade)
            .filter(RebalanceTrade.batch_id == batch.id)
            .all()
        )
        cash = session.query(CashAccount).first()
        if cash is None:
            cash = CashAccount(balance=0)
            session.add(cash)
            session.flush()

        executed = 0
        for trade in trades:
            fund = session.get(Fund, trade.fund_id)
            if fund is None:
                continue
            nav = (
                session.query(NavPrice)
                .filter(NavPrice.fund_id == fund.id, NavPrice.is_latest.is_(True))
                .one_or_none()
            )
            if nav is None or float(nav.nav) <= 0:
                trade.status = "blocked"
                continue

            shares_delta = float(trade.amount) / float(nav.nav)
            holding = session.query(Holding).filter(Holding.fund_id == fund.id).one_or_none()
            if holding is None:
                holding = Holding(fund_id=fund.id, shares=0, avg_cost=0)
                session.add(holding)
                session.flush()

            if trade.action == "buy":
                max_affordable = float(cash.balance)
                amount = min(float(trade.amount), max_affordable)
                if amount <= 0:
                    trade.status = "blocked"
                    continue
                shares_delta = amount / float(nav.nav)
                total_cost = float(holding.shares) * float(holding.avg_cost) + amount
                holding.shares = float(holding.shares) + shares_delta
                holding.avg_cost = total_cost / float(holding.shares) if holding.shares > 0 else 0
                cash.balance = float(cash.balance) - amount
            else:
                max_sell_value = float(holding.shares) * float(nav.nav)
                amount = min(float(trade.amount), max_sell_value)
                if amount <= 0:
                    trade.status = "blocked"
                    continue
                shares_delta = amount / float(nav.nav)
                holding.shares = max(0.0, float(holding.shares) - shares_delta)
                cash.balance = float(cash.balance) + amount

            trade.status = "executed"
            trade.executed_at = datetime.utcnow()
            executed += 1

        batch.status = "executed"
        batch.executed_at = datetime.utcnow()

        remaining = (
            session.query(RebalanceTrade)
            .filter(
                RebalanceTrade.plan_id == plan_id,
                RebalanceTrade.status.in_(["planned", "ready"]),
            )
            .count()
        )
        plan = session.get(RebalancePlan, plan_id)
        if plan and remaining == 0:
            plan.status = "completed"

        session.commit()
        return executed
    finally:
        session.close()


def recalculate_remaining_plan(plan_id: int, batch_interval_days: int = 7) -> RebalancePlan:
    session = get_session()
    try:
        plan = session.get(RebalancePlan, plan_id)
        if plan is None:
            raise ValueError("Plan not found")

        executed_batches = (
            session.query(RebalanceBatch)
            .filter(
                RebalanceBatch.plan_id == plan_id,
                RebalanceBatch.status == "executed",
            )
            .count()
        )
        settings = session.query(PortfolioSettings).first()
        if settings is None:
            raise RuntimeError("Portfolio settings missing")

        remaining_batches = max(1, settings.dca_batches - executed_batches)
        new_plan_data = generate_rebalance_plan(dca_batches_override=remaining_batches)

        plan.total_assets = new_plan_data["total_assets"]
        plan.cash_balance = new_plan_data["cash_balance"]
        plan.cash_target = new_plan_data["cash_target"]
        plan.should_rebalance = new_plan_data["should_rebalance"]

        # Remove pending batches/trades
        session.query(RebalanceTrade).filter(
            RebalanceTrade.plan_id == plan_id,
            RebalanceTrade.status.in_(["planned", "ready"]),
        ).delete(synchronize_session=False)
        session.query(RebalanceBatch).filter(
            RebalanceBatch.plan_id == plan_id,
            RebalanceBatch.status.in_(["pending", "ready"]),
        ).delete(synchronize_session=False)
        session.flush()

        batches = []
        for idx in range(1, remaining_batches + 1):
            batch_no = executed_batches + idx
            due_at = datetime.utcnow() + timedelta(days=(idx - 1) * batch_interval_days)
            batch = RebalanceBatch(
                plan_id=plan.id,
                batch_no=batch_no,
                due_at=due_at,
                status="pending",
            )
            session.add(batch)
            batches.append(batch)
        session.flush()

        batch_lookup = {idx + 1: batch for idx, batch in enumerate(batches)}
        for trade in new_plan_data["trades"]:
            batch = batch_lookup.get(trade.batch) if trade.batch else None
            session.add(
                RebalanceTrade(
                    plan_id=plan.id,
                    batch_id=batch.id if batch else None,
                    fund_id=trade.fund_id,
                    action=trade.action,
                    amount=trade.amount,
                    status="planned",
                )
            )

        session.commit()
        return plan
    finally:
        session.close()
