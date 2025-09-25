"""Claim API routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ...shared.logging import LoggerMixin
from ..auth.jwt_stub import JWTStub
from ..models import ClaimCreate, ClaimResponse, ClaimListResponse, ClaimUpdate, ErrorResponse
from ..repositories.dynamodb import ClaimRepository
from ..idempotency.dynamodb import IdempotencyManager

router = APIRouter(prefix="/claims", tags=["claims"])
security = HTTPBearer()


class ClaimService(LoggerMixin):
    """Claim service business logic."""
    
    def __init__(
        self, 
        repository: ClaimRepository, 
        event_publisher, 
        jwt_auth: JWTStub,
        idempotency_manager: IdempotencyManager
    ):
        self.repository = repository
        self.event_publisher = event_publisher
        self.jwt_auth = jwt_auth
        self.idempotency_manager = idempotency_manager
    
    def create_claim(self, claim_data: ClaimCreate, customer_id: str) -> ClaimResponse:
        """Create a new claim with idempotency support."""
        # Check idempotency if key is provided
        if claim_data.idempotency_key:
            request_data = claim_data.dict(exclude={'idempotency_key'})
            cached_response = self.idempotency_manager.get_response(
                claim_data.idempotency_key, 
                request_data
            )
            if cached_response:
                self.logger.info("Returning cached response for idempotency key", 
                               key=claim_data.idempotency_key)
                return ClaimResponse(**cached_response)
        
        # Create claim in database
        claim = self.repository.create_claim(claim_data)
        
        # Publish event
        claim_dict = claim.dict()
        self.event_publisher.publish_claim_created(claim_dict)
        
        # Store in idempotency cache if key provided
        if claim_data.idempotency_key:
            request_data = claim_data.dict(exclude={'idempotency_key'})
            response_data = claim_dict
            self.idempotency_manager.put_if_absent(
                claim_data.idempotency_key,
                request_data,
                response_data
            )
        
        return ClaimResponse(**claim_dict)
    
    def get_claim(self, claim_id: str, customer_id: str) -> ClaimResponse:
        """Get a claim by ID."""
        claim = self.repository.get_claim(claim_id)
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim not found"
            )
        
        # Check if claim belongs to customer
        if claim.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return ClaimResponse(**claim.dict())
    
    def get_policy_claims(
        self, 
        policy_id: str, 
        customer_id: str,
        limit: int = 20, 
        next_token: Optional[str] = None
    ) -> ClaimListResponse:
        """Get claims for a policy."""
        claims, next_token = self.repository.get_policy_claims(
            policy_id, limit, next_token
        )
        
        # Filter claims by customer (in a real app, this would be done at DB level)
        customer_claims = [claim for claim in claims if claim.customer_id == customer_id]
        
        claim_responses = [ClaimResponse(**claim.dict()) for claim in customer_claims]
        
        return ClaimListResponse(
            claims=claim_responses,
            total=len(claim_responses),
            next_token=next_token
        )
    
    def update_claim(
        self, 
        claim_id: str, 
        update_data: ClaimUpdate, 
        customer_id: str
    ) -> ClaimResponse:
        """Update a claim."""
        # Check if claim exists and belongs to customer
        existing_claim = self.repository.get_claim(claim_id)
        if not existing_claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim not found"
            )
        
        if existing_claim.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Update claim
        updated_claim = self.repository.update_claim(claim_id, update_data)
        if not updated_claim:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update claim"
            )
        
        # Publish event
        updated_fields = list(update_data.dict(exclude_unset=True).keys())
        claim_dict = updated_claim.dict()
        self.event_publisher.publish_claim_updated(claim_dict, updated_fields)
        
        return ClaimResponse(**claim_dict)


# Dependency injection
def get_claim_service() -> ClaimService:
    """Get claim service instance."""
    # This would be injected via dependency injection in a real app
    from ...shared.config import get_settings
    from ...shared.aws import get_dynamodb_client
    from ..events.publisher import ClaimEventPublisher
    from ..auth.jwt_stub import JWTStub
    from ..idempotency.dynamodb import IdempotencyManager
    
    settings = get_settings()
    dynamodb = get_dynamodb_client(settings)
    repository = ClaimRepository(dynamodb, f"{settings.service_name}_claims")
    event_publisher = ClaimEventPublisher(settings)
    jwt_auth = JWTStub(settings)
    idempotency_manager = IdempotencyManager(dynamodb, f"{settings.service_name}_idem")
    
    return ClaimService(repository, event_publisher, jwt_auth, idempotency_manager)


def get_current_customer(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current customer from JWT token."""
    from ...shared.config import get_settings
    from ..auth.jwt_stub import JWTStub
    
    settings = get_settings()
    jwt_auth = JWTStub(settings)
    
    customer_id = jwt_auth.verify_token(credentials.credentials)
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    return customer_id


@router.post("/", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim(
    claim_data: ClaimCreate,
    customer_id: str = Depends(get_current_customer),
    service: ClaimService = Depends(get_claim_service)
):
    """Create a new claim."""
    try:
        return service.create_claim(claim_data, customer_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create claim: {str(e)}"
        )


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: str,
    customer_id: str = Depends(get_current_customer),
    service: ClaimService = Depends(get_claim_service)
):
    """Get a claim by ID."""
    return service.get_claim(claim_id, customer_id)


@router.get("/policy/{policy_id}", response_model=ClaimListResponse)
async def get_policy_claims(
    policy_id: str,
    customer_id: str = Depends(get_current_customer),
    limit: int = Query(20, ge=1, le=100),
    next_token: Optional[str] = Query(None),
    service: ClaimService = Depends(get_claim_service)
):
    """Get claims for a policy."""
    return service.get_policy_claims(policy_id, customer_id, limit, next_token)


@router.put("/{claim_id}", response_model=ClaimResponse)
async def update_claim(
    claim_id: str,
    update_data: ClaimUpdate,
    customer_id: str = Depends(get_current_customer),
    service: ClaimService = Depends(get_claim_service)
):
    """Update a claim."""
    return service.update_claim(claim_id, update_data, customer_id)
