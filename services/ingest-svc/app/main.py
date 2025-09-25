"""Ingest service main application with background SQS worker."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ...shared.config import get_settings
from ...shared.logging import configure_logging, get_logger
from .worker import IngestWorker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: start and stop background workers."""
    settings = get_settings()
    configure_logging(settings.service_name, settings.log_level)
    logger = get_logger(__name__)

    logger.info("Ingest service starting up", service_name=settings.service_name)

    # Start background worker
    worker = IngestWorker()
    app.state.worker = worker
    worker_task = asyncio.create_task(worker.run())

    try:
        yield
    finally:
        await worker.stop()
        await worker_task
        logger.info("Ingest service shutting down")


app = FastAPI(
    title="Ingest Service",
    description="Event ingestion and indexing service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ingest-svc"}


@app.get("/ready")
async def readiness_check():
    try:
        # Basic check: ensure worker is running
        if not getattr(app.state, "worker", None):
            raise RuntimeError("Worker not initialized")
        return {"status": "ready", "service": "ingest-svc"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}") from e


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.service_port, reload=True)
