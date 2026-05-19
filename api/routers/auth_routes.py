# api/routers/auth_routes.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from api.auth import create_token, hash_password, verify_password
from ingestion.db import run_query

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    """Create a new user account."""
    existing = run_query("SELECT id FROM users WHERE email = %s", (body.email.lower(),), fetch=True)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(body.password)
    rows = run_query(
        """
        INSERT INTO users (email, hashed_password)
        VALUES (%s, %s)
        RETURNING id
        """,
        (body.email.lower(), hashed),
        fetch=True,
    )
    user_id = rows[0][0]
    return TokenResponse(access_token=create_token(user_id))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    """Authenticate and return a JWT."""
    rows = run_query(
        "SELECT id, hashed_password FROM users WHERE email = %s",
        (body.email.lower(),),
        fetch=True,
    )
    if not rows or not verify_password(body.password, rows[0][1]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return TokenResponse(access_token=create_token(rows[0][0]))
