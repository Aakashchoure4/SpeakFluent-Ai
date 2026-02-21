"""
Pydantic request / response schemas for authentication.
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    full_name: Optional[str] = Field(None, max_length=150)
    preferred_language: str = Field(default="en", pattern="^(en|hi)$")


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
class UserLogin(BaseModel):
    username: str
    password: str


# ---------------------------------------------------------------------------
# Token
# ---------------------------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ---------------------------------------------------------------------------
# User Response
# ---------------------------------------------------------------------------
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    preferred_language: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True
