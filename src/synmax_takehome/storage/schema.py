"""Single source of truth for SQLite `api_well_data` shape."""

TABLE_NAME = "api_well_data"

# Order used by INSERT / row dicts (PDF names, quoted in SQL).
TABLE_COLUMNS: tuple[str, ...] = (
    "Operator",
    "Status",
    "Well Type",
    "Work Type",
    "Directional Status",
    "Multi-Lateral",
    "Mineral Owner",
    "Surface Owner",
    "Surface Location",
    "GL Elevation",
    "KB Elevation",
    "DF Elevation",
    "Single/Multiple Completion",
    "Potash Waiver",
    "Spud Date",
    "Last Inspection",
    "TVD",
    "API",
    "Latitude",
    "Longitude",
    "CRS",
)


def _q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def create_table_ddl() -> str:
    cols = ", ".join(f"{_q(c)} TEXT" for c in TABLE_COLUMNS)
    return (
        f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} ({cols}, PRIMARY KEY ({_q('API')}));"
    )


def insert_columns_sql() -> str:
    return ", ".join(_q(c) for c in TABLE_COLUMNS)


def placeholders() -> str:
    return ", ".join("?" for _ in TABLE_COLUMNS)
