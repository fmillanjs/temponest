"""
Auth Service - JWT and API Key Authentication
FastAPI application for authentication and authorization.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import html
from app.settings import settings
from app.database import db
from app.limiter import limiter
from app.routers import auth, api_keys

# Import shared Redis client
import sys
sys.path.append('/app/../..')
from shared.redis import RedisCache

# Global Redis cache instance
cache: RedisCache = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    global cache
    print("🔐 Starting Auth Service...")

    # Connect to database
    await db.connect()

    # Connect to Redis
    cache = RedisCache(url=settings.REDIS_URL)
    try:
        await cache.connect()
        print(f"✅ Connected to Redis at {settings.REDIS_URL}")
    except Exception as e:
        print(f"⚠️  Failed to connect to Redis: {e}. Caching will be disabled.")
        cache = None

    yield

    # Cleanup
    await db.disconnect()
    if cache:
        await cache.close()

# Create FastAPI app
app = FastAPI(
    title="Agentic Company - Auth Service",
    description="Authentication and authorization service with JWT and API keys",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter

# Add rate limit exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Custom validation error handler to prevent XSS
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom validation error handler that escapes user input to prevent XSS.
    This addresses OWASP A03:2021 (Injection) and A07:2021 (XSS).
    """
    errors = []
    for error in exc.errors():
        # Escape the input value if it's a string to prevent XSS
        error_dict = error.copy()
        if "input" in error_dict and isinstance(error_dict["input"], str):
            error_dict["input"] = html.escape(error_dict["input"])
        errors.append(error_dict)

    return JSONResponse(
        status_code=422,
        content={"detail": errors}
    )


# CORS middleware
# Security: Use explicit origins, not wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Parse from environment variable
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],  # Explicit methods
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],  # Explicit headers
    max_age=600,  # Cache preflight requests for 10 minutes
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    print(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check (no rate limit for monitoring)
@app.get("/health")
@limiter.exempt
async def health_check():
    """
    Health check endpoint with Redis caching.

    Cache Key: health:auth
    TTL: 10 seconds
    """
    cache_key = "health:auth"

    # Try to get from cache
    if cache:
        try:
            cached_health = await cache.get(cache_key)
            if cached_health:
                return cached_health
        except Exception as e:
            print(f"Health check cache read error: {e}")

    # Cache miss - check health
    health_status = {
        "status": "healthy",
        "service": "auth",
        "database": "connected" if db.pool else "disconnected",
        "cache": "connected" if cache else "disconnected"
    }

    # Cache for 10 seconds
    if cache:
        try:
            await cache.set(cache_key, health_status, ttl=10)
        except Exception as e:
            print(f"Health check cache write error: {e}")

    return health_status


# Include routers
app.include_router(auth.router)
app.include_router(api_keys.router)

# Prometheus metrics
from prometheus_client import make_asgi_app

# Mount prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9002)
