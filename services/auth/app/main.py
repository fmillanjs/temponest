"""
Auth Service - JWT and API Key Authentication
FastAPI application for authentication and authorization.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.settings import settings
from app.database import db
from app.routers import auth, api_keys


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    print("🔐 Starting Auth Service...")

    # Connect to database
    await db.connect()

    yield

    # Cleanup
    await db.disconnect()


# Create FastAPI app
app = FastAPI(
    title="Agentic Company - Auth Service",
    description="Authentication and authorization service with JWT and API keys",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth",
        "database": "connected" if db.pool else "disconnected"
    }


# Include routers
app.include_router(auth.router)
app.include_router(api_keys.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9002)
