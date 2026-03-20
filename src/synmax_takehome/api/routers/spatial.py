from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/search", tags=["spatial"])

from synmax_takehome.api.deps import get_db_conn
from synmax_takehome.storage.repository import apis_in_polygon


_PAIR_RE = re.compile(r"\(\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\)")


def _parse_polygon_points(points: str) -> list[tuple[float, float]]:
    """Parse a polygon string like [(32.81,-104.19),(32.66,-104.32), ...]."""
    pairs = [(float(a), float(b)) for a, b in _PAIR_RE.findall(points)]
    if pairs:
        return pairs

    # Fallback: extract floats and pair sequentially.
    nums = [float(x) for x in re.findall(r"[+-]?\d+(?:\.\d+)?", points)]
    if len(nums) % 2 != 0:
        raise ValueError("Invalid polygon input: uneven lat/lon values.")
    return [(nums[i], nums[i + 1]) for i in range(0, len(nums), 2)]


@router.get("/polygon", response_class=list)
def polygon(points: str, conn=Depends(get_db_conn)) -> list[str]:
    """Return a list of API numbers within the provided polygon."""
    try:
        polygon_lat_lon = _parse_polygon_points(points)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if len(polygon_lat_lon) < 3:
        raise HTTPException(
            status_code=400, detail="Polygon requires at least 3 (lat,lon) points."
        )

    return apis_in_polygon(conn, polygon_lat_lon)
