from pathlib import Path

import sqlite3
from collections.abc import Generator

from fastapi import Depends

from synmax_takehome.config import Settings
from synmax_takehome.storage.repository import get_connection, init_db


def get_settings() -> Settings:
    return Settings()


def get_sqlite_path(settings: Settings = Depends(get_settings)) -> Path:
    return settings.sqlite_path


def get_db_conn(
    settings: Settings = Depends(get_settings),
) -> Generator[sqlite3.Connection, None, None]:
    """Create a SQLite connection per request and always close it."""
    conn = get_connection(settings.sqlite_path)
    init_db(conn)
    try:
        yield conn
    finally:
        conn.close()
