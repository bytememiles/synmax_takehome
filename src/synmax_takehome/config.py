from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_sqlite_path() -> Path:
    return Path(__file__).resolve().parents[2] / "sqlite.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SYNMAX_", env_file=".env", extra="ignore"
    )

    sqlite_path: Path = _default_sqlite_path()
    # Playwright: set SYNMAX_PLAYWRIGHT_HEADLESS=false for headed (UI) browser by default.
    playwright_headless: bool = True
    playwright_timeout_ms: int = 90_000
    # Optional Chromium profile directory (persists cookies; helpful after one Turnstile solve).
    playwright_user_data_dir: Path | None = None
    # Use installed browser: "chrome", "msedge", "chrome-beta", … (see Playwright docs). Often
    # passes Turnstile where bundled Chromium fails.
    playwright_channel: str | None = None
    # When headed, drop obvious automation defaults (helps some Cloudflare configurations).
    playwright_reduce_automation_flags: bool = True
