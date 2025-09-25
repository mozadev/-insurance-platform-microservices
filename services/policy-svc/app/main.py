"""Policy service main application."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

from ...shared.config import get_settings
from ...shared.logging import configure_logging, get_logger
from .routers.policies import router as policies_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    settings = get_settings()
    configure_logging(settings.service_name, settings.log_level)
    logger = get_logger(__name__)
    
    # Configure OpenTelemetry
    if settings.otel_exporter_otlp_endpoint:
        resource = Resource.create({
            "service.name": settings.otel_service_name,
            "service.version": "1.0.0",
        })
        
        trace.set_tracer_provider(TracerProvider(resource=resource))
        tracer = trace.get_tracer_provider()
        
        otlp_exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer.add_span_processor(span_processor)
    
    logger.info("Policy service starting up", service_name=settings.service_name)
    
    yield
    
    # Shutdown
    logger.info("Policy service shutting down")


# Create FastAPI app
app = FastAPI(
    title="Policy Service",
    description="Policy management microservice",
    version="1.0.0",
    lifespan=lifespan
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
app.include_router(policies_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "policy-svc"}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # Check dependencies (DynamoDB, SNS, etc.)
    try:
        settings = get_settings()
        from ...shared.aws import get_dynamodb_client, get_sns_client
        
        # Test DynamoDB connection
        dynamodb = get_dynamodb_client(settings)
        dynamodb.describe_table(TableName=f"{settings.service_name}_policies")
        
        # Test SNS connection
        sns = get_sns_client(settings)
        sns.get_topic_attributes(TopicArn=settings.policies_topic_arn)
        
        return {"status": "ready", "service": "policy-svc"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}") from e


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=True
    )
