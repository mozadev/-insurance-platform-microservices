"""Search API routes."""

from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ...shared.logging import LoggerMixin
from ..models import SearchRequest, SearchResponse, IndexDocument, BulkIndexRequest, ErrorResponse
from ..repositories.opensearch import SearchRepository

router = APIRouter(prefix="/search", tags=["search"])
security = HTTPBearer()


class SearchService(LoggerMixin):
    """Search service business logic."""
    
    def __init__(self, repository: SearchRepository):
        self.repository = repository
    
    def search(
        self, 
        query: str, 
        page: int = 1, 
        size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None
    ) -> SearchResponse:
        """Perform search across policies and claims."""
        try:
            return self.repository.search(
                query=query,
                page=page,
                size=size,
                filters=filters,
                sort=sort
            )
        except Exception as e:
            self.logger.error("Search failed", error=str(e), query=query)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Search failed: {str(e)}"
            )
    
    def index_document(self, document: IndexDocument) -> bool:
        """Index a single document."""
        try:
            return self.repository.index_document(document)
        except Exception as e:
            self.logger.error("Failed to index document", error=str(e), id=document.id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to index document: {str(e)}"
            )
    
    def bulk_index(self, documents: list[IndexDocument]) -> Dict[str, int]:
        """Bulk index multiple documents."""
        try:
            success_count, failed_count = self.repository.bulk_index(documents)
            return {
                "success_count": success_count,
                "failed_count": failed_count,
                "total": len(documents)
            }
        except Exception as e:
            self.logger.error("Bulk indexing failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Bulk indexing failed: {str(e)}"
            ) from e


# Dependency injection
def get_search_service() -> SearchService:
    """Get search service instance."""
    from ...shared.config import get_settings
    from ...shared.aws import get_opensearch_client
    
    settings = get_settings()
    opensearch_client = get_opensearch_client(settings)
    repository = SearchRepository(opensearch_client, settings.opensearch_index_prefix)
    
    return SearchService(repository)


def get_current_customer(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current customer from JWT token."""
    from ...shared.config import get_settings
    from ...shared.logging import get_logger
    
    # For search service, we'll use a simple token validation
    # In production, this would integrate with the auth service
    _ = get_settings()
    _ = get_logger(__name__)
    
    # Simple token validation for demo purposes
    if not credentials.credentials or credentials.credentials != "demo-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    return "CUST-DEMO01"  # Demo customer ID


@router.get("/", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    coverage_type: Optional[str] = Query(None, description="Filter by coverage type"),
    sort: Optional[str] = Query(None, description="Sort field (prefix with - for desc)"),
    customer_id: str = Depends(get_current_customer),
    service: SearchService = Depends(get_search_service)
):
    """Search across policies and claims."""
    # Build filters
    filters = {}
    if status:
        filters["status"] = status
    if category:
        filters["category"] = category
    if coverage_type:
        filters["coverageType"] = coverage_type
    
    # Add customer filter
    filters["customerId"] = customer_id
    
    return service.search(
        query=q,
        page=page,
        size=size,
        filters=filters if filters else None,
        sort=sort
    )


@router.post("/index", response_model=Dict[str, Any])
async def index_document(
    document: IndexDocument,
    customer_id: str = Depends(get_current_customer),
    service: SearchService = Depends(get_search_service)
):
    """Index a single document."""
    success = service.index_document(document)
    return {"success": success, "id": document.id}


@router.post("/bulk-index", response_model=Dict[str, int])
async def bulk_index(
    request: BulkIndexRequest,
    customer_id: str = Depends(get_current_customer),
    service: SearchService = Depends(get_search_service)
):
    """Bulk index multiple documents."""
    return service.bulk_index(request.documents)


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    doc_type: str = Query(..., regex="^(policy|claim)$"),
    customer_id: str = Depends(get_current_customer),
    service: SearchService = Depends(get_search_service)
):
    """Delete a document from the search index."""
    success = service.repository.delete_document(doc_id, doc_type)
    return {"success": success, "id": doc_id}
