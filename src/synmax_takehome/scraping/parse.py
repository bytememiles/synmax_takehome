from __future__ import annotations

import re
from typing import Final

from bs4 import BeautifulSoup

from synmax_takehome.storage.schema import TABLE_COLUMNS

_API_HEADER_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*(\d{2}-\d{3}-\d{5})\b",
    re.MULTILINE,
)
_COORD_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s+(.*)$",
)


class ParseError(Exception):
    """HTML does not contain expected well detail markers."""


# NM OCD Well Details — General Well Information (stable client IDs)
IDS: Final[dict[str, str]] = {
    "Operator": "ctl00_ctl00__main_main_ucGeneralWellInformation_lblOperator",
    "Status": "ctl00_ctl00__main_main_ucGeneralWellInformation_lblStatus",
    "Well Type": "ctl00_ctl00__main_main_ucGeneralWellInformation_lblWellType",
    "Work Type": "ctl00_ctl00__main_main_ucGeneralWellInformation_lblWorkType",
    "Directional Status": "ctl00_ctl00__main_main_ucGeneralWellInformation_lblDirectionalStatus",
    "Multi-Lateral": "ctl00_ctl00__main_main_ucGeneralWellInformation_lblMultiLateral",
    "Mineral Owner": "ctl00_ctl00__main_main_ucGeneralWellInformation_lblMineralOwner",
    "Surface Owner": "ctl00_ctl00__main_main_ucGeneralWellInformation_lblSurfaceOwner",
    "Surface Location": "ctl00_ctl00__main_main_ucGeneralWellInformation_Location_lblLocation",
    "_lot": "ctl00_ctl00__main_main_ucGeneralWellInformation_Location_lblLot",
    "_fnl": "ctl00_ctl00__main_main_ucGeneralWellInformation_Location_lblFootageNSH",
    "_fwl": "ctl00_ctl00__main_main_ucGeneralWellInformation_Location_lblFootageEW",
    "_latlon": "ctl00_ctl00__main_main_ucGeneralWellInformation_Location_lblCoordinates",
    "GL Elevation": "ctl00_ctl00__main_main_ucGeneralWellInformation_lblGLElevation",
    "KB Elevation": "ctl00_ctl00__main_main_ucGeneralWellInformation_lblKBElevation",
    "DF Elevation": "ctl00_ctl00__main_main_ucGeneralWellInformation_lblDFElevation",
    "Single/Multiple Completion": "ctl00_ctl00__main_main_ucGeneralWellInformation_lblCompletions",
    "Potash Waiver": "ctl00_ctl00__main_main_ucGeneralWellInformation_lblPotashWaiver",
    "Spud Date": "ctl00_ctl00__main_main_ucGeneralWellInformation_lblSpudDate",
    "Last Inspection": "ctl00_ctl00__main_main_ucGeneralWellInformation_lblLastInspectionDate",
    "TVD": "ctl00_ctl00__main_main_ucGeneralWellInformation_lblTrueVerticalDepth",
    "_header_api": "ctl00_ctl00__main_main_lblApi",
}


def _clean(text: str | None) -> str | None:
    if text is None:
        return None
    t = " ".join(text.split())
    return t if t else None


def _text_by_id(soup: BeautifulSoup, element_id: str) -> str | None:
    tag = soup.find(id=element_id)
    if tag is None:
        return None
    return _clean(tag.get_text(separator=" ", strip=True))


def _parse_api_from_header(header_text: str | None) -> str | None:
    if not header_text:
        return None
    m = _API_HEADER_RE.search(header_text)
    return m.group(1) if m else None


def _parse_coordinates(raw: str | None) -> tuple[str | None, str | None, str | None]:
    if not raw:
        return None, None, None
    m = _COORD_RE.match(raw.strip())
    if not m:
        return None, None, None
    lat, lon, crs = m.group(1), m.group(2), _clean(m.group(3))
    return lat, lon, crs


def _build_surface_location(soup: BeautifulSoup) -> str | None:
    loc = _text_by_id(soup, IDS["Surface Location"])
    lot = _text_by_id(soup, IDS["_lot"])
    fnl = _text_by_id(soup, IDS["_fnl"])
    fwl = _text_by_id(soup, IDS["_fwl"])
    parts = [p for p in (loc, lot, fnl, fwl) if p]
    return "; ".join(parts) if parts else None


def parse_well_html(html: str, *, fallback_api: str) -> dict[str, str | None]:
    """Extract well fields from Well Details HTML (fragment or full document)."""
    soup = BeautifulSoup(html, "lxml")
    if (
        soup.find(id=IDS["_header_api"]) is None
        and soup.find(id=IDS["Operator"]) is None
    ):
        raise ParseError("Missing well detail markers (lblApi / Operator span).")

    header = _text_by_id(soup, IDS["_header_api"])
    api = _parse_api_from_header(header) or fallback_api.strip()

    lat, lon, crs = _parse_coordinates(_text_by_id(soup, IDS["_latlon"]))

    row: dict[str, str | None] = {c: None for c in TABLE_COLUMNS}
    row["Operator"] = _text_by_id(soup, IDS["Operator"])
    row["Status"] = _text_by_id(soup, IDS["Status"])
    row["Well Type"] = _text_by_id(soup, IDS["Well Type"])
    row["Work Type"] = _text_by_id(soup, IDS["Work Type"])
    row["Directional Status"] = _text_by_id(soup, IDS["Directional Status"])
    row["Multi-Lateral"] = _text_by_id(soup, IDS["Multi-Lateral"])
    row["Mineral Owner"] = _text_by_id(soup, IDS["Mineral Owner"])
    row["Surface Owner"] = _text_by_id(soup, IDS["Surface Owner"])
    row["Surface Location"] = _build_surface_location(soup)
    row["GL Elevation"] = _text_by_id(soup, IDS["GL Elevation"])
    row["KB Elevation"] = _text_by_id(soup, IDS["KB Elevation"])
    row["DF Elevation"] = _text_by_id(soup, IDS["DF Elevation"])
    row["Single/Multiple Completion"] = _text_by_id(
        soup, IDS["Single/Multiple Completion"]
    )
    row["Potash Waiver"] = _text_by_id(soup, IDS["Potash Waiver"])
    row["Spud Date"] = _text_by_id(soup, IDS["Spud Date"])
    row["Last Inspection"] = _text_by_id(soup, IDS["Last Inspection"])
    row["TVD"] = _text_by_id(soup, IDS["TVD"])
    row["API"] = api
    row["Latitude"] = lat
    row["Longitude"] = lon
    row["CRS"] = crs
    return row
