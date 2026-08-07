"""
TrustLens AI — MongoDB database layer (PyMongo)
"""
import os
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient, DESCENDING
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "trustlens")

_client: MongoClient = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client


def get_collection():
    return get_client()[DB_NAME]["scan_logs"]


def init_db():
    """Create indexes for performance."""
    col = get_collection()
    col.create_index([("created_at", DESCENDING)])
    col.create_index([("scan_type", 1)])
    print(f"[DB] Connected to MongoDB — database: '{DB_NAME}'")


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------

def add_history(data: dict) -> str:
    """Insert a scan result into the scan_logs collection. Returns inserted id."""
    try:
        col = get_collection()
        doc = {
            "scan_type":  data.get("scan_type") or data.get("type", "unknown"),
            "filename":   data.get("filename"),
            "risk_score": float(data.get("risk_score") or data.get("confidence", 0)),
            "verdict":    (data.get("verdict") or data.get("risk_level", "SUSPICIOUS")).upper(),
            "summary":    str(data.get("summary") or data.get("details", "")),
            "details":    str(data),
            "created_at": datetime.now(timezone.utc),
        }
        result = col.insert_one(doc)
        return str(result.inserted_id)
    except Exception as e:
        print(f"[DB] Error adding to history: {e}")
        return ""


def get_history(
    skip: int = 0,
    limit: int = 50,
    scan_type: str = None,
) -> list:
    """Return scan logs, newest first, with optional type filter."""
    try:
        col = get_collection()
        query = {}
        if scan_type:
            query["scan_type"] = scan_type
        cursor = (
            col.find(query)
            .sort("created_at", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        result = []
        for doc in cursor:
            result.append({
                "id":         str(doc["_id"]),
                "scan_type":  doc.get("scan_type", ""),
                "filename":   doc.get("filename"),
                "risk_score": doc.get("risk_score", 0.0),
                "verdict":    doc.get("verdict", "UNKNOWN"),
                "summary":    doc.get("summary", ""),
                "created_at": doc.get("created_at"),
            })
        return result
    except Exception as e:
        print(f"[DB] Error getting history: {e}")
        return []


def delete_one(scan_id: str) -> bool:
    """Delete a single scan by its string ObjectId. Returns True if deleted."""
    try:
        col = get_collection()
        result = col.delete_one({"_id": ObjectId(scan_id)})
        return result.deleted_count > 0
    except Exception as e:
        print(f"[DB] Error deleting scan {scan_id}: {e}")
        return False


def delete_all():
    """Clear all scans from the collection."""
    try:
        col = get_collection()
        col.delete_many({})
    except Exception as e:
        print(f"[DB] Error clearing history: {e}")
