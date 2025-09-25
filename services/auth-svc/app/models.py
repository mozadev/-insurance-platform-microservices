"""Pydantic models for auth service."""

from datetime import datetime

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    """Token request model."""

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=100)


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    customer_id: str


class UserInfo(BaseModel):
    """User information model."""

    customer_id: str
    username: str
    email: str | None = None
    created_at: datetime


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    message: str
    details: dict | None = None
