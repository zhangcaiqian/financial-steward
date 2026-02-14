"""Agent tools."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

import akshare as ak
import httpx

from src.portfolio.rebalance import generate_rebalance_plan
from src.portfolio.service import list_funds_with_cycles, update_settings
from src.portfolio.db import get_session
from src.portfolio.models import Cycle, CycleTarget
from src.collector import MacroDataCollector
from src.analyzer import EconomicCycleAnalyzer

logger = logging.getLogger(__name__)

def tool_get_portfolio_summary(_: Dict[str, Any]) -> Dict[str, Any]:
    plan = generate_rebalance_plan()
    return {
        "total_assets": plan["total_assets"],
        "cash_balance": plan["cash_balance"],
        "cash_target": plan["cash_target"],
        "cycle_allocations": plan["cycle_allocations"],
        "funds": [
            {
                "code": f.code,
                "name": f.name,
                "value": f.value,
                "target_weight": f.target_weight,
                "delta_value": f.delta_value,
            }
            for f in plan["funds"]
        ],
    }


def tool_get_rebalance_suggestion(_: Dict[str, Any]) -> Dict[str, Any]:
    plan = generate_rebalance_plan()
    return {
        "should_rebalance": plan["should_rebalance"],
        "trades": [
            {
                "action": t.action,
                "code": t.code,
                "name": t.name,
                "amount": t.amount,
                "batch": t.batch,
                "cycle_weights": t.cycle_weights,
            }
            for t in plan["trades"]
        ],
    }


def tool_get_cycle_targets(_: Dict[str, Any]) -> Dict[str, Any]:
    session = get_session()
    try:
        cycles = {cycle.id: cycle.code for cycle in session.query(Cycle).all()}
        targets = session.query(CycleTarget).filter(CycleTarget.is_active.is_(True)).all()
        return {cycles.get(target.cycle_id, str(target.cycle_id)): float(target.target_weight) for target in targets}
    finally:
        session.close()


def tool_get_settings(_: Dict[str, Any]) -> Dict[str, Any]:
    settings = update_settings({})
    return {
        "rebalance_frequency_days": settings.rebalance_frequency_days,
        "rebalance_threshold_ratio": float(settings.rebalance_threshold_ratio),
        "cash_target_ratio": float(settings.cash_target_ratio),
        "dca_batches": settings.dca_batches,
    }


def tool_get_fund_list(_: Dict[str, Any]) -> Dict[str, Any]:
    funds = list_funds_with_cycles()
    return {"funds": funds}


def tool_get_economic_cycle(_: Dict[str, Any]) -> Dict[str, Any]:
    collector = MacroDataCollector()
    data = collector.collect_all()
    analyzer = EconomicCycleAnalyzer(data)
    report = analyzer.generate_report()
    return report


def tool_get_index_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    symbol = payload.get("symbol")
    market = payload.get("market", "cn")
    start = payload.get("start_date")
    end = payload.get("end_date")

    if not symbol:
        return {"error": "missing_symbol"}

    df = None
    try:
        logger.info("Third-party API call akshare symbol=%s market=%s", symbol, market)
        if market == "cn":
            df = ak.stock_zh_index_daily_em(symbol=symbol)
        elif market == "hk":
            df = ak.stock_hk_index_daily_em(symbol=symbol)
        elif market == "bond":
            df = ak.bond_zh_hs_daily(symbol=symbol)
        else:
            df = ak.stock_zh_index_daily_em(symbol=symbol)
    except Exception as exc:
        logger.exception("Third-party API call akshare failed symbol=%s market=%s", symbol, market)
        return {"error": "akshare_failed", "detail": str(exc)}

    if df is None or df.empty:
        return {"error": "no_data"}

    rename_map = {}
    for col in df.columns:
        lower = col.lower()
        if col in ("日期", "时间"):
            rename_map[col] = "date"
        elif lower in ("date", "time"):
            rename_map[col] = "date"
        else:
            rename_map[col] = lower
    df = df.rename(columns=rename_map)
    if "date" in df.columns:
        df["date"] = df["date"].astype(str)
    if start:
        df = df[df["date"] >= start]
    if end:
        df = df[df["date"] <= end]

    records = df.tail(200).to_dict(orient="records")
    return {"symbol": symbol, "market": market, "records": records}


def tool_web_search(payload: Dict[str, Any]) -> Dict[str, Any]:
    query = payload.get("query")
    if not query:
        return {"error": "missing_query"}

    base_url = payload.get("base_url") or os.getenv("SEARCH_BASE_URL", "http://localhost:8080")
    url = f"{base_url}/search"
    params = {"q": query, "format": "json"}

    try:
        logger.info("Third-party API call web_search base_url=%s query=%s", base_url, query)
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.exception("Third-party API call web_search failed base_url=%s query=%s", base_url, query)
        return {"error": "search_failed", "detail": str(exc)}

    results = [
        {
            "title": item.get("title"),
            "url": item.get("url"),
            "content": item.get("content"),
        }
        for item in data.get("results", [])
    ]
    return {"query": query, "results": results}


TOOLS = {
    "get_portfolio_summary": tool_get_portfolio_summary,
    "get_rebalance_suggestion": tool_get_rebalance_suggestion,
    "get_cycle_targets": tool_get_cycle_targets,
    "get_settings": tool_get_settings,
    "get_fund_list": tool_get_fund_list,
    "get_economic_cycle": tool_get_economic_cycle,
    "get_index_data": tool_get_index_data,
    "web_search": tool_web_search,
}


TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "get_portfolio_summary",
            "description": "获取当前资产配置概览（总资产、现金、周期分布、基金偏离）",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rebalance_suggestion",
            "description": "生成当前调仓建议（买卖金额与批次）",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cycle_targets",
            "description": "获取四周期目标权重",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_settings",
            "description": "获取组合参数设置",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fund_list",
            "description": "获取用户维护的基金列表与周期分类",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_economic_cycle",
            "description": "判断当前经济周期并返回分析报告",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_index_data",
            "description": "查询指数数据（A股/港股/债券），返回行情记录",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "market": {"type": "string", "enum": ["cn", "hk", "bond"]},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "联网搜索，返回搜索摘要结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "base_url": {"type": "string"},
                },
                "required": ["query"],
            },
        },
    },
]
