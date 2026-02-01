"""Lightweight chat parser for portfolio actions."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, Optional

from .service import normalize_cycle_code


ACTION_BUY = ("买入", "申购")
ACTION_SELL = ("卖出", "赎回")


def parse_chat(text: str) -> Dict:
    text = text.strip()
    if not text:
        return {"intent": "unknown", "reason": "empty"}

    if _contains_any(text, ("入金", "存入", "充值", "加仓资金")):
        amount = _extract_amount(text)
        if amount is None:
            return {"intent": "cash", "ok": False, "reason": "missing_amount"}
        return {"intent": "cash", "ok": True, "data": {"amount": amount}}

    if _contains_any(text, ("新增基金", "添加基金", "录入基金")):
        return _parse_fund(text)

    if _contains_any(text, ("持仓", "份")):
        holding = _parse_holding(text)
        if holding:
            return {"intent": "holding", "ok": True, "data": holding}

    if _contains_any(text, ACTION_BUY + ACTION_SELL):
        transaction = _parse_transaction(text)
        if transaction:
            return {"intent": "transaction", "ok": True, "data": transaction}

    return {"intent": "unknown", "ok": False, "reason": "unmatched"}


def _parse_transaction(text: str) -> Optional[Dict]:
    action = None
    for word in ACTION_BUY:
        if word in text:
            action = "buy"
            break
    for word in ACTION_SELL:
        if word in text:
            action = "sell"
            break
    if action is None:
        return None

    fund_code = _extract_fund_code(text)
    if not fund_code:
        return None

    clean_text = text.replace(fund_code, "")
    clean_text = re.sub(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", "", clean_text)
    amount = _extract_amount(clean_text)
    shares = _extract_shares(text)

    trade_date = _extract_date(text)
    return {
        "fund_code": fund_code,
        "trade_type": action,
        "amount": amount if amount is not None else 0.0,
        "shares": shares,
        "trade_date": trade_date,
        "note": text,
    }


def _parse_holding(text: str) -> Optional[Dict]:
    fund_code = _extract_fund_code(text)
    if not fund_code:
        return None
    shares = _extract_shares(text)
    if shares is None:
        return None
    return {"fund_code": fund_code, "shares": shares, "avg_cost": 0.0}


def _parse_fund(text: str) -> Dict:
    fund_code = _extract_fund_code(text)
    name = _extract_quoted(text) or _extract_name_hint(text, fund_code)
    if not fund_code or not name:
        return {"intent": "fund", "ok": False, "reason": "missing_code_or_name"}

    fund_type = "etf" if ("ETF" in text or "场内" in text) else "open"
    cycle_weights = _extract_cycle_weights(text)
    return {
        "intent": "fund",
        "ok": True,
        "data": {
            "code": fund_code,
            "name": name,
            "fund_type": fund_type,
            "currency": "CNY",
            "cycle_weights": cycle_weights,
        },
    }


def _extract_fund_code(text: str) -> Optional[str]:
    match = re.search(r"\b\d{6}\b", text)
    if match:
        return match.group(0)
    return None


def _extract_amount(text: str) -> Optional[float]:
    matches = re.findall(r"\d+(?:\.\d+)?", text)
    if not matches:
        return None
    return float(matches[-1])


def _extract_shares(text: str) -> Optional[float]:
    match = re.search(r"(\d+(?:\.\d+)?)\s*份", text)
    if match:
        return float(match.group(1))
    return None


def _extract_date(text: str) -> Optional[datetime]:
    match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text)
    if match:
        year, month, day = match.groups()
        return datetime(int(year), int(month), int(day))
    return None


def _extract_quoted(text: str) -> Optional[str]:
    match = re.search(r"[\"“”']([^\"“”']+)[\"“”']", text)
    if match:
        return match.group(1)
    return None


def _extract_name_hint(text: str, fund_code: Optional[str]) -> Optional[str]:
    if not fund_code:
        return None
    parts = text.replace(fund_code, "").split()
    for part in parts:
        if "基金" in part or "ETF" in part:
            return part
    return None


def _extract_cycle_weights(text: str) -> Dict[str, float]:
    weights: Dict[str, float] = {}
    for name in ("强复苏", "弱复苏", "弱衰退", "强衰退"):
        pattern = rf"{name}\s*(\d+(?:\.\d+)?)%"
        match = re.search(pattern, text)
        if match:
            weights[normalize_cycle_code(name)] = float(match.group(1)) / 100.0
    if not weights:
        for name in ("强复苏", "弱复苏", "弱衰退", "强衰退"):
            if name in text:
                weights[normalize_cycle_code(name)] = 1.0
                break
    return weights


def _contains_any(text: str, keys: tuple) -> bool:
    return any(key in text for key in keys)
