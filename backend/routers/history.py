"""History router — returns scan logs from the database."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db, ScanLog
from schemas import ScanLogOut

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/", response_model=List[ScanLogOut])
def get_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    scan_type: str = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(ScanLog).order_by(ScanLog.created_at.desc())
    if scan_type:
        query = query.filter(ScanLog.scan_type == scan_type)
    return query.offset(skip).limit(limit).all()


@router.delete("/{scan_id}")
def delete_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(ScanLog).filter(ScanLog.id == scan_id).first()
    if scan:
        db.delete(scan)
        db.commit()
    return {"ok": True}
