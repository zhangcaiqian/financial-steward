"""Load strategy context for agent."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def load_strategy_context() -> str:
    repo_dir = Path(__file__).resolve().parents[3]
    strategy_path = repo_dir / "docs" / "均衡型资产配置方案.md"
    if not strategy_path.exists():
        return ""
    try:
        return strategy_path.read_text(encoding="utf-8")
    except Exception:
        return ""
