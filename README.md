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

Loads each API from a CSV you name with `--csv` (filename or path; must include an `api` column). The take-home’s sample list is `apis_pythondev_test.csv`. Results go into `sqlite.db` table `api_well_data`.

Deliverables note:

- `apis_pythondev_test.csv` is the **input** list of API numbers to scrape.
- `polygon_api_numbers.csv` is the **required output** list of API numbers returned by your Part 2 polygon endpoint for the fixed polygon in the take-home PDF.

You can (re)generate `polygon_api_numbers.csv` from your `sqlite.db` using:

```bash
synmax-generate-polygon-csv --db sqlite.db --out polygon_api_numbers.csv
```

```bash
# --csv = your input list (replace the filename with yours if needed)
synmax-load-wells --csv apis_pythondev_test.csv --db sqlite.db --delay 0.75

# Example: another CSV in the repo root
synmax-load-wells --csv my_well_apis.csv --db sqlite.db --delay 0.75
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--csv` | `apis_pythondev_test.csv` | Input CSV path (header row with `api` column) |
| `--db` | `sqlite.db` (or `SYNMAX_SQLITE_PATH`) | SQLite database path |
| `--delay` | `0.75` | Seconds between HTTP requests |
| `--limit` | none | Process only first N rows (testing) |
| `--headful` | off | Run browser with UI (overrides env; helps if Cloudflare Turnstile blocks headless) |
| `--headless` | off | Force headless (overrides env) |
| `--timeout` | see env | Playwright timeout (ms); default from `SYNMAX_PLAYWRIGHT_TIMEOUT_MS` |
| `--user-data-dir` | see env | Chromium profile path; keeps cookies between wells (`SYNMAX_PLAYWRIGHT_USER_DATA_DIR`) |
| `--channel` | see env | Installed browser channel: `chrome`, `msedge`, … (`SYNMAX_PLAYWRIGHT_CHANNEL`) |
| `--no-reduce-automation` | off | Skip Playwright tweaks that hide automation hints (rarely needed) |

**Cloudflare / Turnstile:** NM OCD often serves a **“Verify you are human”** interstitial (Turnstile). **Headless** runs usually **cannot** complete it, so the loader will fail fast with `stage=cloudflare` instead of waiting the full timeout.

What works in practice:

1. **Visible browser:** `synmax-load-wells ... --headful` (or `SYNMAX_PLAYWRIGHT_HEADLESS=false`). Complete the checkbox in the window; the loader then waits for the real well page.
2. **Persistent profile:** set `--user-data-dir .playwright_profile` or `SYNMAX_PLAYWRIGHT_USER_DATA_DIR=.playwright_profile`. Solve Turnstile **once**; later rows may reuse the saved cookie for that profile. Add `.playwright_profile/` to `.gitignore` if you use a folder in the repo.
3. **If the checkbox shows “Verification failed”:** Playwright’s **bundled Chromium** is often detected. Install **Google Chrome** or **Edge**, then run with **`--channel chrome`** or **`--channel msedge`** (still **`--headful`**, still a **real** click). Example:

```bash
synmax-load-wells --csv apis_pythondev_test.csv --db sqlite.db --delay 0.75 ^
  --headful --channel chrome --user-data-dir .playwright_profile
```

**Windows quick start (Command Prompt):**

```bat
set SYNMAX_PLAYWRIGHT_HEADLESS=false
set SYNMAX_PLAYWRIGHT_CHANNEL=chrome
set SYNMAX_PLAYWRIGHT_USER_DATA_DIR=.playwright_profile

synmax-load-wells --csv apis_pythondev_test.csv --db sqlite.db --delay 0.75 --headful
```

**Recommended command (single copy/paste):**

```bat
synmax-load-wells --csv apis_pythondev_test.csv --db sqlite.db --delay 0.75 --headful --channel chrome --user-data-dir .playwright_profile
```

Other things that help: stable **home/residential** IP (VPN/datacenter IPs get blocked), disable aggressive VPN/browser privacy extensions for that window, wait until the iframe finishes loading before clicking, use **Troubleshoot / Refresh** on the widget if offered.

Always follow the site’s terms and don’t attempt to bypass protections.

**Offline parse check** (no network):

```bash
pytest tests/test_parse.py -q
```

## Part 2: API

### Host the server locally

Make sure `sqlite.db` is present in the repo root (or set `SYNMAX_SQLITE_PATH`).

```bash
uvicorn synmax_takehome.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Sample requests (curl)

1) Health check

```bash
curl http://127.0.0.1:8000/health
```

2) Get one well by API

```bash
curl "http://127.0.0.1:8000/well?api=30-015-25471"
```

3) Polygon search

The API expects the polygon as a string containing `(lat,lon)` pairs (the format shown in the take-home PDF).

```bash
curl -G "http://127.0.0.1:8000/search/polygon" ^
  --data-urlencode "points=[(32.81,-104.19),(32.66,-104.32),(32.54,-104.24),(32.50,-104.03),(32.73,-104.01),(32.79,-103.91),(32.84,-104.05),(32.81,-104.19)]"
```

Notes:
- `/well` returns `404` if the API number is not in the database.
- `/search/polygon` returns a JSON array of matching API numbers.

## Layout

- `synmax_takehome.scraping` — Playwright fetch + HTML parse
- `synmax_takehome.storage` — schema + repository (SQL)
- `synmax_takehome.models` — `WellRecord` for API responses
- `synmax_takehome.api` — FastAPI app factory

Environment:

- `SYNMAX_SQLITE_PATH` — override default DB path
- `SYNMAX_PLAYWRIGHT_HEADLESS` — `true` / `false` (default headless; set `false` to use a visible browser without passing `--headful`)
- `SYNMAX_PLAYWRIGHT_TIMEOUT_MS` — navigation / selector wait timeout (default `90000`)
- `SYNMAX_PLAYWRIGHT_USER_DATA_DIR` — optional Chromium user-data folder for cookie persistence (pairs well with `--headful` after one Turnstile solve)
- `SYNMAX_PLAYWRIGHT_CHANNEL` — e.g. `chrome` or `msedge` (use installed browser; often fixes Turnstile “Verification failed” with bundled Chromium)
- `SYNMAX_PLAYWRIGHT_REDUCE_AUTOMATION_FLAGS` — `true` / `false` (default `true` when headed: drops `--enable-automation` and uses `AutomationControlled` tweak)
