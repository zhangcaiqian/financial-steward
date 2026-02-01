"""FastAPI application for portfolio management."""
from __future__ import annotations

import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.env import load_env

load_env()

from src.portfolio.init_db import init_db
from src.portfolio.price_sync import sync_latest_navs
from src.portfolio.rebalance import generate_rebalance_plan
from src.portfolio.rebalance_plan import (
    create_rebalance_plan,
    execute_batch,
    mark_due_batches_ready,
    recalculate_remaining_plan,
    serialize_plan,
)
from src.portfolio.scheduler import start_batch_scheduler
from src.portfolio.service import (
    adjust_cash,
    create_transaction,
    get_chat_message,
    get_prompt,
    list_funds,
    list_chat_history,
    mark_chat_applied,
    save_chat_message,
    update_cycle_targets,
    update_fund,
    update_settings,
    upsert_fund,
    upsert_holding,
    upsert_prompt,
)
from src.portfolio.llm_extractor import extract_chat_intent
from src.api.schemas import (
    CashAdjustment,
    ChatConfirmRequest,
    ChatIngestRequest,
    CycleTargetsUpdate,
    FundCreate,
    FundUpdate,
    HoldingUpsert,
    PortfolioSettingsUpdate,
    PromptUpdate,
    RebalanceRequest,
    TransactionCreate,
)


