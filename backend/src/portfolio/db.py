"""Database helpers for portfolio system."""
from __future__ import annotations

import os
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import PORTFOLIO_DB


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


_SSL_QUERY_KEYS = {"ssl_ca", "ssl_cert", "ssl_key", "ssl_verify_cert", "ssl_verify_identity"}


def _build_db_url() -> tuple[str, dict]:
    """Return (url, connect_args). Extracts SSL params from the query string
    and converts them into pymysql-compatible ``connect_args``."""
    url = PORTFOLIO_DB.get('url')
    if not url:
        user = PORTFOLIO_DB['user']
        password = PORTFOLIO_DB['password']
        host = PORTFOLIO_DB['host']
        port = PORTFOLIO_DB['port']
        database = PORTFOLIO_DB['database']
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4", {}

    parsed = urlparse(url)
    qs = parse_qs(parsed.query, keep_blank_values=True)

    ssl_opts: dict = {}
    remaining_qs: dict = {}
    for key, values in qs.items():
        val = values[0] if values else ""
        if key == "ssl_ca":
            ssl_opts["ca"] = val
        elif key == "ssl_cert":
            ssl_opts["cert"] = val
        elif key == "ssl_key":
            ssl_opts["key"] = val
        elif key in _SSL_QUERY_KEYS:
            pass
        else:
            remaining_qs[key] = val

    clean_url = urlunparse(parsed._replace(query=urlencode(remaining_qs)))
    connect_args: dict = {}
    if ssl_opts:
        connect_args["ssl"] = ssl_opts

    return clean_url, connect_args


_ENGINE = None
_SESSION_FACTORY = None


def get_engine():
    global _ENGINE
    if _ENGINE is None:
        echo = os.getenv('PORTFOLIO_DB_ECHO', 'false').lower() == 'true'
        url, connect_args = _build_db_url()
        _ENGINE = create_engine(
            url,
            echo=echo,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args=connect_args,
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
