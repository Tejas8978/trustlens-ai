"""
Authentication & Operative Session Router
Feeds login credentials, registrations, and session audit logs into MongoDB.
"""
from typing import Optional, List
import re
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import database

router = APIRouter(prefix="/api/auth", tags=["auth"])


class AuthRequest(BaseModel):
    email: str
    password: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = "Forensic Analyst"
    auth_type: Optional[str] = "password"  # password | biometric | quick_demo | register
    auth_level: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    log_id: Optional[str] = ""
    email: str
    name: str
    role: str
    auth_level: str
    login_count: int
    last_login: str
    status: str
    mongodb_connected: bool


class LoginAuditItem(BaseModel):
    id: str
    email: str
    name: str
    role: str
    auth_type: str
    auth_level: str
    client_ip: str
    user_agent: str
    status: str
    timestamp: str


@router.post("/login", response_model=UserResponse)
async def login_endpoint(payload: AuthRequest, request: Request):
    """
    Feeds operative login details directly into MongoDB:
    Verifies credentials (or biometric / demo clearance), updates operative record in 'users',
    and stores an immutable audit log in 'login_logs'.
    """
    clean_email = (payload.email or "").strip().lower()
    if not clean_email:
        raise HTTPException(status_code=400, detail="Operative email is required")

    # Credential verification check
    auth_check = database.verify_user_credentials(
        email=clean_email,
        password=payload.password,
        auth_type=payload.auth_type or "password",
    )
    if not auth_check.get("ok"):
        raise HTTPException(
            status_code=401,
            detail=auth_check.get("error", "Invalid operative clearance credentials"),
        )

    forwarded_for = request.headers.get("x-forwarded-for")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "127.0.0.1")
    user_agent = request.headers.get("user-agent", "TrustLens Web Terminal")

    user_info = {
        "email": clean_email,
        "name": payload.name,
        "role": payload.role,
        "auth_level": payload.auth_level,
    }

    result = database.record_login(
        user_data=user_info,
        auth_type=payload.auth_type or "password",
        ip=client_ip,
        user_agent=user_agent,
        password=payload.password,
    )

    return UserResponse(**result)


@router.get("/check-email")
def check_email_endpoint(email: str):
    """
    Checks if an email is already registered in MongoDB.
    Returns {"exists": True/False, "email": "..."}
    """
    clean_email = (email or "").strip().lower()
    if not clean_email:
        return {"exists": False, "email": ""}
    user = database.get_user_by_email(clean_email)
    return {"exists": user is not None, "email": clean_email}


@router.post("/register", response_model=UserResponse)
async def register_endpoint(payload: AuthRequest, request: Request):
    """
    Registers a new user into MongoDB 'users' collection with secure password hash
    and logs initial access into 'login_logs'.
    Strictly enforces only one account per email address.
    """
    clean_email = (payload.email or "").strip().lower()
    if not clean_email:
        raise HTTPException(status_code=400, detail="Email address is required.")
    if not payload.name or not payload.name.strip():
        raise HTTPException(status_code=400, detail="Full name is required.")
    
    pwd = (payload.password or "").strip()
    if len(pwd) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")

    has_upper = bool(re.search(r"[A-Z]", pwd))
    has_lower = bool(re.search(r"[a-z]", pwd))
    has_digit = bool(re.search(r"[0-9]", pwd))
    has_special = bool(re.search(r"[^A-Za-z0-9]", pwd))

    if not (has_upper and has_lower and has_digit and has_special):
        raise HTTPException(
            status_code=400,
            detail="Password must combine uppercase letters (A-Z), lowercase letters (a-z), numbers (0-9), and special characters (e.g. !@#$%).",
        )

    forwarded_for = request.headers.get("x-forwarded-for")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "127.0.0.1")
    user_agent = request.headers.get("user-agent", "TrustLens Web Terminal")

    reg_result = database.create_user(
        email=clean_email,
        name=payload.name.strip(),
        password=payload.password,
        role=payload.role or "User",
        auth_level=payload.auth_level or "LEVEL 4 // CLEARANCE GRANTED",
        ip=client_ip,
        user_agent=user_agent,
    )

    if not reg_result.get("ok"):
        if reg_result.get("already_exists"):
            raise HTTPException(
                status_code=409,
                detail="This email address is already registered. Only one account is permitted per email. Please sign in instead.",
            )
        if not reg_result.get("mongodb_connected", True):
            raise HTTPException(
                status_code=503,
                detail="MongoDB database is currently unreachable. Could not save account to MongoDB Atlas.",
            )
        raise HTTPException(
            status_code=400,
            detail=reg_result.get("error", "Account registration failed."),
        )

    return UserResponse(**reg_result)


@router.get("/logs", response_model=List[LoginAuditItem])
def get_login_logs_endpoint(limit: int = 50):
    """
    Retrieves recent operative login telemetry directly from MongoDB 'login_logs'.
    """
    logs = database.get_login_logs(limit=limit)
    return [LoginAuditItem(**log) for log in logs]


@router.get("/users")
def get_users_endpoint(limit: int = 50):
    """
    Retrieves registered operatives from MongoDB 'users' collection.
    """
    return database.get_users_list(limit=limit)


@router.delete("/logs")
def clear_login_logs_endpoint():
    """Clear all login telemetry logs from MongoDB."""
    success = database.clear_login_logs()
    return {"success": success, "message": "Login telemetry logs cleared"}
