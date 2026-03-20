from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from synmax_takehome.api.deps import get_db_conn
from synmax_takehome.models import WellRecord
from synmax_takehome.storage.repository import get_well_by_api

router = APIRouter(prefix="/well", tags=["wells"])


@router.get("", response_class=dict)
def well(api: str, conn=Depends(get_db_conn)) -> dict:
    """Return all DB fields for a single API number."""
    row = get_well_by_api(conn, api)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Well not found for API={api}")
    rec = WellRecord.model_validate(row)
    # by_alias=True ensures keys match the PDF/DDL columns (e.g. \"Well Type\").
    return rec.model_dump(by_alias=True)
