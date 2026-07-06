from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timezone

SQLALCHEMY_DATABASE_URL = "sqlite:///./trustlens.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    scan_type = Column(String, nullable=False)          # image | audio | video | sms | email
    filename = Column(String, nullable=True)
    risk_score = Column(Float, nullable=False)
    verdict = Column(String, nullable=False)            # SAFE | SUSPICIOUS | HIGH_RISK
    summary = Column(Text, nullable=False)
    details = Column(Text, nullable=True)               # JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)


def add_history(data: dict):
    """Add a scan to the database"""
    try:
        db = SessionLocal()
        scan = ScanLog(
            scan_type=data.get("type", "unknown"),
            filename=data.get("filename", ""),
            risk_score=float(data.get("confidence", 0)),
            verdict=data.get("risk_level", "SUSPICIOUS").upper(),
            summary=str(data.get("details", "")),
            details=str(data)
        )
        db.add(scan)
        db.commit()
        db.close()
    except Exception as e:
        print(f"Error adding to history: {e}")


def get_history() -> list:
    """Get all scans from the database"""
    try:
        db = SessionLocal()
        scans = db.query(ScanLog).order_by(ScanLog.created_at.desc()).all()
        result = []
        for scan in scans:
            result.append({
                "id": scan.id,
                "type": scan.scan_type,
                "filename": scan.filename,
                "risk_level": scan.verdict,
                "confidence": scan.risk_score,
                "details": scan.summary,
                "created_at": scan.created_at
            })
        db.close()
        return result
    except Exception as e:
        print(f"Error getting history: {e}")
        return []


def delete_history():
    """Clear all scans from the database"""
    try:
        db = SessionLocal()
        db.query(ScanLog).delete()
        db.commit()
        db.close()
    except Exception as e:
        print(f"Error deleting history: {e}")

