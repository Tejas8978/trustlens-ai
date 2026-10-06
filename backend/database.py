"""
TrustLens AI — MongoDB database layer (PyMongo)
Manages scan_logs, users, and login_logs collections with resilient pooling,
safe timeouts, native BSON schema, and secure credential handling.
"""
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import bcrypt
import certifi
from bson import ObjectId
from pymongo import MongoClient, DESCENDING, ReturnDocument
from dotenv import load_dotenv

load_dotenv()

_raw_uri = (os.getenv("MONGO_URI") or "").strip()
MONGO_URI = _raw_uri if _raw_uri else "mongodb://localhost:27017"
DB_NAME = (os.getenv("MONGO_DB_NAME") or "trustlens").strip()
MONGO_TIMEOUT_MS = int(os.getenv("MONGO_TIMEOUT_MS", "4000"))

_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    """Returns singleton MongoClient instance with responsive fail-fast timeouts."""
    global _client
    if _client is None:
        kwargs: Dict[str, Any] = {
            "serverSelectionTimeoutMS": MONGO_TIMEOUT_MS,
            "connectTimeoutMS": 5000,
            "maxPoolSize": 50,
            "minPoolSize": 1,
        }
        if "mongodb+srv://" in MONGO_URI or "tls=true" in MONGO_URI.lower() or "ssl=true" in MONGO_URI.lower():
            try:
                kwargs["tlsCAFile"] = certifi.where()
            except Exception:
                pass
        _client = MongoClient(MONGO_URI, **kwargs)
    return _client


def close_db():
    """Safely terminates all open connection pools on shutdown."""
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
        _client = None


def ping_db() -> bool:
    """Verifies active connectivity to MongoDB without throwing."""
    try:
        client = get_client()
        client.admin.command("ping")
        return True
    except Exception:
        return False


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
    """Create indexes for performance and security. Logs connection status."""
    try:
        if not ping_db():
            print(f"[DB] WARNING: MongoDB unreachable at {MONGO_URI}. Operating in offline/resilient mode.")
            return

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
# Password & Auth Helpers
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hashes plain-text password using bcrypt with salt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain-text password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_user_by_email(email: str) -> Optional[dict]:
    """Fetches user document by email from MongoDB."""
    try:
        users_col = get_users_collection()
        return users_col.find_one({"email": email.strip().lower()})
    except Exception as e:
        print(f"[DB] Error querying user: {e}")
        return None


def verify_user_credentials(
    email: str,
    password: Optional[str],
    auth_type: str = "password",
) -> dict:
    """
    Validates operative authentication credentials.
    Supports biometric clearance and quick demo access while securely enforcing
    password verification for password-based logins with existing hashes.
    """
    clean_email = (email or "").strip().lower()
    if not clean_email:
        return {"ok": False, "error": "Operative email is required"}

    if auth_type in ("biometric", "quick_demo"):
        return {"ok": True}

    user = get_user_by_email(clean_email)
    if not user:
        # First-time operative login with password: allowed, hash will be stored
        return {"ok": True}

    stored_hash = user.get("password_hash")
    if not stored_hash:
        # Existing unhashed record: migrate on this login
        return {"ok": True}

    if not password or not verify_password(password, stored_hash):
        return {"ok": False, "error": "Invalid operative clearance credentials"}

    return {"ok": True}


# ---------------------------------------------------------------------------
# Scan Logs CRUD helpers
# ---------------------------------------------------------------------------

