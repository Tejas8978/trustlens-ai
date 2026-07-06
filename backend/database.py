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
