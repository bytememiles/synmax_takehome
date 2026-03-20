from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from synmax_takehome.api.deps import get_db_conn
from synmax_takehome.models import WellRecord
from synmax_takehome.storage.repository import get_well_by_api

router = APIRouter(prefix="/well", tags=["wells"])


@router.get("", response_model=WellRecord, response_model_by_alias=True)
def well(api: str, conn=Depends(get_db_conn)) -> WellRecord:
    """Return all DB fields for a single API number."""
    row = get_well_by_api(conn, api)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Well not found for API={api}")
    rec = WellRecord.model_validate(row)
    return rec
