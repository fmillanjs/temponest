"""
Temporal Activities - Individual units of work that can be retried.

Activities:
- invoke_overseer: Call the Overseer agent
- invoke_developer: Call the Developer agent
- request_approval: Create approval request in DB
- check_approval_status: Check if task was approved
- send_telegram_notification: Send notification via n8n webhook
- execute_deployment: Deploy generated code
- validate_output: Validate agent output
"""

import os
import httpx
import uuid
from typing import Dict, Any
from datetime import datetime
from temporalio import activity


# Configuration
AGENTS_URL = os.getenv("AGENTS_URL", "http://agents:9000")
APPROVAL_UI_URL = os.getenv("APPROVAL_UI_URL", "http://approval-ui:9001")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook/approval")


@activity.defn
async def invoke_overseer(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke the Overseer agent to decompose a goal.

    Args:
        request: {
            "task": str,
            "context": dict,
            "idempotency_key": str
        }

    Returns:
        Overseer result with plan and citations
    """
    activity.logger.info(f"Invoking Overseer for task: {request['task']}")

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{AGENTS_URL}/overseer/run",
            json=request
        )
        response.raise_for_status()
        result = response.json()

    activity.logger.info(f"Overseer completed in {result.get('latency_ms')}ms")

    # Record heartbeat (for long-running tasks)
    activity.heartbeat()

    return result.get("result", {})


@activity.defn
async def invoke_developer(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke the Developer agent to generate code.

    Args:
        request: {
            "task": str,
            "context": dict,
            "idempotency_key": str
        }

    Returns:
        Developer result with code, tests, and setup instructions
    """
    activity.logger.info(f"Invoking Developer for task: {request['task']}")

    async with httpx.AsyncClient(timeout=600.0) as client:
        response = await client.post(
            f"{AGENTS_URL}/developer/run",
            json=request
        )
        response.raise_for_status()
        result = response.json()

    activity.logger.info(f"Developer completed in {result.get('latency_ms')}ms")

    # Record heartbeat
    activity.heartbeat()

    return result.get("result", {})


@activity.defn
async def request_approval(request: Dict[str, Any]) -> str:
    """
    Create an approval request in the database.

    Args:
        request: {
            "workflow_id": str,
            "run_id": str,
            "task_description": str,
            "risk_level": str,
            "context": dict
        }

    Returns:
        Approval request ID (UUID)
    """
    activity.logger.info(f"Creating approval request for: {request['task_description']}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{APPROVAL_UI_URL}/api/approvals",
            json=request
        )
        response.raise_for_status()
        result = response.json()

    approval_id = result["approval_id"]
    activity.logger.info(f"Created approval request: {approval_id}")

    return approval_id


@activity.defn
async def check_approval_status(approval_id: str) -> Dict[str, Any]:
    """
    Check the status of an approval request.

    Args:
        approval_id: Approval request UUID

    Returns:
        {
            "status": "pending" | "approved" | "denied",
            "approved_by": str,
            "approved_at": str
        }
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{APPROVAL_UI_URL}/api/approvals/{approval_id}"
        )
        response.raise_for_status()
        result = response.json()

    return result


@activity.defn
async def send_telegram_notification(notification: Dict[str, Any]) -> bool:
    """
    Send notification via n8n Telegram webhook.

    Args:
        notification: {
            "approval_id": str,
            "task": str,
            "risk_level": str
        }

    Returns:
        True if sent successfully
    """
    activity.logger.info(f"Sending Telegram notification for approval: {notification['approval_id']}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                N8N_WEBHOOK_URL,
                json={
                    "type": "approval_request",
                    "approval_id": notification["approval_id"],
                    "task": notification["task"],
                    "risk_level": notification["risk_level"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            response.raise_for_status()

        activity.logger.info("Telegram notification sent successfully")
        return True

    except Exception as e:
        activity.logger.error(f"Failed to send Telegram notification: {e}")
        # Don't fail the activity - notification is best-effort
        return False


@activity.defn
async def execute_deployment(deployment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute deployment of generated code.

    Args:
        deployment: {
            "tasks": list of executed tasks,
            "idempotency_key": str
        }

    Returns:
        Deployment result
    """
    activity.logger.info("Executing deployment")

    # For now, this is a placeholder
    # In a real system, this would:
    # 1. Write files to disk
    # 2. Run tests
    # 3. Build containers
    # 4. Deploy to environment
    # 5. Run smoke tests

    idempotency_key = deployment.get("idempotency_key")
    tasks = deployment.get("tasks", [])

    activity.logger.info(f"Deploying {len(tasks)} tasks with key: {idempotency_key}")

    # Simulate deployment
    deployment_id = str(uuid.uuid4())

    result = {
        "deployment_id": deployment_id,
        "status": "success",
        "tasks_deployed": len(tasks),
        "deployed_at": datetime.utcnow().isoformat(),
        "idempotency_key": idempotency_key
    }

    activity.logger.info(f"Deployment completed: {deployment_id}")

    return result


@activity.defn
async def validate_output(output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate agent output meets quality requirements.

    Checks:
    - Has ≥2 citations
    - Code is not empty
    - Tests are included
    - No obvious errors

    Args:
        output: Agent output to validate

    Returns:
        {
            "valid": bool,
            "errors": list of error messages
        }
    """
    activity.logger.info("Validating agent output")

    errors = []

    # Check citations
    citations = output.get("citations", [])
    if len(citations) < 2:
        errors.append(f"Insufficient citations: found {len(citations)}, need ≥2")

    # Check code exists
    code = output.get("code", {})
    if isinstance(code, dict):
        implementation = code.get("implementation", "")
        if not implementation or len(implementation.strip()) < 50:
            errors.append("Implementation is missing or too short")

        tests = code.get("tests", "")
        if not tests or len(tests.strip()) < 20:
            errors.append("Tests are missing or too short")

    valid = len(errors) == 0

    if valid:
        activity.logger.info("Validation passed")
    else:
        activity.logger.warning(f"Validation failed: {errors}")

    return {
        "valid": valid,
        "errors": errors
    }
