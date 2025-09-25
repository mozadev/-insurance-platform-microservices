"""Main API router for gateway BFF."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...shared.logging import LoggerMixin
from ..clients.service_client import ResilientServiceClient

router = APIRouter(prefix="/api", tags=["api"])
security = HTTPBearer()


class GatewayService(LoggerMixin):
    """Gateway service for API composition."""

    def __init__(
        self,
        policy_client: ResilientServiceClient,
        claim_client: ResilientServiceClient,
        search_client: ResilientServiceClient,
    ):
        self.policy_client = policy_client
        self.claim_client = claim_client
        self.search_client = search_client

    async def get_customer_dashboard(self, customer_id: str) -> dict[str, Any]:
        """Get customer dashboard data."""
        try:
            # Get customer policies
            policies_response = await self.policy_client._make_request_with_retry(
                "GET", f"/customers/{customer_id}/policies"
            )

            # Get recent claims
            claims_response = (
                await self.claim_client._make_request_with_retry(
                    "GET",
                    f"/claims/policy/{policies_response['policies'][0]['policyId']}",
                )
                if policies_response["policies"]
                else {"claims": []}
            )

            return {
                "customer_id": customer_id,
                "policies": policies_response.get("policies", []),
                "recent_claims": claims_response.get("claims", [])[:5],  # Last 5 claims
                "summary": {
                    "total_policies": len(policies_response.get("policies", [])),
                    "active_policies": len(
                        [
                            p
                            for p in policies_response.get("policies", [])
                            if p.get("status") == "active"
                        ]
                    ),
                    "total_claims": len(claims_response.get("claims", [])),
                    "open_claims": len(
                        [
                            c
                            for c in claims_response.get("claims", [])
                            if c.get("status") == "open"
                        ]
                    ),
                },
            }
        except Exception as e:
            self.logger.error(
                "Failed to get customer dashboard",
                error=str(e),
                customer_id=customer_id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get dashboard: {str(e)}",
            ) from e

    async def search_all(self, query: str, customer_id: str) -> dict[str, Any]:
        """Search across all services."""
        try:
            # Search in search service
            search_response = await self.search_client._make_request_with_retry(
                "GET", f"/search/?q={query}"
            )

            return {
                "query": query,
                "results": search_response.get("results", []),
                "total": search_response.get("total", 0),
                "took": search_response.get("took", 0),
            }
        except Exception as e:
            self.logger.error("Search failed", error=str(e), query=query)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Search failed: {str(e)}",
            ) from e


# Dependency injection
def get_gateway_service() -> GatewayService:
    """Get gateway service instance."""
    from ...shared.config import get_settings

    settings = get_settings()

    policy_client = ResilientServiceClient(settings.policy_svc_url)
    claim_client = ResilientServiceClient(settings.claim_svc_url)
    search_client = ResilientServiceClient(settings.search_svc_url)

    return GatewayService(policy_client, claim_client, search_client)


def get_current_customer(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Get current customer from JWT token."""
    # Simple token validation for demo purposes
    if not credentials.credentials or credentials.credentials != "demo-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    return "CUST-DEMO01"  # Demo customer ID


@router.get("/dashboard")
async def get_dashboard(
    customer_id: str = Depends(get_current_customer),
    service: GatewayService = Depends(get_gateway_service),
):
    """Get customer dashboard."""
    return await service.get_customer_dashboard(customer_id)


@router.get("/search")
async def search(
    q: str,
    customer_id: str = Depends(get_current_customer),
    service: GatewayService = Depends(get_gateway_service),
):
    """Search across all services."""
    return await service.search_all(q, customer_id)


# Policy endpoints
@router.get("/policies")
async def get_policies(
    customer_id: str = Depends(get_current_customer),
    service: GatewayService = Depends(get_gateway_service),
):
    """Get customer policies."""
    policy_client = service.policy_client
    return await policy_client._make_request_with_retry(
        "GET", f"/customers/{customer_id}/policies"
    )


@router.get("/policies/{policy_id}")
async def get_policy(
    policy_id: str,
    customer_id: str = Depends(get_current_customer),
    service: GatewayService = Depends(get_gateway_service),
):
    """Get specific policy."""
    policy_client = service.policy_client
    return await policy_client._make_request_with_retry("GET", f"/policies/{policy_id}")


# Claim endpoints
@router.get("/claims")
async def get_claims(
    customer_id: str = Depends(get_current_customer),
    service: GatewayService = Depends(get_gateway_service),
):
    """Get customer claims."""
    _ = service.claim_client
    # This would need to be implemented in claim service
    return {"claims": [], "total": 0}


@router.get("/claims/{claim_id}")
async def get_claim(
    claim_id: str,
    customer_id: str = Depends(get_current_customer),
    service: GatewayService = Depends(get_gateway_service),
):
    """Get specific claim."""
    claim_client = service.claim_client
    return await claim_client._make_request_with_retry("GET", f"/claims/{claim_id}")


@router.post("/claims")
async def create_claim(
    claim_data: dict[str, Any],
    customer_id: str = Depends(get_current_customer),
    service: GatewayService = Depends(get_gateway_service),
):
    """Create new claim."""
    claim_client = service.claim_client
    return await claim_client._make_request_with_retry(
        "POST", "/claims", data=claim_data
    )
