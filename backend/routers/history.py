"""History router — returns scan logs from MongoDB."""
from fastapi import APIRouter, Query
from typing import List
from schemas import ScanLogOut
import database

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/", response_model=List[ScanLogOut])
def get_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    scan_type: str = Query(None),
):
    return database.get_history(skip=skip, limit=limit, scan_type=scan_type)


@router.delete("/{scan_id}")
def delete_scan(scan_id: str):
    database.delete_one(scan_id)
    return {"ok": True}