app = FastAPI(title="Financial Steward API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("PORTFOLIO_CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    init_db(seed=True)
    start_batch_scheduler()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/funds")
def create_fund(payload: FundCreate) -> dict:
    fund = upsert_fund(
        code=payload.code,
        name=payload.name,
        fund_type=payload.fund_type,
        currency=payload.currency,
        cycle_weights=payload.cycle_weights,
    )
    return {"id": fund.id, "code": fund.code, "name": fund.name}


@app.get("/funds")
def get_funds() -> list[dict]:
    funds = list_funds()
    return [{"id": fund.id, "code": fund.code, "name": fund.name, "fund_type": fund.fund_type} for fund in funds]


@app.put("/funds/{fund_id}")
def update_fund_api(fund_id: int, payload: FundUpdate) -> dict:
    fund = update_fund(fund_id, payload.model_dump(exclude_unset=True))
    return {"id": fund.id, "code": fund.code, "name": fund.name}


@app.post("/holdings")
def upsert_holdings(payload: HoldingUpsert) -> dict:
    holding = upsert_holding(payload.fund_code, payload.shares, payload.avg_cost)
    return {"id": holding.id, "fund_id": holding.fund_id, "shares": float(holding.shares)}


@app.post("/cash/deposit")
def deposit_cash(payload: CashAdjustment) -> dict:
    cash = adjust_cash(payload.amount, payload.note)
    return {"balance": float(cash.balance)}


@app.post("/cash/withdraw")
def withdraw_cash(payload: CashAdjustment) -> dict:
    cash = adjust_cash(-payload.amount, payload.note)
    return {"balance": float(cash.balance)}


@app.post("/transactions")
def create_transaction_api(payload: TransactionCreate) -> dict:
    tx = create_transaction(
        fund_code=payload.fund_code,
        trade_type=payload.trade_type,
        amount=payload.amount,
        shares=payload.shares,
        price=payload.price,
        trade_date=payload.trade_date,
        note=payload.note,
    )
    return {"id": tx.id}


@app.put("/cycles/targets")
def update_targets(payload: CycleTargetsUpdate) -> dict:
    update_cycle_targets(payload.targets)
    return {"ok": True}


@app.put("/settings")
def update_settings_api(payload: PortfolioSettingsUpdate) -> dict:
    settings = update_settings(payload.model_dump(exclude_unset=True))
    return {
        "rebalance_frequency_days": settings.rebalance_frequency_days,
        "rebalance_threshold_ratio": float(settings.rebalance_threshold_ratio),
        "cash_target_ratio": float(settings.cash_target_ratio),
        "dca_batches": settings.dca_batches,
    }


@app.get("/settings")
def get_settings_api() -> dict:
    settings = update_settings({})
    return {
        "rebalance_frequency_days": settings.rebalance_frequency_days,
        "rebalance_threshold_ratio": float(settings.rebalance_threshold_ratio),
        "cash_target_ratio": float(settings.cash_target_ratio),
        "dca_batches": settings.dca_batches,
    }


@app.get("/cycles/targets")
def get_cycle_targets_api() -> dict:
    from src.portfolio.db import get_session
    from src.portfolio.models import Cycle, CycleTarget

    session = get_session()
    try:
        cycles = {cycle.id: cycle.code for cycle in session.query(Cycle).all()}
        targets = session.query(CycleTarget).filter(CycleTarget.is_active.is_(True)).all()
        return {cycles.get(target.cycle_id, str(target.cycle_id)): float(target.target_weight) for target in targets}
    finally:
        session.close()


@app.post("/portfolio/rebalance")
def create_rebalance(payload: RebalanceRequest) -> dict:
    if payload.persist:
        plan = create_rebalance_plan(
            batch_interval_days=payload.batch_interval_days,
            recalc_each_batch=payload.recalc_each_batch,
        )
        return {"plan_id": plan.id, "status": plan.status, "should_rebalance": plan.should_rebalance}

    plan = generate_rebalance_plan()
    return {
        "should_rebalance": plan["should_rebalance"],
        "total_assets": plan["total_assets"],
        "cash_balance": plan["cash_balance"],
        "cash_target": plan["cash_target"],
        "funds": [snapshot.__dict__ for snapshot in plan["funds"]],
        "trades": [trade.__dict__ for trade in plan["trades"]],
    }


@app.get("/portfolio/summary")
def portfolio_summary() -> dict:
    plan = generate_rebalance_plan()
    return {
        "should_rebalance": plan["should_rebalance"],
        "total_assets": plan["total_assets"],
        "cash_balance": plan["cash_balance"],
        "cash_target": plan["cash_target"],
        "cycle_allocations": plan["cycle_allocations"],
        "funds": [snapshot.__dict__ for snapshot in plan["funds"]],
    }


@app.get("/portfolio/rebalance/{plan_id}")
def rebalance_detail(plan_id: int) -> dict:
    return serialize_plan(plan_id)


@app.post("/portfolio/rebalance/{plan_id}/execute/{batch_no}")
def execute_rebalance_batch(plan_id: int, batch_no: int) -> dict:
    executed = execute_batch(plan_id, batch_no)
    return {"executed": executed}


@app.post("/portfolio/rebalance/{plan_id}/recalculate")
def recalc_plan(plan_id: int) -> dict:
    plan = recalculate_remaining_plan(plan_id)
    return {"plan_id": plan.id, "status": plan.status}


@app.post("/portfolio/rebalance/mark-due")
def mark_due() -> dict:
    count = mark_due_batches_ready()
    return {"ready_batches": count}


@app.post("/prices/sync")
def sync_navs() -> dict:
    count = sync_latest_navs()
    return {"updated": count}


@app.post("/chat/ingest")
def chat_ingest(payload: ChatIngestRequest) -> dict:
    result = extract_chat_intent(payload.text)
    if not result.get("ok"):
        msg = save_chat_message(payload.text, None, "failed", None, None)
        return {"ok": False, "error": result.get("error"), "detail": result.get("detail"), "chat_id": msg.id}

    parsed = result.get("parsed", {})
    msg = save_chat_message(payload.text, parsed, "parsed", result.get("provider"), result.get("model"))
    return {"ok": True, "parsed": parsed, "chat_id": msg.id}


@app.post("/chat/confirm")
def chat_confirm(payload: ChatConfirmRequest) -> dict:
    msg = get_chat_message(payload.chat_id)
    if msg is None:
        raise HTTPException(status_code=404, detail="Chat message not found")
    if msg.status == "applied":
        return {"ok": True, "chat_id": msg.id, "status": "applied"}

    parsed = msg.parsed_json or {}
    intent = parsed.get("intent")
    data = parsed.get("data", {}) if isinstance(parsed.get("data"), dict) else {}
    if intent == "cash":
        cash = adjust_cash(float(data.get("amount", 0)))
        mark_chat_applied(msg.id)
        return {"ok": True, "chat_id": msg.id, "cash_balance": float(cash.balance)}
    if intent == "holding":
        holding = upsert_holding(data.get("fund_code", ""), data.get("shares", 0), data.get("avg_cost", 0))
        mark_chat_applied(msg.id)
        return {"ok": True, "chat_id": msg.id, "holding_id": holding.id}
    if intent == "transaction":
        trade_date = data.get("trade_date")
        if isinstance(trade_date, str) and trade_date:
            try:
                trade_date = datetime.fromisoformat(trade_date)
            except ValueError:
                trade_date = None
        tx = create_transaction(
            fund_code=data.get("fund_code", ""),
            trade_type=data.get("trade_type", ""),
            amount=float(data.get("amount", 0.0)),
            shares=data.get("shares"),
            price=data.get("price"),
            trade_date=trade_date,
            note=data.get("note"),
        )
        mark_chat_applied(msg.id)
        return {"ok": True, "chat_id": msg.id, "transaction_id": tx.id}
    if intent == "fund":
        fund = upsert_fund(
            code=data.get("fund_code") or data.get("code", ""),
            name=data.get("fund_name") or data.get("name", ""),
            fund_type=data.get("fund_type", "open"),
            currency=data.get("currency", "CNY"),
            cycle_weights=data.get("cycle_weights", {}),
        )
        mark_chat_applied(msg.id)
        return {"ok": True, "chat_id": msg.id, "fund_id": fund.id}

    raise HTTPException(status_code=400, detail="Unsupported chat intent")


@app.get("/chat/history")
def chat_history(limit: int = 50) -> list[dict]:
    rows = list_chat_history(limit)
    return [
        {
            "id": row.id,
            "text": row.text,
            "status": row.status,
            "parsed": row.parsed_json,
            "provider": row.provider,
            "model": row.model,
            "created_at": row.created_at.isoformat(),
            "applied_at": row.applied_at.isoformat() if row.applied_at else None,
        }
        for row in rows
    ]


@app.get("/prompts/{name}")
def get_prompt_api(name: str) -> dict:
    prompt = get_prompt(name)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"name": prompt.name, "content": prompt.content, "updated_at": prompt.updated_at.isoformat()}


@app.put("/prompts")
def update_prompt_api(payload: PromptUpdate) -> dict:
    prompt = upsert_prompt(payload.name, payload.content)
    return {"name": prompt.name, "updated_at": prompt.updated_at.isoformat()}
