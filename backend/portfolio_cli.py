"""CLI for portfolio management tasks."""
from __future__ import annotations

import argparse
import json

from src.env import load_env

load_env()

from src.portfolio.init_db import init_db
from src.portfolio.price_sync import sync_latest_navs
from src.portfolio.rebalance import generate_rebalance_plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Portfolio management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Create tables and seed defaults")
    subparsers.add_parser("sync-nav", help="Sync latest NAV prices")
    subparsers.add_parser("rebalance", help="Generate rebalance plan")

    args = parser.parse_args()
    if args.command == "init-db":
        init_db(seed=True)
        print("✅ Portfolio tables initialized")
        return
    if args.command == "sync-nav":
        count = sync_latest_navs()
        print(f"✅ NAV sync completed: {count} funds updated")
        return
    if args.command == "rebalance":
        plan = generate_rebalance_plan()
        print(json.dumps(_serialize_plan(plan), ensure_ascii=False, indent=2))
        return


def _serialize_plan(plan: dict) -> dict:
    funds = []
    for snapshot in plan.get("funds", []):
        funds.append(
            {
                "code": snapshot.code,
                "name": snapshot.name,
                "value": snapshot.value,
                "target_weight": snapshot.target_weight,
                "delta_value": snapshot.delta_value,
                "cycle_weights": snapshot.cycle_weights,
            }
        )
    trades = []
    for trade in plan.get("trades", []):
        trades.append(
            {
                "action": trade.action,
                "code": trade.code,
                "name": trade.name,
                "amount": trade.amount,
                "batch": trade.batch,
                "cycle_weights": trade.cycle_weights,
            }
        )
    return {
        "total_assets": plan.get("total_assets"),
        "cash_balance": plan.get("cash_balance"),
        "cash_target": plan.get("cash_target"),
        "cycle_allocations": plan.get("cycle_allocations"),
        "should_rebalance": plan.get("should_rebalance"),
        "funds": funds,
        "trades": trades,
    }


if __name__ == "__main__":
    main()
