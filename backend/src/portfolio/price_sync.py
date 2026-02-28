"""Sync NAV prices into database."""
from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from sqlalchemy import and_

from .db import get_session
from .models import Fund, NavPrice
from .price_provider import PriceProvider
from .price_provider_akshare import AksharePriceProvider

MANUAL_FUND_TYPES = {"advisory"}

logger = logging.getLogger(__name__)


def get_or_fetch_nav(fund_code: str, fund_type: str) -> tuple[date, float]:
    """Get latest NAV from DB; if missing, fetch from AKShare and persist."""
    session = get_session()
    try:
        fund = session.query(Fund).filter(Fund.code == fund_code).one_or_none()
        if fund is None:
            raise ValueError(f"Fund not found: {fund_code}")

        nav_price = (
            session.query(NavPrice)
            .filter(NavPrice.fund_id == fund.id, NavPrice.is_latest.is_(True))
            .one_or_none()
        )
        if nav_price is not None:
            return nav_price.nav_date, float(nav_price.nav)
    finally:
        session.close()

    if fund_type in MANUAL_FUND_TYPES:
        raise ValueError(f"No NAV available for manual fund: {fund_code}")

    provider = AksharePriceProvider()
    nav_date, nav_value = provider.get_latest_nav(fund_code, fund_type)

    session = get_session()
    try:
        fund = session.query(Fund).filter(Fund.code == fund_code).one()
        _unset_latest(session, fund.id)
        session.add(
            NavPrice(
                fund_id=fund.id,
                nav_date=nav_date,
                nav=nav_value,
                source="akshare",
                is_latest=True,
                is_stale=False,
            )
        )
        session.commit()
    finally:
        session.close()

    return nav_date, nav_value


def sync_latest_navs(
    provider: Optional[PriceProvider] = None,
    as_of: Optional[date] = None,
) -> int:
    provider = provider or AksharePriceProvider()
    session = get_session()
    updated = 0

    try:
        funds = session.query(Fund).filter(Fund.is_active.is_(True)).all()
        for fund in funds:
            if fund.fund_type in MANUAL_FUND_TYPES:
                continue
            try:
                nav_date, nav_value = provider.get_latest_nav(fund.code, fund.fund_type)
                if as_of and nav_date > as_of:
                    nav_date = as_of
                existing = (
                    session.query(NavPrice)
                    .filter(and_(NavPrice.fund_id == fund.id, NavPrice.nav_date == nav_date))
                    .one_or_none()
                )
                if existing:
                    if float(existing.nav) != nav_value:
                        existing.nav = nav_value
                    if not existing.is_latest:
                        _unset_latest(session, fund.id)
                        existing.is_latest = True
                    existing.is_stale = False
                else:
                    _unset_latest(session, fund.id)
                    session.add(
                        NavPrice(
                            fund_id=fund.id,
                            nav_date=nav_date,
                            nav=nav_value,
                            source="akshare",
                            is_latest=True,
                            is_stale=False,
                        )
                    )
                updated += 1
            except Exception as exc:
                logger.warning("NAV sync failed for %s: %s", fund.code, exc)
        session.commit()
    finally:
        session.close()

    return updated


def upsert_manual_nav(fund_code: str, nav_value: float, nav_date: date) -> NavPrice:
    """Manually set NAV for funds that cannot be auto-synced (e.g. advisory)."""
    session = get_session()
    try:
        fund = session.query(Fund).filter(Fund.code == fund_code).one_or_none()
        if fund is None:
            raise ValueError(f"Fund not found: {fund_code}")

        existing = (
            session.query(NavPrice)
            .filter(and_(NavPrice.fund_id == fund.id, NavPrice.nav_date == nav_date))
            .one_or_none()
        )
        if existing:
            existing.nav = nav_value
            existing.source = "manual"
            existing.is_stale = False
            if not existing.is_latest:
                _unset_latest(session, fund.id)
                existing.is_latest = True
            nav_price = existing
        else:
            _unset_latest(session, fund.id)
            nav_price = NavPrice(
                fund_id=fund.id,
                nav_date=nav_date,
                nav=nav_value,
                source="manual",
                is_latest=True,
                is_stale=False,
            )
            session.add(nav_price)

        session.commit()
        session.refresh(nav_price)
        return nav_price
    finally:
        session.close()


def _unset_latest(session, fund_id: int) -> None:
    session.query(NavPrice).filter(
        NavPrice.fund_id == fund_id,
        NavPrice.is_latest.is_(True),
    ).update({"is_latest": False})
