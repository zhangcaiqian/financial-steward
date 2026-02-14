"""FastAPI application for portfolio management."""
from __future__ import annotations

import os
import json
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
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
    get_prompt,
    list_funds_with_cycles,
    update_cycle_targets,
    update_fund,
    update_settings,
    upsert_fund,
    upsert_holding,
    upsert_prompt,
)
from src.agent.agent import AgentSession
from src.api.schemas import (
    CashAdjustment,
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
    return list_funds_with_cycles()


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


@app.websocket("/ws/agent")
async def agent_ws(websocket: WebSocket):
    await websocket.accept()
    session = AgentSession()

    async def on_delta(message_id: str, chunk: str):
        await websocket.send_json({"type": "message.delta", "message_id": message_id, "delta": {"content": chunk}})

    async def on_tool_event(payload: dict):
        await websocket.send_json(payload)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type in ("user", "user.message"):
                content = data.get("content", "")
                message_id = str(uuid.uuid4())
                await websocket.send_json(
                    {"type": "message.start", "message": {"id": message_id, "role": "assistant"}}
                )
                try:
                    result = await session.handle_user_message(
                        content,
                        lambda chunk: on_delta(message_id, chunk),
                        on_tool_event,
                    )
                    await websocket.send_json(
                        {
                            "type": "message.end",
                            "message_id": message_id,
                            "message": {
                                "role": "assistant",
                                "content": result.get("text", ""),
                                "blocks": result.get("blocks", []),
                            },
                        }
                    )
                except Exception as exc:
                    await websocket.send_json({"type": "error", "message": str(exc)})
            elif msg_type in ("action", "action.call"):
                action = data.get("action")
                params = data.get("params", {})
                from src.agent.tools import TOOLS

                tool = TOOLS.get(action)
                if not tool:
                    await websocket.send_json({"type": "error", "message": "Unknown action"})
                    continue
                result = tool(params)
                message_id = str(uuid.uuid4())
                await websocket.send_json(
                    {
                        "type": "message.end",
                        "message_id": message_id,
                        "message": {
                            "role": "assistant",
                            "content": f"已执行动作：{action}",
                            "blocks": [
                                {"type": "text", "content": f"已执行动作：{action}"},
                                {"type": "text", "content": json.dumps(result, ensure_ascii=False)},
                            ],
                        },
                    }
                )
            else:
                await websocket.send_json({"type": "error", "message": "Unsupported message type"})
    except WebSocketDisconnect:
        return
