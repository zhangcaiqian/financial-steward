"""Database helpers for portfolio system."""
from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import PORTFOLIO_DB


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


def _build_db_url() -> str:
    url = PORTFOLIO_DB.get('url')
    if url:
        return url

    user = PORTFOLIO_DB['user']
    password = PORTFOLIO_DB['password']
    host = PORTFOLIO_DB['host']
    port = PORTFOLIO_DB['port']
    database = PORTFOLIO_DB['database']
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"


_ENGINE = None
_SESSION_FACTORY = None


def get_engine():
    global _ENGINE
    if _ENGINE is None:
        echo = os.getenv('PORTFOLIO_DB_ECHO', 'false').lower() == 'true'
        _ENGINE = create_engine(
            _build_db_url(),
            echo=echo,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _ENGINE


def get_session():
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    return _SESSION_FACTORY()
