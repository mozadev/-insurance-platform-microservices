"""Auth service main application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ...shared.config import get_settings
from ...shared.logging import configure_logging, get_logger
from .routers.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    settings = get_settings()
    configure_logging(settings.service_name, settings.log_level)
    logger = get_logger(__name__)
    
    logger.info("Auth service starting up", service_name=settings.service_name)
    yield
    logger.info("Auth service shutting down")


app = FastAPI(
    title="Auth Service",
    description="Authentication service stub",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "auth-svc"}


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.service_port, reload=True)
