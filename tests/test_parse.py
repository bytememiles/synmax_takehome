from pathlib import Path

import pytest

from synmax_takehome.models import WellRecord
from synmax_takehome.scraping.parse import parse_well_html

WEB_PAGES = sorted(
    (Path(__file__).resolve().parent.parent / "web_pages").glob("*.html")
)
KNOWN_API = "30-045-35432"
KNOWN_FIXTURE = (
    Path(__file__).resolve().parent.parent / "web_pages" / f"{KNOWN_API}.html"
)


@pytest.fixture(scope="module")
def known_html() -> str:
    return KNOWN_FIXTURE.read_text(encoding="utf-8")


def test_parse_known_web_page_matches_known_well(known_html: str) -> None:
    assert KNOWN_API in KNOWN_FIXTURE.stem
    row = parse_well_html(known_html, fallback_api=KNOWN_API)
    assert row["API"] == KNOWN_API
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


def test_well_record_validates_parsed_known_row(known_html: str) -> None:
    row = parse_well_html(known_html, fallback_api=KNOWN_API)
    rec = WellRecord.model_validate(row)
    assert rec.API == KNOWN_API
    assert rec.to_db_row()["Well Type"] == "Oil"


@pytest.mark.parametrize("html_path", WEB_PAGES, ids=lambda p: p.name)
def test_parse_saved_web_pages_with_console_summary(html_path: Path) -> None:
    row = parse_well_html(
        html_path.read_text(encoding="utf-8"), fallback_api=html_path.stem
    )
    rec = WellRecord.model_validate(row)

    # Printed when running with -s, gives quick confidence in parsed values.
    print(
        " | ".join(
            [
                f"file={html_path.name}",
                f"api={rec.API}",
                f"status={rec.Status}",
                f"well_type={rec.Well_Type}",
                f"operator={rec.Operator}",
                f"lat={rec.Latitude}",
                f"lon={rec.Longitude}",
                f"crs={rec.CRS}",
                f"spud={rec.Spud_Date}",
                f"tvd={rec.TVD}",
            ]
        )
    )

    assert rec.API == html_path.stem
    assert rec.Status is not None
    assert rec.Operator is not None
