from __future__ import annotations

import argparse
import csv
import logging
import sys
import time
from pathlib import Path

from synmax_takehome.config import Settings
from synmax_takehome.models import WellRecord
from synmax_takehome.scraping.fetch import fetch_well_page
from synmax_takehome.scraping.parse import ParseError, parse_well_html
from synmax_takehome.storage.repository import get_connection, init_db, upsert_well

log = logging.getLogger(__name__)


def _read_api_list(csv_path: Path, limit: int | None) -> list[str]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit("CSV has no header row.")
        by_lower = {n.strip().lower(): n for n in reader.fieldnames}
        key = by_lower.get("api")
        if not key:
            raise SystemExit("CSV must contain an 'api' column.")
        out: list[str] = []
        for row in reader:
            raw = (row.get(key) or "").strip()
            if raw:
                out.append(raw)
            if limit is not None and len(out) >= limit:
                break
        return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Scrape NM OCD well pages into SQLite."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("apis_pythondev_test.csv"),
        help="CSV with an 'api' column",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="SQLite path (default: repo sqlite.db or SYNMAX_SQLITE_PATH)",
    )
    parser.add_argument(
        "--delay", type=float, default=0.75, help="Seconds between fetches"
    )
    parser.add_argument("--limit", type=int, default=None, help="Max rows (testing)")
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Show browser (useful for Cloudflare / Turnstile)",
    )
    parser.add_argument(
        "--timeout", type=int, default=90_000, help="Playwright timeout (ms)"
    )
    parser.add_argument(
        "--skip-validate",
        action="store_true",
        help="Skip Pydantic WellRecord validation after parse",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    settings = Settings()
    db_path = args.db if args.db is not None else settings.sqlite_path

    apis = _read_api_list(args.csv, args.limit)
    if not apis:
        log.error("No API numbers found in %s", args.csv)
        sys.exit(1)

    conn = get_connection(db_path)
    init_db(conn)

    ok, failed = 0, 0
    for i, api in enumerate(apis):
        try:
            html = fetch_well_page(
                api, headless=not args.headful, timeout_ms=args.timeout
            )
            row = parse_well_html(html, fallback_api=api)
            if not args.skip_validate:
                WellRecord.model_validate(row)
            upsert_well(conn, row)
            ok += 1
            log.info("[%s/%s] OK %s", i + 1, len(apis), api)
        except (ParseError, Exception) as e:
            failed += 1
            log.warning("[%s/%s] FAIL %s: %s", i + 1, len(apis), api, e)

        if i + 1 < len(apis) and args.delay > 0:
            time.sleep(args.delay)

    conn.close()
    log.info("Done: %s succeeded, %s failed, db=%s", ok, failed, db_path)
    if failed:
        sys.exit(2)


if __name__ == "__main__":
    main()
