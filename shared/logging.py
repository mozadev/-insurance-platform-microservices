"""Structured logging configuration for microservices."""

import logging
import sys

import structlog
from opentelemetry import trace


def configure_logging(service_name: str, log_level: str = "INFO") -> None:
    """Configure structured logging with OpenTelemetry integration."""

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def add_trace_context(logger: structlog.BoundLogger) -> structlog.BoundLogger:
    """Add OpenTelemetry trace context to logger."""
    span = trace.get_current_span()
    if span and span.is_recording():
        trace_id = format(span.get_span_context().trace_id, "032x")
        span_id = format(span.get_span_context().span_id, "016x")
        return logger.bind(trace_id=trace_id, span_id=span_id)
    return logger


class LoggerMixin:
    """Mixin class to add structured logging to any class."""

    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger instance for this class."""
        logger = get_logger(self.__class__.__name__)
        return add_trace_context(logger)
