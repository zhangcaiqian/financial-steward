"""Pydantic schemas for API."""
from __future__ import annotations

from datetime import date, datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class FundCreate(BaseModel):
    code: str
    name: str
    fund_type: str = "open"
    currency: str = "CNY"
    cycle_weights: Dict[str, float] = Field(default_factory=dict)


class FundUpdate(BaseModel):
    name: Optional[str] = None
    fund_type: Optional[str] = None
    currency: Optional[str] = None
    cycle_weights: Optional[Dict[str, float]] = None


class HoldingUpsert(BaseModel):
    fund_code: str
    shares: float
    avg_cost: float = 0.0


class CashAdjustment(BaseModel):
    amount: float
    note: Optional[str] = None


class TransactionCreate(BaseModel):
    fund_code: str
    trade_type: str
    amount: float
    shares: Optional[float] = None
    price: Optional[float] = None
    trade_date: Optional[datetime] = None
    note: Optional[str] = None


class CycleTargetsUpdate(BaseModel):
    targets: Dict[str, float]


class PortfolioSettingsUpdate(BaseModel):
    rebalance_frequency_days: Optional[int] = None
    rebalance_threshold_ratio: Optional[float] = None
    cash_target_ratio: Optional[float] = None
    dca_batches: Optional[int] = None


class RebalanceRequest(BaseModel):
    persist: bool = True
    batch_interval_days: int = 7
    recalc_each_batch: bool = True


class ManualNavInput(BaseModel):
    fund_code: str
    nav: float
    nav_date: Optional[date] = None


class TradeInput(BaseModel):
    fund: str
    amount: float
    trade_type: str = "buy"
    price: Optional[float] = None


class PromptUpdate(BaseModel):
    name: str = "agent_system"
    content: str
