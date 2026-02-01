"""Price provider interface."""
from __future__ import annotations

from datetime import date
from typing import Tuple


class PriceProvider:
    """Abstract price provider."""

    def get_latest_nav(self, fund_code: str, fund_type: str) -> Tuple[date, float]:
        raise NotImplementedError
