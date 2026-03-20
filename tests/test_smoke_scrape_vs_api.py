from __future__ import annotations

from pathlib import Path

import pytest

from fastapi import HTTPException

from synmax_takehome.api.routers.spatial import polygon as polygon_endpoint
from synmax_takehome.api.routers.wells import well as well_endpoint
from synmax_takehome.models import WellRecord
from synmax_takehome.scraping.parse import parse_well_html
from synmax_takehome.storage.repository import get_connection


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_polygon_points_as_string() -> str:
    # Keep the format flexible: endpoint extracts (lat,lon) floats via regex.
    from synmax_takehome.cli.generate_polygon_csv import DEFAULT_POLYGON_LAT_LON

    return str(DEFAULT_POLYGON_LAT_LON)


@pytest.mark.parametrize(
    "html_path",
    sorted((_repo_root() / "web_pages").glob("*.html")),
    ids=lambda p: p.name,
)
def test_scrape_and_api_match_for_each_saved_well(html_path: Path) -> None:
    sqlite_path = _repo_root() / "sqlite.db"
    if not sqlite_path.exists():
        pytest.skip("sqlite.db not found; run Part 1 first.")

    api = html_path.stem
    html = _read_text(html_path)

    # Scrape/parse from the saved HTML fixture
    scraped_row = parse_well_html(html, fallback_api=api)
    scraped_record = WellRecord.model_validate(scraped_row).model_dump(by_alias=True)

    # Call the actual endpoint handler (in-process) using the sqlite row
    conn = get_connection(sqlite_path)
    try:
        try:
            api_record = well_endpoint(api=api, conn=conn)
        except HTTPException as e:
            if e.status_code == 404:
                pytest.skip(f"API {api} not present in sqlite.db; expected 404.")
            raise
    finally:
        conn.close()

    # Friendly terminal logs (shown with `pytest -s`)
    print(
        "match={api}".format(api=api),
        "| file={f}".format(f=html_path.name),
        "| status={s}".format(s=scraped_record.get("Status")),
        "| operator={o}".format(o=scraped_record.get("Operator")),
    )

    if scraped_record != api_record:
        mismatched_keys = sorted(
            k
            for k in scraped_record.keys()
            if scraped_record.get(k) != api_record.get(k)
        )
        print("DIFF api={api} keys={keys}".format(api=api, keys=mismatched_keys))

    assert scraped_record == api_record


def test_polygon_endpoint_matches_generated_csv() -> None:
    sqlite_path = _repo_root() / "sqlite.db"
    if not sqlite_path.exists():
        pytest.skip("sqlite.db not found; run Part 1 first.")

    csv_path = _repo_root() / "polygon_api_numbers.csv"
    if not csv_path.exists():
        pytest.skip("polygon_api_numbers.csv not found; run generator after Part 1.")

    with csv_path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    # first row is header
    expected = [x for x in lines[1:] if x]

    # Call endpoint handler with the polygon string format from the generator.
    points = _load_polygon_points_as_string()
    conn = get_connection(sqlite_path)
    try:
        got = polygon_endpoint(points=points, conn=conn)
    finally:
        conn.close()

    print(
        "polygon check: points_str_len={n} expected_count={e} got_count={g}".format(
            n=len(points), e=len(expected), g=len(got)
        )
    )
    # Order should be sorted (repository returns sorted).
    assert got == expected
