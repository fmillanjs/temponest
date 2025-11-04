"""
Scheduler Service - FastAPI application
Manages scheduled task execution for the agentic platform
"""
from contextlib import asynccontextmanager
from typing import Optional
import httpx

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from settings import settings
from db import DatabaseManager
from scheduler import TaskScheduler
from models import SchedulerHealthResponse
from routers import schedules


# Global state
db_manager: Optional[DatabaseManager] = None
task_scheduler: Optional[TaskScheduler] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    global db_manager, task_scheduler

    # Startup
    print("🚀 Starting Scheduler Service...")

    # Initialize database
    db_manager = DatabaseManager()
    await db_manager.connect()

    # Initialize and start scheduler
    task_scheduler = TaskScheduler(db_manager)
    await task_scheduler.start()

    print("✅ Scheduler Service ready")

    yield

    # Shutdown
    print("🛑 Shutting down Scheduler Service...")

    # Stop scheduler
    if task_scheduler:
        await task_scheduler.stop()

    # Close database connection
    if db_manager:
        await db_manager.disconnect()

    print("✅ Scheduler Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Scheduler Service",
    description="Scheduled task execution service for agentic platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
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


# Include routers
app.include_router(schedules.router)

# Prometheus metrics
from prometheus_client import make_asgi_app
from metrics import MetricsRecorder, service_info

# Initialize service info
service_info.info({
    'version': '1.0.0',
    'service': 'scheduler-service',
    'environment': 'production'
})

# Mount prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Health check endpoint
@app.get("/health", response_model=SchedulerHealthResponse)
async def health_check():
    """Health check endpoint"""

    # Check database
    db_connected = False
    if db_manager and db_manager.pool:
        try:
            async with db_manager.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                db_connected = True
        except Exception as e:
            print(f"Database health check failed: {e}")

    # Check scheduler
    scheduler_running = task_scheduler.is_running() if task_scheduler else False
    active_jobs = task_scheduler.get_active_jobs_count() if task_scheduler else 0

    # Check agent service
    agent_service_available = False
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.agent_service_url}/health",
                timeout=5.0
            )
            agent_service_available = response.status_code == 200
    except Exception as e:
        print(f"Agent service health check failed: {e}")

    # Overall status
    status = "healthy" if (db_connected and scheduler_running and agent_service_available) else "unhealthy"

    # Update Prometheus metrics
    MetricsRecorder.update_scheduler_health(scheduler_running)
    MetricsRecorder.update_active_jobs(active_jobs)
    MetricsRecorder.update_agent_service_health(agent_service_available)

    return SchedulerHealthResponse(
        status=status,
        scheduler_running=scheduler_running,
        active_jobs=active_jobs,
        database_connected=db_connected,
        agent_service_available=agent_service_available
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Scheduler Service",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9003,
        reload=True
    )
