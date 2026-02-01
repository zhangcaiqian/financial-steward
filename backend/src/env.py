"""Environment loader."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def load_env() -> None:
    env = os.getenv("ENVIRONMENT", "development")
    base_dir = Path(__file__).resolve().parents[1]
    env_file = base_dir / f".env.{env}"
    default_env = base_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    elif default_env.exists():
        load_dotenv(default_env)
