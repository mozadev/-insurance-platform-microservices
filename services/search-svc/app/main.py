"""Search service main application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from ...shared.config import get_settings
from ...shared.logging import configure_logging, get_logger
from .routers.search import router as search_router


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

    # Initialize OpenSearch indices
    try:
        from ...shared.aws import get_opensearch_client
        from .repositories.opensearch import SearchRepository

        opensearch_client = get_opensearch_client(settings)
        repository = SearchRepository(
            opensearch_client, settings.opensearch_index_prefix
        )
        repository.create_indices()

        logger.info("OpenSearch indices initialized")
    except Exception as e:
        logger.error("Failed to initialize OpenSearch indices", error=str(e))

    logger.info("Search service starting up", service_name=settings.service_name)

    yield

    # Shutdown
    logger.info("Search service shutting down")


# Create FastAPI app
app = FastAPI(
    title="Search Service",
    description="Search microservice with OpenSearch",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "search-svc"}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # Check dependencies (OpenSearch)
    try:
        settings = get_settings()
        from ...shared.aws import get_opensearch_client

        # Test OpenSearch connection
        opensearch_client = get_opensearch_client(settings)
        opensearch_client.cluster.health()

        return {"status": "ready", "service": "search-svc"}
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Service not ready: {str(e)}"
        ) from e


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.service_port, reload=True)
