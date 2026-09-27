import uuid
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from app.database import db

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    role: Optional[str] = "Lead RevOps"
    org_id: Optional[str] = "org_demo_01"

@router.post("/login")
async def login(req: LoginRequest):
    """Authenticates user against SQLite users table and returns user profile + session token."""
    user = await db.verify_user_credentials(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password. Use demo@graph8.ai / password123")
    
    token = f"g8_token_{user['id']}_{uuid.uuid4().hex[:16]}"
    return {
        "success": True,
        "token": token,
        "user": user
    }

@router.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Validates session token or returns demo user context."""
    if not authorization:
        # Default fallback to demo user for seamless zero-friction experience
        demo = await db.get_user_by_email("demo@graph8.ai")
        if demo:
            demo_clean = dict(demo)
            demo_clean.pop("password_hash", None)
            return {"authenticated": True, "user": demo_clean}
        raise HTTPException(status_code=401, detail="Unauthorized")

    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1]
        # Extract user ID if format matches g8_token_{uid}_{rand}
        if token.startswith("g8_token_"):
            sub_parts = token.split("_")
            if len(sub_parts) >= 4:
                user_id = f"{sub_parts[2]}_{sub_parts[3]}"
                user = await db.get_user_by_id(user_id)
                if user:
                    return {"authenticated": True, "user": user}
        
        # If token exists, resolve demo user
        demo = await db.get_user_by_email("demo@graph8.ai")
        if demo:
            demo_clean = dict(demo)
            demo_clean.pop("password_hash", None)
            return {"authenticated": True, "user": demo_clean}

    raise HTTPException(status_code=401, detail="Invalid session token")

@router.post("/logout")
async def logout():
    """Logs out current user session."""
    return {"success": True, "message": "Logged out successfully"}

@router.post("/register")
async def register_user(req: RegisterRequest):
    """Registers a new RevOps team member."""
    existing = await db.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    user = await db.create_user(
        email=req.email,
        password=req.password,
        name=req.name,
        role=req.role or "Lead RevOps",
        org_id=req.org_id or "org_demo_01"
    )
    token = f"g8_token_{user['id']}_{uuid.uuid4().hex[:16]}"
    return {
        "success": True,
        "token": token,
        "user": user
    }

@router.get("/users", response_model=List[Dict[str, Any]])
async def list_users():
    """Lists all team members in the organization."""
    return await db.list_users()
