"""History router — returns scan logs from MongoDB."""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from schemas import ScanLogOut, ScanDetailOut
import database

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/", response_model=List[ScanLogOut])
def get_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    scan_type: Optional[str] = Query(None),
):
    """Retrieve paginated scan logs, optionally filtered by scan_type."""
    return database.get_history(skip=skip, limit=limit, scan_type=scan_type)


@router.get("/{scan_id}", response_model=ScanDetailOut)
def get_scan_details(scan_id: str):
    """Retrieve complete evidence breakdown and recommendations for a single scan."""
    scan = database.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Forensic scan record not found or ID is invalid")
    return ScanDetailOut(**scan)


@router.delete("/{scan_id}")
def delete_scan(scan_id: str):
    """Delete a single scan record from history."""
    deleted = database.delete_one(scan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scan record not found or could not be deleted")
    return {"ok": True, "deleted": True}


@router.delete("/")
def clear_all_history():
    """Clear all scan records from MongoDB history."""
    cleared = database.delete_all()
    return {"ok": True, "cleared": cleared}
