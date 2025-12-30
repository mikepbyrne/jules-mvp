"""Main FastAPI application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from src.api import webhooks
from src.config import get_settings
from src.core.database import engine
from src.core.logging import get_logger
from src.core.redis import get_redis_client

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan events.

    Handles startup and shutdown operations:
    - Initialize connections (Redis, database)
    - Setup monitoring
    - Cleanup on shutdown
    """
    # Startup
    logger.info(
        "Starting Jules backend",
        extra={
            "environment": settings.environment,
            "debug": settings.debug,
            "log_level": settings.log_level,
        },
    )

    # Initialize Sentry if configured
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=1.0 if settings.is_development else 0.1,
            profiles_sample_rate=1.0 if settings.is_development else 0.1,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
        )
        logger.info("Sentry monitoring initialized")

    # Initialize and test Redis connection
    try:
        redis_client = get_redis_client()
        await redis_client.connect()  # FIX: Explicitly connect
        await redis_client.client.ping()  # FIX: Use client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}", exc_info=True)
        # Continue anyway - Redis is used for caching, not critical

    # Test database connection
    try:
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database connection failed: {e}", exc_info=True)
        raise  # Database is critical

    yield

    # Shutdown
    logger.info("Shutting down Jules backend")

    # Close Redis connection
    try:
        redis_client = get_redis_client()
        await redis_client.disconnect()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Redis cleanup failed: {e}", exc_info=True)

    # Close database connections
    await engine.dispose()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="Jules Backend API",
    description="SMS-based AI life companion backend service",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Trusted host middleware (prevent host header attacks)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_origins,
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all HTTP requests."""
    import time

    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Log request
    process_time = (time.time() - start_time) * 1000
    logger.info(
        f"{request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": int(process_time),
            "client_host": request.client.host if request.client else None,
        },
    )

    # Add timing header
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

    return response


# Include routers
app.include_router(webhooks.router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Jules Backend API",
        "version": "0.1.0",
        "status": "operational",
        "environment": settings.environment,
    }


# Health check
@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    health_status = {
        "status": "healthy",
        "service": "jules-backend",
        "version": "0.1.0",
        "environment": settings.environment,
        "checks": {},
    }

    # Check database
    try:
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check Redis
    try:
        redis_client = get_redis_client()
        await redis_client.client.ping()  # FIX: Use client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        # Redis failure doesn't make service unhealthy, just degraded
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"

    return health_status


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
