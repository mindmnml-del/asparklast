"""
AISpark Studio - FastAPI Application
Modular backend with domain-specific routers and unified services.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from services.unified_ai_service import ai_service
from services.cache_service import cache as cache_service
from utils.health_check import get_quick_health

# Routers
from api.routers.auth_router import router as auth_router
from api.routers.generation_router import router as generation_router
from api.routers.prompts_router import router as prompts_router
from api.routers.characters_router import router as characters_router
from api.routers.helios_router import router as helios_router
from api.routers.critic_router import router as critic_router
from api.routers.search_router import router as search_router

# V1/V2 B2B routers
from api.v1.sandbox_router import router as sandbox_router
from api.v2.admin_router import router as admin_router
from api.v2.b2b_router import router as b2b_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if not settings.debug_mode:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Attach a correlation ID and log every request/response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    logger.info("AISpark Studio starting...")

    try:
        from alembic.config import Config as AlembicConfig
        from alembic import command as alembic_command
        alembic_cfg = AlembicConfig("alembic.ini")
        alembic_command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations applied")

        await cache_service.initialize()

        if ai_service.ensure_ready():
            logger.info("AI Service ready")

        logger.info("AISpark Studio ready!")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield
    await cache_service.close()
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="AISpark Studio API",
    version="2.0.0",
    lifespan=lifespan,
)

_cors_origins = [
    origin.strip()
    for origin in settings.allowed_origins.split(",")
    if origin.strip()
]

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

# Register domain routers
app.include_router(auth_router)
app.include_router(generation_router)
app.include_router(prompts_router)
app.include_router(characters_router)
app.include_router(helios_router)
app.include_router(critic_router)
app.include_router(search_router)

# Register B2B routers
app.include_router(sandbox_router, prefix="/v1/sandbox", tags=["B2B Sandbox"])
app.include_router(admin_router, prefix="/v2/admin", tags=["B2B Admin"])
app.include_router(b2b_router, prefix="/v2/b2b", tags=["B2B Core"])


# Core system endpoints
@app.get("/")
def root():
    return {"message": "AISpark Studio API v2.0", "docs": "/docs"}


@app.get("/health")
def health():
    return get_quick_health()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
