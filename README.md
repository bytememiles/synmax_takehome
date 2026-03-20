# SynMax Python take-home

## Setup

- Python 3.11+
- From repo root:

```bash
python -m venv .venv
pip install -e ".[dev]"
playwright install chromium
```

**Windows (Command Prompt):** After creating `.venv`, you can use:

- `venv_shell.bat` — double-click (or run once) to open a **new** window with the venv active.
- `call venv_here.bat` — run from an **existing** prompt to activate in that window.

## Part 1: Scrape wells into SQLite

Loads each API from `apis_pythondev_test.csv` (or a path you pass), fetches NM OCD Well Details, parses fields, and upserts into `sqlite.db` table `api_well_data`.

```bash
synmax-load-wells --csv apis_pythondev_test.csv --db sqlite.db --delay 0.75
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--csv` | `apis_pythondev_test.csv` | Input CSV with `api` column |
| `--db` | `sqlite.db` (or `SYNMAX_SQLITE_PATH`) | SQLite database path |
| `--delay` | `0.75` | Seconds between HTTP requests |
| `--limit` | none | Process only first N rows (testing) |
| `--headful` | off | Run browser with UI (helps if Cloudflare Turnstile blocks headless) |
| `--timeout` | `90000` | Playwright navigation timeout (ms) |

**Cloudflare Turnstile:** The live site may show a challenge. If headless runs fail, try `--headful` once to pass the check, or run from a network where automation is allowed. Document any constraints in your submission notes.

**Offline parse check** (no network):

```bash
pytest tests/test_parse.py -q
```

## Part 2: API (placeholder)

```bash
uvicorn synmax_takehome.api.main:app --reload
```

Routers under `synmax_takehome.api.routers` will be wired in Part 2.

## Layout

- `synmax_takehome.scraping` — Playwright fetch + HTML parse
- `synmax_takehome.storage` — schema + repository (SQL)
- `synmax_takehome.models` — `WellRecord` for API responses
- `synmax_takehome.api` — FastAPI app factory

Environment:

- `SYNMAX_SQLITE_PATH` — override default DB path
