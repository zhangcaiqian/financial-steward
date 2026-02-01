"""AKShare price provider for fund/ETF NAV."""
from __future__ import annotations

import time
from datetime import date
from typing import Optional, Tuple

import akshare as ak
import pandas as pd

from .price_provider import PriceProvider


class AksharePriceProvider(PriceProvider):
    """Fetch latest available NAV or close price via AKShare."""

    def __init__(self, request_delay: float = 0.5):
        self.request_delay = request_delay

    def get_latest_nav(self, fund_code: str, fund_type: str) -> Tuple[date, float]:
        if fund_type == "etf":
            return self._get_etf_nav(fund_code)
        if fund_type == "open":
            return self._get_open_fund_nav(fund_code)

        # Fallback for unknown types
        try:
            return self._get_open_fund_nav(fund_code)
        except Exception:
            return self._get_etf_nav(fund_code)

    def _get_open_fund_nav(self, fund_code: str) -> Tuple[date, float]:
        time.sleep(self.request_delay)
        func = getattr(ak, "fund_open_fund_info_em", None)
        if func is None:
            raise RuntimeError("AKShare missing fund_open_fund_info_em")

        df = func(symbol=fund_code, indicator="单位净值走势")
        return _extract_latest_nav(df)

    def _get_etf_nav(self, fund_code: str) -> Tuple[date, float]:
        time.sleep(self.request_delay)
        candidates = [
            ("fund_etf_fund_daily_em", {"symbol": fund_code}),
            ("fund_etf_fund_info_em", {"symbol": fund_code}),
        ]
        last_error: Optional[Exception] = None
        for name, kwargs in candidates:
            func = getattr(ak, name, None)
            if func is None:
                continue
            try:
                df = func(**kwargs)
                return _extract_latest_nav(df)
            except Exception as exc:
                last_error = exc
                continue
        if last_error:
            raise last_error
        raise RuntimeError("No AKShare ETF interface available")


def _extract_latest_nav(df: pd.DataFrame) -> Tuple[date, float]:
    if df is None or df.empty:
        raise ValueError("Empty NAV dataframe")

    date_col = _find_column(df, ["净值日期", "日期", "date", "Date"])
    value_col = _find_column(df, ["单位净值", "净值", "收盘", "收盘价", "close", "Close"])

    if date_col is None or value_col is None:
        raise ValueError("Cannot detect date/nav columns")

    data = df[[date_col, value_col]].copy()
    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
    data = data.dropna(subset=[date_col, value_col])
    if data.empty:
        raise ValueError("NAV dataframe has no valid rows")

    data = data.sort_values(date_col)
    latest = data.iloc[-1]
    nav_date = latest[date_col].date()
    nav_value = float(latest[value_col])
    return nav_date, nav_value


def _find_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    for name in candidates:
        if name in df.columns:
            return name
    return None
