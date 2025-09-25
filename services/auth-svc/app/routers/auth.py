"""Auth API routes."""

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status
from jose import JWTError, jwt

from ...shared.config import get_settings
from ...shared.logging import LoggerMixin
from ..models import TokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthService(LoggerMixin):
    """Auth service business logic."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def create_token(self, customer_id: str) -> str:
        """Create JWT token."""
        expire = datetime.utcnow() + timedelta(hours=self.settings.jwt_expiration_hours)
        
        to_encode = {
            "sub": customer_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(to_encode, self.settings.jwt_secret_key, algorithm=self.settings.jwt_algorithm)
    
    def authenticate_user(self, username: str, password: str) -> str:
        """Authenticate user and return customer ID."""
        # Simple stub authentication for demo
        if username == "demo" and password == "demo":
            return "CUST-DEMO01"
        elif username == "test" and password == "test":
            return "CUST-TEST01"
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )


@router.post("/token", response_model=TokenResponse)
async def create_access_token(request: TokenRequest):
    """Create access token."""
    try:
        service = AuthService()
        customer_id = service.authenticate_user(request.username, request.password)
        access_token = service.create_token(customer_id)
        
        return TokenResponse(
            access_token=access_token,
            expires_in=service.settings.jwt_expiration_hours * 3600,
            customer_id=customer_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )
