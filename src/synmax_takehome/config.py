from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_sqlite_path() -> Path:
    return Path(__file__).resolve().parents[2] / "sqlite.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SYNMAX_", env_file=".env", extra="ignore"
    )

    sqlite_path: Path = _default_sqlite_path()
