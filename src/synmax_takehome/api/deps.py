from pathlib import Path

from fastapi import Depends

from synmax_takehome.config import Settings


def get_settings() -> Settings:
    return Settings()


def get_sqlite_path(settings: Settings = Depends(get_settings)) -> Path:
    return settings.sqlite_path
