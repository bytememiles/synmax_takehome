from __future__ import annotations

import argparse
import csv
import logging
import sys
import time
from pathlib import Path

from synmax_takehome.config import Settings
from synmax_takehome.models import WellRecord
from synmax_takehome.scraping.fetch import CloudflareChallengeError, fetch_well_page
from synmax_takehome.scraping.parse import ParseError, parse_well_html
from synmax_takehome.storage.repository import get_connection, init_db, upsert_well

log = logging.getLogger(__name__)


def _one_line(msg: object) -> str:
    """Strip embedded newlines so log lines stay single-line in the console."""
    return " ".join(str(msg).replace("\r", " ").split())


def _read_api_list(csv_path: Path, limit: int | None) -> list[str]:
    # utf-8-sig strips a UTF-8 BOM so the header is "api", not "\ufeffapi" (common on Windows).
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit("CSV has no header row.")
        by_lower = {
            (n or "").replace("\ufeff", "").strip().lower(): n
            for n in reader.fieldnames
            if n is not None
        }
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
    settings = Settings()

    parser = argparse.ArgumentParser(
        description="Scrape NM OCD well pages into SQLite."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("apis_pythondev_test.csv"),
        help="CSV with an `api` column",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="SQLite path (default: repo sqlite.db or SYNMAX_SQLITE_PATH)",
    )
    parser.add_argument(
        "--delay", type=float, default=0.75, help="Seconds between HTTP requests"
    )
    parser.add_argument("--limit", type=int, default=None, help="Max rows (testing)")
    head = parser.add_mutually_exclusive_group()
    head.add_argument(
        "--headful",
        action="store_true",
        help="Run Playwright with a visible browser (overrides SYNMAX_PLAYWRIGHT_HEADLESS)",
    )
    head.add_argument(
        "--headless",
        action="store_true",
        help="Run Playwright headless (overrides SYNMAX_PLAYWRIGHT_HEADLESS)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help=f"Playwright timeout in ms (default: {settings.playwright_timeout_ms} or SYNMAX_PLAYWRIGHT_TIMEOUT_MS)",
    )
    parser.add_argument(
        "--user-data-dir",
        type=Path,
        default=None,
        help="Chromium profile folder (cookies persist; env SYNMAX_PLAYWRIGHT_USER_DATA_DIR)",
    )
    parser.add_argument(
        "--channel",
        type=str,
        default=None,
        help='Playwright browser channel, e.g. chrome or msedge (env SYNMAX_PLAYWRIGHT_CHANNEL)',
    )
    parser.add_argument(
        "--no-reduce-automation",
        action="store_true",
        help="Do not tweak automation flags (for debugging; Turnstile may be stricter)",
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
        force=True,
    )

    db_path = args.db if args.db is not None else settings.sqlite_path
    timeout_ms = (
        args.timeout
        if args.timeout is not None
        else settings.playwright_timeout_ms
    )

    if args.headful:
        headless = False
    elif args.headless:
        headless = True
    else:
        headless = settings.playwright_headless

    user_data_dir = (
        args.user_data_dir
        if args.user_data_dir is not None
        else settings.playwright_user_data_dir
    )
    channel_raw = (
        args.channel
        if args.channel is not None
        else settings.playwright_channel
    )
    channel = (channel_raw or "").strip() or None
    reduce_automation = (
        settings.playwright_reduce_automation_flags
        and not args.no_reduce_automation
    )

    apis = _read_api_list(args.csv, args.limit)
    if not apis:
        log.error("No API numbers found in %s", args.csv)
        sys.exit(1)

    log.info(
        "start csv=%s db=%s total=%s headless=%s channel=%s reduce_automation=%s "
        "timeout_ms=%s delay_s=%s user_data_dir=%s",
        args.csv,
        db_path,
        len(apis),
        headless,
        channel or "-",
        reduce_automation,
        timeout_ms,
        args.delay,
        user_data_dir or "-",
    )

    conn = get_connection(db_path)
    init_db(conn)

    ok, failed = 0, 0
    try:
        for i, api in enumerate(apis):
            n = i + 1
            total = len(apis)
            log.info("[%s/%s] fetch api=%s", n, total, api)
            try:
                html = fetch_well_page(
                    api,
                    headless=headless,
                    timeout_ms=timeout_ms,
                    user_data_dir=user_data_dir,
                    channel=channel,
                    reduce_automation_flags=reduce_automation,
                )
                row = parse_well_html(html, fallback_api=api)
                if not args.skip_validate:
                    WellRecord.model_validate(row)
                upsert_well(conn, row)
                ok += 1
                log.info(
                    "[%s/%s] ok api=%s status=%s well_type=%s",
                    n,
                    total,
                    api,
                    row.get("Status") or "-",
                    row.get("Well Type") or "-",
                )
            except ParseError as e:
                failed += 1
                log.warning(
                    "[%s/%s] fail api=%s stage=parse err=%s",
                    n,
                    total,
                    api,
                    _one_line(e),
                )
            except CloudflareChallengeError as e:
                failed += 1
                log.warning(
                    "[%s/%s] fail api=%s stage=cloudflare err=%s",
                    n,
                    total,
                    api,
                    _one_line(e),
                )
            except Exception as e:
                failed += 1
                log.warning(
                    "[%s/%s] fail api=%s stage=fetch err=%s",
                    n,
                    total,
                    api,
                    _one_line(e),
                )

            if i + 1 < len(apis) and args.delay > 0:
                time.sleep(args.delay)
    except KeyboardInterrupt:
        log.info("interrupted ok=%s fail=%s (of %s)", ok, failed, len(apis))
        sys.exit(130)
    finally:
        conn.close()

    log.info("done ok=%s fail=%s db=%s", ok, failed, db_path)
    if failed:
        sys.exit(2)


if __name__ == "__main__":
    main()
