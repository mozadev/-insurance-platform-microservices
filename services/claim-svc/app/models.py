"""Pydantic models for claim service."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class ClaimBase(BaseModel):
    """Base claim model."""
    policy_id: str = Field(..., pattern=r"^POL-[A-Z0-9]{8}$")
    customer_id: str = Field(..., pattern=r"^CUST-[A-Z0-9]{8}$")
    status: str = Field(..., regex="^(open|closed|in_review)$")
    amount: float = Field(..., ge=0)
    occurred_at: datetime
    description: Optional[str] = Field(None, max_length=1000)
    category: str = Field(..., regex="^(auto|property|health|life|other)$")


class ClaimCreate(ClaimBase):
    """Model for creating a claim."""
    idempotency_key: Optional[str] = Field(None, max_length=255)


class ClaimUpdate(BaseModel):
    """Model for updating a claim."""
    status: Optional[str] = Field(None, regex="^(open|closed|in_review)$")
    amount: Optional[float] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, regex="^(auto|property|health|life|other)$")


class Claim(ClaimBase):
    """Complete claim model."""
    claim_id: str = Field(..., pattern=r"^CLAIM-[A-Z0-9]{8}$")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ClaimResponse(BaseModel):
    """API response model for claim."""
    claim_id: str
    policy_id: str
    customer_id: str
    status: str
    amount: float
    occurred_at: datetime
    description: Optional[str]
    category: str
    created_at: datetime
    updated_at: datetime


class ClaimListResponse(BaseModel):
    """API response model for claim list."""
    claims: list[ClaimResponse]
    total: int
    next_token: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    details: Optional[dict] = None
