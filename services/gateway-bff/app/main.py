"""Gateway BFF main application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from slowapi.errors import RateLimitExceeded

from ...shared.config import get_settings
from ...shared.logging import configure_logging, get_logger
from .middleware.rate_limiter import (
    create_rate_limit_exception_handler,
    create_rate_limiter,
)
from .routers.api import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    settings = get_settings()
    configure_logging(settings.service_name, settings.log_level)
    logger = get_logger(__name__)

    # Configure OpenTelemetry
    if settings.otel_exporter_otlp_endpoint:
        resource = Resource.create(
            {
                "service.name": settings.otel_service_name,
                "service.version": "1.0.0",
            }
        )

        trace.set_tracer_provider(TracerProvider(resource=resource))
        tracer = trace.get_tracer_provider()

        otlp_exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer.add_span_processor(span_processor)

    logger.info("Gateway BFF starting up", service_name=settings.service_name)

    yield

    # Shutdown
    logger.info("Gateway BFF shutting down")


# Create FastAPI app
app = FastAPI(
    title="Insurance Platform Gateway",
    description="API Gateway BFF for Insurance Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure rate limiting
settings = get_settings()
limiter = create_rate_limiter(settings.redis_url)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, create_rate_limit_exception_handler())

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "gateway-bff"}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # Check dependencies (other services)
    try:
        settings = get_settings()
        from ..clients.service_client import ResilientServiceClient

        # Test service connections
        policy_client = ResilientServiceClient(settings.policy_svc_url)
        claim_client = ResilientServiceClient(settings.claim_svc_url)
        search_client = ResilientServiceClient(settings.search_svc_url)

        # Quick health checks
        await policy_client.get("/health")
        await claim_client.get("/health")
        await search_client.get("/health")

        await policy_client.close()
        await claim_client.close()
        await search_client.close()

        return {"status": "ready", "service": "gateway-bff"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}") from e


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.service_port, reload=True)
