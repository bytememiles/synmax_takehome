from __future__ import annotations

import argparse
import csv
from pathlib import Path

from synmax_takehome.config import Settings
from synmax_takehome.storage.repository import apis_in_polygon, get_connection, init_db


# Polygon from the take-home PDF (lat, lon) including a repeated first/last point.
DEFAULT_POLYGON_LAT_LON: list[tuple[float, float]] = [
    (32.81, -104.19),
    (32.66, -104.32),
    (32.54, -104.24),
    (32.50, -104.03),
    (32.73, -104.01),
    (32.79, -103.91),
    (32.84, -104.05),
    (32.81, -104.19),
]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Generate the polygon CSV deliverable from sqlite.db."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="SQLite DB path (default: SYNMAX_SQLITE_PATH or sqlite.db)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("polygon_api_numbers.csv"),
        help="Output CSV path (default: polygon_api_numbers.csv)",
    )
    args = parser.parse_args(argv)

    settings = Settings()
    db_path = args.db if args.db is not None else settings.sqlite_path

    conn = get_connection(db_path)
    try:
        init_db(conn)
        apis = apis_in_polygon(conn, DEFAULT_POLYGON_LAT_LON)
    finally:
        conn.close()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["api"])
        for api in apis:
            writer.writerow([api])


if __name__ == "__main__":
    main()
