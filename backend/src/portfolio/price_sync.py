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


logger = logging.getLogger(__name__)


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


def _unset_latest(session, fund_id: int) -> None:
    session.query(NavPrice).filter(
        NavPrice.fund_id == fund_id,
        NavPrice.is_latest.is_(True),
    ).update({"is_latest": False})
