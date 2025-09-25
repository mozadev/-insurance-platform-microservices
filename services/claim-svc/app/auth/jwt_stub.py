"""JWT authentication stub for local development."""

from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from ...shared.config import Settings
from ...shared.logging import LoggerMixin


class JWTStub(LoggerMixin):
    """JWT authentication stub for local development."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.expiration_hours = settings.jwt_expiration_hours
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_access_token(
        self, subject: str, expires_delta: timedelta | None = None
    ) -> str:
        """Create JWT access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=self.expiration_hours)

        to_encode = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> str | None:
        """Verify JWT token and return subject."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            subject: str = payload.get("sub")
            if subject is None:
                return None
            return subject
        except JWTError:
            return None

    def create_test_token(self, customer_id: str = "CUST-TEST01") -> str:
        """Create a test token for local development."""
        return self.create_access_token(customer_id)

    def hash_password(self, password: str) -> str:
        """Hash password for storage."""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
