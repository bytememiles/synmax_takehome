from pathlib import Path

import pytest

from synmax_takehome.models import WellRecord
from synmax_takehome.scraping.parse import parse_well_html

FIXTURE = Path(__file__).resolve().parent.parent / "content.html"


@pytest.fixture(scope="module")
def html() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_parse_fixture_matches_known_well(html: str) -> None:
    row = parse_well_html(html, fallback_api="30-045-35432")
    assert row["API"] == "30-045-35432"
    assert row["Status"] == "Active"
    assert row["Well Type"] == "Oil"
    assert row["Work Type"] == "New"
    assert row["Directional Status"] == "Horizontal"
    assert row["Multi-Lateral"] == "No"
    assert row["Mineral Owner"] == "Federal"
    assert row["Surface Owner"] == "Federal"
    assert row["Surface Location"] and "E-07-24N-09W" in row["Surface Location"]
    assert row["GL Elevation"] == "6876"
    assert row["Single/Multiple Completion"] == "Single"
    assert row["Potash Waiver"] == "False"
    assert row["Spud Date"] == "02/27/2014"
    assert row["Last Inspection"] == "03/03/2026"
    assert row["TVD"] == "5502"
    assert row["Latitude"] == "36.3313293"
    assert row["Longitude"] == "-107.8383865"
    assert row["CRS"] == "NAD83"
    assert row["Operator"] and "DJR OPERATING" in row["Operator"]


def test_well_record_validates_parsed_row(html: str) -> None:
    row = parse_well_html(html, fallback_api="30-045-35432")
    rec = WellRecord.model_validate(row)
    assert rec.API == "30-045-35432"
    assert rec.to_db_row()["Well Type"] == "Oil"
