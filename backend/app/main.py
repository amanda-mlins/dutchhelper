"""Main FastAPI application"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.routes import router
from app.auth_routes import auth_router
from app.config import settings
from app.database import check_db
from app.limiter import limiter  # shared limiter instance

# ---------------------------------------------------------------------------
# Rate limiting (slowapi) — limiter instance defined in app/limiter.py
# to avoid circular imports between this module and auth_routes.py
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown tasks
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("DutchHelper API starting up")
    yield
    # Gracefully close the singleton httpx client used by the LLM service
    try:
        from app.llm_service import OpenRouterService
        if OpenRouterService._client and not OpenRouterService._client.is_closed:
            await OpenRouterService._client.aclose()
            logger.info("OpenRouter httpx client closed")
    except Exception as e:
        logger.warning(f"Could not close OpenRouter client: {e}")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="DutchHelper API",
    description="API for Dutch language learning assistance with grammatical analysis",
    version="1.0.0",
    lifespan=lifespan,
    # Hide interactive docs in production — enable only when DEBUG=True
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# Attach the rate limiter state and error handler to the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

# When running behind a reverse proxy (Nginx, Caddy, cloud LB) this makes
# FastAPI trust X-Forwarded-Proto so that request.url.scheme == "https" and
# the Secure flag on cookies works correctly.
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # Narrow this to your domain once it's known
    )

# uvicorn must be started with --proxy-headers in production so that
# X-Forwarded-* headers are forwarded from the reverse proxy.

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
app.include_router(router)
app.include_router(auth_router)

# ---------------------------------------------------------------------------
# Root + health
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("Root endpoint called")
    return {
        "message": "Welcome to DutchHelper API",
        "version": "1.0.0",
    }

@app.get("/health")
def health():
    """
    Health check endpoint.
    Returns 200 only when the database is reachable.
    Load balancers and container orchestrators use this to gate traffic.
    """
    db_ok = check_db()
    if not db_ok:
        return {"status": "degraded", "database": "unreachable"}, 503
    return {"status": "healthy", "database": "ok"}
