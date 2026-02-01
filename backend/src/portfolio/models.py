"""SQLAlchemy models for portfolio system."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Cycle(Base):
    __tablename__ = "cycles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)

    fund_weights = relationship("FundCycleWeight", back_populates="cycle")
    targets = relationship("CycleTarget", back_populates="cycle")


class CycleTarget(Base):
    __tablename__ = "cycle_targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("cycles.id"), nullable=False)
    target_weight: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    cycle = relationship("Cycle", back_populates="targets")

    __table_args__ = (UniqueConstraint("cycle_id", "is_active", name="uq_cycle_target_active"),)


class Fund(Base):
    __tablename__ = "funds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    fund_type: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CNY")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    cycle_weights = relationship("FundCycleWeight", back_populates="fund")
    holdings = relationship("Holding", back_populates="fund")
    prices = relationship("NavPrice", back_populates="fund")


class FundCycleWeight(Base):
    __tablename__ = "fund_cycle_weights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id"), nullable=False)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("cycles.id"), nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)

    fund = relationship("Fund", back_populates="cycle_weights")
    cycle = relationship("Cycle", back_populates="fund_weights")

    __table_args__ = (UniqueConstraint("fund_id", "cycle_id", name="uq_fund_cycle_weight"),)


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id"), nullable=False)
    shares: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False, default=0)
    avg_cost: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    fund = relationship("Fund", back_populates="holdings")

    __table_args__ = (UniqueConstraint("fund_id", name="uq_holding_fund"),)


class CashAccount(Base):
    __tablename__ = "cash_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    balance: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id"), nullable=False)
    trade_type: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    shares: Mapped[float] = mapped_column(Numeric(20, 6), nullable=True)
    price: Mapped[float] = mapped_column(Numeric(20, 6), nullable=True)
    trade_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    note: Mapped[str] = mapped_column(String(256), nullable=True)


class NavPrice(Base):
    __tablename__ = "nav_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id"), nullable=False)
    nav_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    nav: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="akshare")
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_stale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    fund = relationship("Fund", back_populates="prices")

    __table_args__ = (UniqueConstraint("fund_id", "nav_date", name="uq_fund_nav_date"),)


class PortfolioSettings(Base):
    __tablename__ = "portfolio_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rebalance_frequency_days: Mapped[int] = mapped_column(Integer, nullable=False)
    rebalance_threshold_ratio: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    cash_target_ratio: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    dca_batches: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    last_rebalance_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(String(4000), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(String(2000), nullable=False)
    parsed_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="parsed")
    provider: Mapped[str] = mapped_column(String(32), nullable=True)
    model: Mapped[str] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class RebalancePlan(Base):
    __tablename__ = "rebalance_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    total_assets: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    cash_balance: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    cash_target: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    should_rebalance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    recalc_each_batch: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    note: Mapped[str] = mapped_column(String(256), nullable=True)

    batches = relationship("RebalanceBatch", back_populates="plan")
    trades = relationship("RebalanceTrade", back_populates="plan")


class RebalanceBatch(Base):
    __tablename__ = "rebalance_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("rebalance_plans.id"), nullable=False)
    batch_no: Mapped[int] = mapped_column(Integer, nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    plan = relationship("RebalancePlan", back_populates="batches")
    trades = relationship("RebalanceTrade", back_populates="batch")

    __table_args__ = (UniqueConstraint("plan_id", "batch_no", name="uq_rebalance_batch_no"),)


class RebalanceTrade(Base):
    __tablename__ = "rebalance_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("rebalance_plans.id"), nullable=False)
    batch_id: Mapped[int] = mapped_column(ForeignKey("rebalance_batches.id"), nullable=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(8), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="planned")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    plan = relationship("RebalancePlan", back_populates="trades")
    batch = relationship("RebalanceBatch", back_populates="trades")
