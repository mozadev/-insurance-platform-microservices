"""Pydantic models for search service."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Individual search result."""

    id: str
    type: str  # "policy" or "claim"
    score: float
    source: dict[str, Any]


class SearchResponse(BaseModel):
    """Search API response."""

    query: str
    results: list[SearchResult]
    total: int
    took: int  # milliseconds
    page: int = 1
    size: int = 20
    next_page: int | None = None


class SearchRequest(BaseModel):
    """Search request model."""

    query: str = Field(..., min_length=1, max_length=500)
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    filters: dict[str, Any] | None = None
    sort: str | None = None


class IndexDocument(BaseModel):
    """Document to be indexed."""

    id: str
    type: str
    data: dict[str, Any]
    indexed_at: datetime


class BulkIndexRequest(BaseModel):
    """Bulk index request."""

    documents: list[IndexDocument]


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    message: str
    details: dict[str, Any] | None = None
