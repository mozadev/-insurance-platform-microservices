"""Policy API routes."""


from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...shared.logging import LoggerMixin
from ..auth.jwt_stub import JWTStub
from ..models import (
    PolicyCreate,
    PolicyListResponse,
    PolicyResponse,
    PolicyUpdate,
)
from ..repositories.dynamodb import PolicyRepository

router = APIRouter(prefix="/policies", tags=["policies"])
security = HTTPBearer()


class PolicyService(LoggerMixin):
    """Policy service business logic."""

    def __init__(
        self, repository: PolicyRepository, event_publisher, jwt_auth: JWTStub
    ):
        self.repository = repository
        self.event_publisher = event_publisher
        self.jwt_auth = jwt_auth

    def create_policy(
        self, policy_data: PolicyCreate, customer_id: str
    ) -> PolicyResponse:
        """Create a new policy."""
        # Create policy in database
        policy = self.repository.create_policy(policy_data)

        # Publish event
        policy_dict = policy.dict()
        self.event_publisher.publish_policy_created(policy_dict)

        return PolicyResponse(**policy_dict)

    def get_policy(self, policy_id: str, customer_id: str) -> PolicyResponse:
        """Get a policy by ID."""
        policy = self.repository.get_policy(policy_id)
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found"
            )

        # Check if policy belongs to customer
        if policy.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        return PolicyResponse(**policy.dict())

    def get_customer_policies(
        self, customer_id: str, limit: int = 20, next_token: str | None = None
    ) -> PolicyListResponse:
        """Get policies for a customer."""
        policies, next_token = self.repository.get_customer_policies(
            customer_id, limit, next_token
        )

        policy_responses = [PolicyResponse(**policy.dict()) for policy in policies]

        return PolicyListResponse(
            policies=policy_responses,
            total=len(policy_responses),
            next_token=next_token,
        )

    def update_policy(
        self, policy_id: str, update_data: PolicyUpdate, customer_id: str
    ) -> PolicyResponse:
        """Update a policy."""
        # Check if policy exists and belongs to customer
        existing_policy = self.repository.get_policy(policy_id)
        if not existing_policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found"
            )

        if existing_policy.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        # Update policy
        updated_policy = self.repository.update_policy(policy_id, update_data)
        if not updated_policy:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update policy",
            )

        # Publish event
        updated_fields = list(update_data.dict(exclude_unset=True).keys())
        policy_dict = updated_policy.dict()
        self.event_publisher.publish_policy_updated(policy_dict, updated_fields)

        return PolicyResponse(**policy_dict)


# Dependency injection
def get_policy_service() -> PolicyService:
    """Get policy service instance."""
    # This would be injected via dependency injection in a real app
    from ...shared.aws import get_dynamodb_client
    from ...shared.config import get_settings
    from ..auth.jwt_stub import JWTStub
    from ..events.publisher import PolicyEventPublisher

    settings = get_settings()
    dynamodb = get_dynamodb_client(settings)
    repository = PolicyRepository(dynamodb, f"{settings.service_name}_policies")
    event_publisher = PolicyEventPublisher(settings)
    jwt_auth = JWTStub(settings)

    return PolicyService(repository, event_publisher, jwt_auth)


def get_current_customer(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Get current customer from JWT token."""
    from ...shared.config import get_settings
    from ..auth.jwt_stub import JWTStub

    settings = get_settings()
    jwt_auth = JWTStub(settings)

    customer_id = jwt_auth.verify_token(credentials.credentials)
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    return customer_id


@router.post("/", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy_data: PolicyCreate,
    customer_id: str = Depends(get_current_customer),
    service: PolicyService = Depends(get_policy_service),
):
    """Create a new policy."""
    try:
        return service.create_policy(policy_data, customer_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create policy: {str(e)}",
        ) from e


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: str,
    customer_id: str = Depends(get_current_customer),
    service: PolicyService = Depends(get_policy_service),
):
    """Get a policy by ID."""
    return service.get_policy(policy_id, customer_id)


@router.get("/", response_model=PolicyListResponse)
async def get_customer_policies(
    customer_id: str = Depends(get_current_customer),
    limit: int = Query(20, ge=1, le=100),
    next_token: str | None = Query(None),
    service: PolicyService = Depends(get_policy_service),
):
    """Get policies for the current customer."""
    return service.get_customer_policies(customer_id, limit, next_token)


@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: str,
    update_data: PolicyUpdate,
    customer_id: str = Depends(get_current_customer),
    service: PolicyService = Depends(get_policy_service),
):
    """Update a policy."""
    return service.update_policy(policy_id, update_data, customer_id)
