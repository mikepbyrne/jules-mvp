"""
Correlation ID middleware for request tracing.

Adds unique correlation ID to every request for cross-service tracing.
"""
import uuid
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

# Thread-safe context variable for correlation ID
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')

logger = logging.getLogger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation ID to requests and responses."""

    async def dispatch(self, request: Request, call_next):
        """Add correlation ID to request context."""

        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))

        # Set in context variable (accessible throughout request)
        correlation_id_var.set(correlation_id)

        # Log request start
        logger.info("request_start",
                   correlation_id=correlation_id,
                   method=request.method,
                   path=request.url.path,
                   client=request.client.host if request.client else None)

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers['X-Correlation-ID'] = correlation_id

        # Log request completion
        logger.info("request_complete",
                   correlation_id=correlation_id,
                   status_code=response.status_code)

        return response


def get_correlation_id() -> str:
    """Get current correlation ID from context."""
    return correlation_id_var.get()


class CorrelationIDFilter(logging.Filter):
    """Logging filter to add correlation ID to all log records."""

    def filter(self, record):
        """Add correlation_id to log record."""
        record.correlation_id = get_correlation_id()
        return True


# Configure logging to include correlation ID
def configure_correlation_logging():
    """Configure logging format to include correlation ID."""

    # Add filter to root logger
    logging.root.addFilter(CorrelationIDFilter())

    # Update formatter to include correlation_id
    formatter = logging.Formatter(
        '{"timestamp":"%(asctime)s","level":"%(levelname)s","correlation_id":"%(correlation_id)s",'
        '"logger":"%(name)s","message":"%(message)s","extra":%(extra)s}',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )

    # Apply to all handlers
    for handler in logging.root.handlers:
        handler.setFormatter(formatter)
