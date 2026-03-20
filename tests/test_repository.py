import sqlite3
import tempfile
from pathlib import Path

from synmax_takehome.storage.repository import (
    apis_in_polygon,
    get_connection,
    init_db,
    upsert_well,
)


def test_apis_in_polygon_finds_interior_point() -> None:
    row = {
        "Operator": None,
        "Status": None,
        "Well Type": None,
        "Work Type": None,
        "Directional Status": None,
        "Multi-Lateral": None,
        "Mineral Owner": None,
        "Surface Owner": None,
        "Surface Location": None,
        "GL Elevation": None,
        "KB Elevation": None,
        "DF Elevation": None,
        "Single/Multiple Completion": None,
        "Potash Waiver": None,
        "Spud Date": None,
        "Last Inspection": None,
        "TVD": None,
        "API": "30-000-00001",
        "Latitude": "32.60",
        "Longitude": "-104.15",
        "CRS": "NAD83",
    }
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "t.db"
        conn = get_connection(db)
        init_db(conn)
        upsert_well(conn, row)
        conn.close()

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        init_db(conn)
        # Square around the point (lat, lon) order per take-home
        poly = [
            (32.50, -104.25),
            (32.50, -104.05),
            (32.70, -104.05),
            (32.70, -104.25),
        ]
        apis = apis_in_polygon(conn, poly)
        conn.close()
        assert apis == ["30-000-00001"]
