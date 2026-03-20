from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Sequence

from shapely.geometry import Point, Polygon

from synmax_takehome.storage.schema import (
    TABLE_COLUMNS,
    TABLE_NAME,
    create_table_ddl,
    insert_columns_sql,
    placeholders,
)


def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(create_table_ddl())
    conn.commit()


def _row_tuple(row: dict[str, str | None]) -> tuple[str | None, ...]:
    return tuple(row.get(c) for c in TABLE_COLUMNS)


def upsert_well(conn: sqlite3.Connection, row: dict[str, str | None]) -> None:
    sql = (
        f"INSERT OR REPLACE INTO {TABLE_NAME} ({insert_columns_sql()}) "
        f"VALUES ({placeholders()})"
    )
    conn.execute(sql, _row_tuple(row))
    conn.commit()


def get_well_by_api(conn: sqlite3.Connection, api: str) -> dict[str, Any] | None:
    cur = conn.execute(
        f'SELECT * FROM {TABLE_NAME} WHERE "API" = ?',
        (api,),
    )
    r = cur.fetchone()
    if r is None:
        return None
    return dict(r)


def apis_in_polygon(
    conn: sqlite3.Connection,
    polygon_lat_lon: Sequence[tuple[float, float]],
) -> list[str]:
    """Return API numbers for wells whose Lat/Lon fall inside the polygon (WGS84).

    `polygon_lat_lon` is (latitude, longitude) vertices in order; ring is auto-closed.
    """
    if len(polygon_lat_lon) < 3:
        return []

    # Shapely uses (x, y) -> (lon, lat) for geographic coords
    ring = [(lon, lat) for lat, lon in polygon_lat_lon]
    if ring[0] != ring[-1]:
        ring = [*ring, ring[0]]
    poly = Polygon(ring)
    if not poly.is_valid:
        poly = poly.buffer(0)

    cur = conn.execute(
        f'SELECT "API", "Latitude", "Longitude" FROM {TABLE_NAME} '
        f'WHERE "Latitude" IS NOT NULL AND "Longitude" IS NOT NULL '
        f'AND TRIM("Latitude") != "" AND TRIM("Longitude") != ""'
    )
    out: list[str] = []
    for api, lat_s, lon_s in cur.fetchall():
        try:
            lat = float(lat_s)
            lon = float(lon_s)
        except (TypeError, ValueError):
            continue
        if poly.contains(Point(lon, lat)):
            out.append(str(api))
    return sorted(out)