def add_history(data: dict) -> str:
    """
    Insert a scan result into scan_logs.
    Stores clean structured evidence and recommendations while avoiding
    unnecessary bloat from raw visual binary artifacts.
    """
    try:
        col = get_collection()

        # Clean evidence list: extract dictionaries without heavy binary strings
        raw_evidence = data.get("evidence", [])
        evidence_list = []
        for item in raw_evidence:
            if hasattr(item, "model_dump"):
                evidence_list.append(item.model_dump())
            elif hasattr(item, "dict"):
                evidence_list.append(item.dict())
            elif isinstance(item, dict):
                evidence_list.append(item)

        raw_recs = data.get("recommendations", [])
        recommendations = [str(r) for r in raw_recs] if isinstance(raw_recs, list) else []

        doc = {
            "scan_type":         data.get("scan_type") or data.get("type", "unknown"),
            "filename":          data.get("filename"),
            "risk_score":        float(data.get("risk_score") or data.get("confidence", 0)),
            "verdict":           (data.get("verdict") or data.get("risk_level", "SUSPICIOUS")).upper(),
            "summary":           str(data.get("summary") or ""),
            "evidence":          evidence_list,
            "recommendations":   recommendations,
            "ai_builder_prompt": data.get("ai_builder_prompt"),
            "created_at":        datetime.now(timezone.utc),
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
            created_at = doc.get("created_at")
            if isinstance(created_at, datetime):
                dt_val = created_at
            else:
                dt_val = datetime.now(timezone.utc)

            result.append({
                "id":         str(doc["_id"]),
                "scan_type":  doc.get("scan_type", ""),
                "filename":   doc.get("filename"),
                "risk_score": doc.get("risk_score", 0.0),
                "verdict":    doc.get("verdict", "UNKNOWN"),
                "summary":    doc.get("summary", ""),
                "created_at": dt_val,
            })
        return result
    except Exception as e:
        print(f"[DB] Error getting history: {e}")
        return []


def get_history_count(scan_type: Optional[str] = None) -> int:
    """Returns total count of scans for pagination metrics."""
    try:
        col = get_collection()
        query: Dict[str, Any] = {}
        if scan_type:
            query["scan_type"] = scan_type
        return col.count_documents(query)
    except Exception:
        return 0


def get_scan(scan_id: str) -> Optional[dict]:
    """Retrieve full scan details by string ObjectId."""
    if not ObjectId.is_valid(scan_id):
        return None
    try:
        col = get_collection()
        doc = col.find_one({"_id": ObjectId(scan_id)})
        if not doc:
            return None

        created_at = doc.get("created_at")
        dt_val = created_at if isinstance(created_at, datetime) else datetime.now(timezone.utc)

        return {
            "id":                str(doc["_id"]),
            "scan_type":         doc.get("scan_type", "unknown"),
            "filename":          doc.get("filename"),
            "risk_score":        doc.get("risk_score", 0.0),
            "verdict":           doc.get("verdict", "UNKNOWN"),
            "summary":           doc.get("summary", ""),
            "evidence":          doc.get("evidence", []),
            "recommendations":   doc.get("recommendations", []),
            "ai_builder_prompt": doc.get("ai_builder_prompt"),
            "created_at":        dt_val,
        }
    except Exception as e:
        print(f"[DB] Error fetching scan {scan_id}: {e}")
        return None


def delete_one(scan_id: str) -> bool:
    """Delete a single scan by string ObjectId. Returns True if deleted."""
    if not ObjectId.is_valid(scan_id):
        return False
    try:
        col = get_collection()
        result = col.delete_one({"_id": ObjectId(scan_id)})
        return result.deleted_count > 0
    except Exception as e:
        print(f"[DB] Error deleting scan {scan_id}: {e}")
        return False


def delete_all() -> bool:
    """Clear all scans from the collection."""
    try:
        col = get_collection()
        col.delete_many({})
        return True
    except Exception as e:
        print(f"[DB] Error clearing history: {e}")
        return False


# ---------------------------------------------------------------------------
# User & Login Telemetry CRUD helpers
# ---------------------------------------------------------------------------

def record_login(
    user_data: dict,
    auth_type: str = "password",
    ip: Optional[str] = "127.0.0.1",
    user_agent: Optional[str] = "TrustLens Secure Terminal",
    password: Optional[str] = None,
) -> dict:
    """
    Feeds login event into MongoDB:
    1. Upserts operative in 'users' collection with login counter and last_login.
    2. Stores bcrypt password hash if provided.
    3. Inserts an immutable audit event in 'login_logs' collection.
    """
    email = (user_data.get("email") or "operative@trustlens.ai").strip().lower()
    name = (user_data.get("name") or email.split("@")[0]).strip()
    role = user_data.get("role") or "Forensic Analyst"
    auth_level = user_data.get("auth_level") or (
        "LEVEL 5 // BIOMETRIC MASTER" if auth_type == "biometric" else "LEVEL 4 // CLEARANCE GRANTED"
    )
    now = datetime.now(timezone.utc)

    set_fields: Dict[str, Any] = {
        "name": name,
        "role": role,
        "auth_level": auth_level,
        "last_login": now,
        "status": "ACTIVE",
    }
    if password and password.strip():
        set_fields["password_hash"] = hash_password(password.strip())

    try:
        users_col = get_users_collection()
        user_doc = users_col.find_one_and_update(
            {"email": email},
            {
                "$set": set_fields,
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
    """Retrieve registered operative accounts from MongoDB (excluding sensitive hashes)."""
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
