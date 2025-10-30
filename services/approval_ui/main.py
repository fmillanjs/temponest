"""
Approval UI - Web interface for human approvals.

Features:
- View pending approval requests
- Approve/deny tasks with reason
- View approval history
- Send signals back to Temporal workflows
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncpg
from temporalio.client import Client as TemporalClient


# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/approvals")
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "temporal:7233")
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-approval-key")


# Models
class ApprovalRequest(BaseModel):
    workflow_id: str
    run_id: str
    task_description: str
    risk_level: str
    context: dict = {}


class ApprovalResponse(BaseModel):
    approval_id: str
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


# Global state
db_pool: Optional[asyncpg.Pool] = None
temporal_client: Optional[TemporalClient] = None
templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    global db_pool, temporal_client

    # Startup
    print("🚀 Starting Approval UI...")

    # Connect to database
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    print("✅ Connected to database")

    # Connect to Temporal
    temporal_client = await TemporalClient.connect(TEMPORAL_HOST)
    print("✅ Connected to Temporal")

    yield

    # Shutdown
    print("🛑 Shutting down Approval UI...")
    if db_pool:
        await db_pool.close()


app = FastAPI(
    title="Approval UI",
    description="Web interface for human-in-the-loop approvals",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "database": "connected" if db_pool else "disconnected",
        "temporal": "connected" if temporal_client else "disconnected"
    }


@app.post("/api/approvals", response_model=ApprovalResponse)
async def create_approval(request: ApprovalRequest):
    """Create a new approval request"""

    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    approval_id = str(uuid.uuid4())

    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO approval_requests
            (id, workflow_id, run_id, task_description, risk_level, context, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            approval_id,
            request.workflow_id,
            request.run_id,
            request.task_description,
            request.risk_level,
            request.context,
            "pending"
        )

    return ApprovalResponse(
        approval_id=approval_id,
        status="pending"
    )


@app.get("/api/approvals/{approval_id}", response_model=ApprovalResponse)
async def get_approval(approval_id: str):
    """Get approval status"""

    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, status, approved_by, approved_at
            FROM approval_requests
            WHERE id = $1
            """,
            approval_id
        )

    if not row:
        raise HTTPException(status_code=404, detail="Approval not found")

    return ApprovalResponse(
        approval_id=row["id"],
        status=row["status"],
        approved_by=row["approved_by"],
        approved_at=row["approved_at"]
    )


@app.get("/api/approvals", response_model=List[dict])
async def list_approvals(status: Optional[str] = None):
    """List all approval requests, optionally filtered by status"""

    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    async with db_pool.acquire() as conn:
        if status:
            rows = await conn.fetch(
                """
                SELECT id, workflow_id, task_description, risk_level, status,
                       approved_by, created_at, approved_at
                FROM approval_requests
                WHERE status = $1
                ORDER BY created_at DESC
                LIMIT 100
                """,
                status
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, workflow_id, task_description, risk_level, status,
                       approved_by, created_at, approved_at
                FROM approval_requests
                ORDER BY created_at DESC
                LIMIT 100
                """
            )

    return [dict(row) for row in rows]


@app.post("/api/approvals/{approval_id}/approve")
async def approve_task(approval_id: str, approver: str = Form(...), reason: str = Form("")):
    """Approve a task and send signal to Temporal workflow"""

    if not db_pool or not temporal_client:
        raise HTTPException(status_code=503, detail="Service not available")

    # Get approval request
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT workflow_id, run_id, status
            FROM approval_requests
            WHERE id = $1
            """,
            approval_id
        )

    if not row:
        raise HTTPException(status_code=404, detail="Approval not found")

    if row["status"] != "pending":
        raise HTTPException(status_code=400, detail="Approval already processed")

    # Update database
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE approval_requests
            SET status = 'approved', approved_by = $1, approved_at = NOW()
            WHERE id = $2
            """,
            approver,
            approval_id
        )

        # Log in audit table
        await conn.execute(
            """
            INSERT INTO audit_log (approval_id, action, actor, details)
            VALUES ($1, 'approve', $2, $3)
            """,
            approval_id,
            approver,
            {"reason": reason}
        )

    # Send signal to Temporal workflow
    workflow_handle = temporal_client.get_workflow_handle(
        workflow_id=row["workflow_id"],
        run_id=row["run_id"]
    )

    await workflow_handle.signal(
        "approval_signal",
        {
            "status": "approved",
            "approver": approver,
            "reason": reason
        }
    )

    return {"status": "approved", "approval_id": approval_id}


@app.post("/api/approvals/{approval_id}/deny")
async def deny_task(approval_id: str, approver: str = Form(...), reason: str = Form(...)):
    """Deny a task and send signal to Temporal workflow"""

    if not db_pool or not temporal_client:
        raise HTTPException(status_code=503, detail="Service not available")

    # Get approval request
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT workflow_id, run_id, status
            FROM approval_requests
            WHERE id = $1
            """,
            approval_id
        )

    if not row:
        raise HTTPException(status_code=404, detail="Approval not found")

    if row["status"] != "pending":
        raise HTTPException(status_code=400, detail="Approval already processed")

    # Update database
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE approval_requests
            SET status = 'denied', approved_by = $1, approved_at = NOW()
            WHERE id = $2
            """,
            approver,
            approval_id
        )

        # Log in audit table
        await conn.execute(
            """
            INSERT INTO audit_log (approval_id, action, actor, details)
            VALUES ($1, 'deny', $2, $3)
            """,
            approval_id,
            approver,
            {"reason": reason}
        )

    # Send signal to Temporal workflow
    workflow_handle = temporal_client.get_workflow_handle(
        workflow_id=row["workflow_id"],
        run_id=row["run_id"]
    )

    await workflow_handle.signal(
        "approval_signal",
        {
            "status": "denied",
            "approver": approver,
            "reason": reason
        }
    )

    return {"status": "denied", "approval_id": approval_id}


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard showing pending approvals"""

    if not db_pool:
        return HTMLResponse("<h1>Service Unavailable</h1>", status_code=503)

    async with db_pool.acquire() as conn:
        pending = await conn.fetch(
            """
            SELECT id, workflow_id, task_description, risk_level, created_at
            FROM approval_requests
            WHERE status = 'pending'
            ORDER BY
                CASE risk_level
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    ELSE 3
                END,
                created_at ASC
            """
        )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "pending_approvals": [dict(row) for row in pending]
        }
    )


@app.get("/approval/{approval_id}", response_class=HTMLResponse)
async def approval_detail(request: Request, approval_id: str):
    """Approval detail page"""

    if not db_pool:
        return HTMLResponse("<h1>Service Unavailable</h1>", status_code=503)

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, workflow_id, run_id, task_description, risk_level,
                   context, status, approved_by, created_at, approved_at
            FROM approval_requests
            WHERE id = $1
            """,
            approval_id
        )

    if not row:
        return HTMLResponse("<h1>Approval Not Found</h1>", status_code=404)

    return templates.TemplateResponse(
        "approval_detail.html",
        {
            "request": request,
            "approval": dict(row)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001)
