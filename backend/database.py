"""
TrustLens AI — MongoDB database layer (PyMongo)
Manages scan_logs, users, and login_logs collections.
"""
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from bson import ObjectId
from pymongo import MongoClient, DESCENDING, ReturnDocument
from dotenv import load_dotenv

import certifi

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "trustlens")

_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        kwargs: Dict[str, Any] = {}
        if "mongodb+srv://" in MONGO_URI or "tls=true" in MONGO_URI.lower() or "ssl=true" in MONGO_URI.lower():
            try:
                kwargs["tlsCAFile"] = certifi.where()
            except Exception:
                pass
        _client = MongoClient(MONGO_URI, **kwargs)
    return _client


def get_collection():
    """Returns the scan_logs collection."""
    return get_client()[DB_NAME]["scan_logs"]


def get_users_collection():
    """Returns the registered operatives users collection."""
    return get_client()[DB_NAME]["users"]


def get_login_logs_collection():
    """Returns the login telemetry events collection."""
    return get_client()[DB_NAME]["login_logs"]


def init_db():
    """Create indexes for performance and security. Logs status."""
    try:
        col = get_collection()
        col.create_index([("created_at", DESCENDING)])
        col.create_index([("scan_type", 1)])

        users_col = get_users_collection()
        users_col.create_index([("email", 1)], unique=True)
        users_col.create_index([("last_login", DESCENDING)])

        logs_col = get_login_logs_collection()
        logs_col.create_index([("timestamp", DESCENDING)])
        logs_col.create_index([("email", 1)])

        print(f"[DB] Connected to MongoDB — database: '{DB_NAME}' (scan_logs, users, login_logs)")
    except Exception as e:
        print(f"[DB] WARNING: Could not connect to MongoDB on startup: {e}")
        print("[DB] Check that MONGO_URI environment variable is set correctly.")


# ---------------------------------------------------------------------------
# Scan Logs CRUD helpers
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
    scan_type: Optional[str] = None,
) -> list:
    """Return scan logs, newest first, with optional type filter."""
    try:
        col = get_collection()
        query: Dict[str, Any] = {}
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


# ---------------------------------------------------------------------------
# User & Login Telemetry CRUD helpers (Feeds into MongoDB)
# ---------------------------------------------------------------------------

def record_login(
    user_data: dict,
    auth_type: str = "password",
    ip: Optional[str] = "127.0.0.1",
    user_agent: Optional[str] = "TrustLens Secure Terminal",
) -> dict:
    """
    Feeds login event into MongoDB:
    1. Upserts operative in 'users' collection with login counter and last_login.
    2. Inserts an immutable audit event in 'login_logs' collection.
    """
    email = (user_data.get("email") or "operative@trustlens.ai").strip().lower()
    name = (user_data.get("name") or email.split("@")[0]).strip()
    role = user_data.get("role") or "Forensic Analyst"
    auth_level = user_data.get("auth_level") or (
        "LEVEL 5 // BIOMETRIC MASTER" if auth_type == "biometric" else "LEVEL 4 // CLEARANCE GRANTED"
    )
    now = datetime.now(timezone.utc)

    try:
        users_col = get_users_collection()
        user_doc = users_col.find_one_and_update(
            {"email": email},
            {
                "$set": {
                    "name": name,
                    "role": role,
                    "auth_level": auth_level,
                    "last_login": now,
                    "status": "ACTIVE",
                },
                "$setOnInsert": {
                    "created_at": now,
                },
                "$inc": {
                    "login_count": 1,
                },
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

        logs_col = get_login_logs_collection()
        log_doc = {
            "email": email,
            "name": name,
            "role": role,
            "auth_type": auth_type,
            "auth_level": auth_level,
            "client_ip": ip or "127.0.0.1",
            "user_agent": user_agent or "TrustLens Client",
            "status": "SUCCESS",
            "timestamp": now,
        }
        log_res = logs_col.insert_one(log_doc)

        user_id = str(user_doc["_id"]) if user_doc and "_id" in user_doc else ""
        return {
            "id": user_id,
            "log_id": str(log_res.inserted_id),
            "email": email,
            "name": name,
            "role": role,
            "auth_level": auth_level,
            "login_count": user_doc.get("login_count", 1) if user_doc else 1,
            "last_login": now.isoformat(),
            "status": "ACTIVE",
            "mongodb_connected": True,
        }
    except Exception as e:
        print(f"[DB] Error recording login to MongoDB: {e}")
        return {
            "id": "",
            "log_id": "",
            "email": email,
            "name": name,
            "role": role,
            "auth_level": auth_level,
            "login_count": 1,
            "last_login": now.isoformat(),
            "status": "ACTIVE",
            "mongodb_connected": False,
        }


def get_login_logs(limit: int = 50) -> List[dict]:
    """Retrieve recent login telemetry logs from MongoDB."""
    try:
        logs_col = get_login_logs_collection()
        cursor = logs_col.find().sort("timestamp", DESCENDING).limit(limit)
        results = []
        for doc in cursor:
            ts = doc.get("timestamp")
            results.append({
                "id": str(doc["_id"]),
                "email": doc.get("email", ""),
                "name": doc.get("name", "Operative"),
                "role": doc.get("role", "Forensic Analyst"),
                "auth_type": doc.get("auth_type", "password"),
                "auth_level": doc.get("auth_level", "LEVEL 4 // CLEARANCE GRANTED"),
                "client_ip": doc.get("client_ip", "127.0.0.1"),
                "user_agent": doc.get("user_agent", ""),
                "status": doc.get("status", "SUCCESS"),
                "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
            })
        return results
    except Exception as e:
        print(f"[DB] Error fetching login logs: {e}")
        return []


def get_users_list(limit: int = 50) -> List[dict]:
    """Retrieve registered operative accounts from MongoDB."""
    try:
        users_col = get_users_collection()
        cursor = users_col.find().sort("last_login", DESCENDING).limit(limit)
        results = []
        for doc in cursor:
            ll = doc.get("last_login")
            ca = doc.get("created_at")
            results.append({
                "id": str(doc["_id"]),
                "email": doc.get("email", ""),
                "name": doc.get("name", "Operative"),
                "role": doc.get("role", "Forensic Analyst"),
                "auth_level": doc.get("auth_level", "LEVEL 4 // CLEARANCE GRANTED"),
                "login_count": doc.get("login_count", 1),
                "last_login": ll.isoformat() if hasattr(ll, "isoformat") else str(ll),
                "created_at": ca.isoformat() if hasattr(ca, "isoformat") else str(ca),
                "status": doc.get("status", "ACTIVE"),
            })
        return results
    except Exception as e:
        print(f"[DB] Error fetching users list: {e}")
        return []


def clear_login_logs() -> bool:
    """Clear all login logs from collection."""
    try:
        logs_col = get_login_logs_collection()
        logs_col.delete_many({})
        return True
    except Exception as e:
        print(f"[DB] Error clearing login logs: {e}")
        return False
