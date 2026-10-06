"""
Authentication & Operative Session Router
Feeds login credentials, registrations, and session audit logs into MongoDB.
"""
from typing import Optional, List
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
    if not payload.email.strip():
        raise HTTPException(status_code=400, detail="Operative email is required")

    # Credential verification check
    auth_check = database.verify_user_credentials(
        email=payload.email,
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
        "email": payload.email,
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


@router.post("/register", response_model=UserResponse)
async def register_endpoint(payload: AuthRequest, request: Request):
    """
    Registers a new operative into MongoDB 'users' with secure password hash
    and logs initial access into 'login_logs'.
    """
    if not payload.email.strip():
        raise HTTPException(status_code=400, detail="Operative email is required")
    if not payload.name or not payload.name.strip():
        raise HTTPException(status_code=400, detail="Operative designation name is required")

    forwarded_for = request.headers.get("x-forwarded-for")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "127.0.0.1")
    user_agent = request.headers.get("user-agent", "TrustLens Web Terminal")

    user_info = {
        "email": payload.email,
        "name": payload.name,
        "role": payload.role or "Forensic Analyst",
        "auth_level": payload.auth_level or "LEVEL 4 // CLEARANCE GRANTED",
    }

    result = database.record_login(
        user_data=user_info,
        auth_type="register",
        ip=client_ip,
        user_agent=user_agent,
        password=payload.password,
    )

    return UserResponse(**result)


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
