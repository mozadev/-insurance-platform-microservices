"""Pydantic models for policy service."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class PolicyBase(BaseModel):
    """Base policy model."""
    customer_id: str = Field(..., pattern=r"^CUST-[A-Z0-9]{8}$")
    status: str = Field(..., regex="^(active|inactive|cancelled|expired)$")
    premium: float = Field(..., ge=0)
    effective_date: date
    expiration_date: date
    coverage_type: str = Field(..., regex="^(auto|property|health|life|other)$")
    deductible: float = Field(..., ge=0)
    coverage_limit: float = Field(..., ge=0)
    
    @validator('expiration_date')
    def validate_expiration_date(cls, v, values):
        if 'effective_date' in values and v <= values['effective_date']:
            raise ValueError('expiration_date must be after effective_date')
        return v


class PolicyCreate(PolicyBase):
    """Model for creating a policy."""
    pass


class PolicyUpdate(BaseModel):
    """Model for updating a policy."""
    status: Optional[str] = Field(None, regex="^(active|inactive|cancelled|expired)$")
    premium: Optional[float] = Field(None, ge=0)
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    coverage_type: Optional[str] = Field(None, regex="^(auto|property|health|life|other)$")
    deductible: Optional[float] = Field(None, ge=0)
    coverage_limit: Optional[float] = Field(None, ge=0)


class Policy(PolicyBase):
    """Complete policy model."""
    policy_id: str = Field(..., pattern=r"^POL-[A-Z0-9]{8}$")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PolicyResponse(BaseModel):
    """API response model for policy."""
    policy_id: str
    customer_id: str
    status: str
    premium: float
    effective_date: date
    expiration_date: date
    coverage_type: str
    deductible: float
    coverage_limit: float
    created_at: datetime
    updated_at: datetime


class PolicyListResponse(BaseModel):
    """API response model for policy list."""
    policies: list[PolicyResponse]
    total: int
    next_token: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    details: Optional[dict] = None
