"""
Temporal Workflows - Durable execution with human-in-the-loop approvals.

Workflows:
- ProjectPipeline: Create a new project from goal to deployment
- ApprovalFlow: Handle human approval with timeout and cancellation
"""

from datetime import timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities (defined in activities.py)
with workflow.unsafe.imports_passed_through():
    from activities import (
        invoke_overseer,
        invoke_developer,
        request_approval,
        check_approval_status,
        send_telegram_notification,
        execute_deployment,
        validate_output
    )


@dataclass
class ProjectRequest:
    """Request to create a new project"""
    goal: str
    context: Dict[str, Any]
    requester: str
    idempotency_key: str


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    task_description: str
    risk_level: str  # low, medium, high
    context: Dict[str, Any]
    required_approvers: int = 1


@dataclass
class ApprovalSignal:
    """Signal sent when human approves/denies"""
    status: str  # approved, denied
    approver: str
    reason: Optional[str] = None


@workflow.defn
class ProjectPipelineWorkflow:
    """
    End-to-end workflow for creating a project:
    1. Overseer decomposes goal into tasks
    2. For each task, request approval based on risk level
    3. Upon approval, invoke Developer to generate code
    4. Validate generated code
    5. Deploy (with final approval)
    """

    def __init__(self):
        self.approval_signals: List[ApprovalSignal] = []

    @workflow.run
    async def run(self, request: ProjectRequest) -> Dict[str, Any]:
        """Main workflow execution"""

        workflow.logger.info(f"Starting project pipeline for goal: {request.goal}")

        # Step 1: Overseer decomposes goal
        workflow.logger.info("Step 1: Invoking Overseer to decompose goal")

        overseer_result = await workflow.execute_activity(
            invoke_overseer,
            args=[{
                "task": request.goal,
                "context": request.context,
                "idempotency_key": f"{request.idempotency_key}-overseer"
            }],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10)
            )
        )

        tasks = overseer_result.get("plan", [])
        workflow.logger.info(f"Overseer created {len(tasks)} tasks")

        # Step 2-4: Execute each task with approval
        executed_tasks = []

        for i, task_item in enumerate(tasks):
            task_desc = task_item.get("task", "")
            task_agent = task_item.get("agent", "developer")

            workflow.logger.info(f"Processing task {i+1}/{len(tasks)}: {task_desc}")

            # Determine risk level (simple heuristic)
            risk_level = self._assess_risk(task_desc)

            # Request approval for medium/high risk
            if risk_level in ["medium", "high"]:
                required_approvers = 2 if risk_level == "high" else 1

                approval_result = await self._wait_for_approval(
                    ApprovalRequest(
                        task_description=task_desc,
                        risk_level=risk_level,
                        context={"task_index": i, "agent": task_agent},
                        required_approvers=required_approvers
                    )
                )

                if approval_result["status"] != "approved":
                    workflow.logger.warning(f"Task {i+1} denied: {approval_result.get('reason')}")
                    return {
                        "status": "cancelled",
                        "reason": f"Task '{task_desc}' was denied",
                        "executed_tasks": executed_tasks
                    }

            # Execute task based on agent
            if task_agent == "developer":
                task_result = await workflow.execute_activity(
                    invoke_developer,
                    args=[{
                        "task": task_desc,
                        "context": request.context,
                        "idempotency_key": f"{request.idempotency_key}-dev-{i}"
                    }],
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=RetryPolicy(maximum_attempts=2)
                )
            else:
                # For now, only developer agent executes tasks
                # Overseer only does decomposition
                task_result = {"status": "skipped", "agent": task_agent}

            # Validate output
            if task_result.get("status") != "skipped":
                validation = await workflow.execute_activity(
                    validate_output,
                    args=[task_result],
                    start_to_close_timeout=timedelta(minutes=2)
                )

                if not validation.get("valid", False):
                    workflow.logger.error(f"Task {i+1} validation failed: {validation.get('errors')}")
                    return {
                        "status": "failed",
                        "reason": f"Validation failed for task '{task_desc}'",
                        "errors": validation.get("errors"),
                        "executed_tasks": executed_tasks
                    }

            executed_tasks.append({
                "task": task_desc,
                "result": task_result,
                "risk_level": risk_level
            })

        # Step 5: Final deployment approval (always high risk)
        workflow.logger.info("Requesting final deployment approval")

        deployment_approval = await self._wait_for_approval(
            ApprovalRequest(
                task_description=f"Deploy project: {request.goal}",
                risk_level="high",
                context={"tasks_count": len(executed_tasks)},
                required_approvers=2
            )
        )

        if deployment_approval["status"] != "approved":
            return {
                "status": "ready_for_deployment",
                "reason": "All tasks completed, deployment not approved",
                "executed_tasks": executed_tasks
            }

        # Execute deployment
        deployment_result = await workflow.execute_activity(
            execute_deployment,
            args=[{
                "tasks": executed_tasks,
                "idempotency_key": f"{request.idempotency_key}-deploy"
            }],
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=RetryPolicy(maximum_attempts=1)
        )

        return {
            "status": "completed",
            "executed_tasks": executed_tasks,
            "deployment": deployment_result,
            "goal": request.goal
        }

    async def _wait_for_approval(self, request: ApprovalRequest) -> Dict[str, Any]:
        """
        Wait for human approval via signal.

        Flow:
        1. Request approval (creates DB record, sends Telegram notification)
        2. Wait for approval signal (24h timeout)
        3. Return approval status
        """
        workflow.logger.info(f"Requesting approval for: {request.task_description}")

        # Create approval request
        approval_id = await workflow.execute_activity(
            request_approval,
            args=[{
                "workflow_id": workflow.info().workflow_id,
                "run_id": workflow.info().run_id,
                "task_description": request.task_description,
                "risk_level": request.risk_level,
                "context": request.context
            }],
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Send notification
        await workflow.execute_activity(
            send_telegram_notification,
            args=[{
                "approval_id": approval_id,
                "task": request.task_description,
                "risk_level": request.risk_level
            }],
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Wait for signal or timeout
        try:
            await workflow.wait_condition(
                lambda: len(self.approval_signals) >= request.required_approvers,
                timeout=timedelta(hours=24)
            )

            # Check if all approvals are positive
            approved_count = sum(
                1 for sig in self.approval_signals if sig.status == "approved"
            )

            if approved_count >= request.required_approvers:
                return {
                    "status": "approved",
                    "approvers": [sig.approver for sig in self.approval_signals]
                }
            else:
                denied_sig = next(sig for sig in self.approval_signals if sig.status == "denied")
                return {
                    "status": "denied",
                    "reason": denied_sig.reason or "Approval denied"
                }

        except TimeoutError:
            workflow.logger.warning("Approval timed out after 24 hours")
            return {
                "status": "timeout",
                "reason": "No approval received within 24 hours"
            }

    @workflow.signal
    async def approval_signal(self, signal: ApprovalSignal):
        """Receive approval/denial signal from human"""
        workflow.logger.info(f"Received approval signal: {signal.status} from {signal.approver}")
        self.approval_signals.append(signal)

    def _assess_risk(self, task_description: str) -> str:
        """
        Assess risk level of a task.

        Rules:
        - low: Documentation, PR drafts, read-only operations
        - medium: Code generation, schema changes, dev deploys
        - high: Production deploys, billing, data migrations, refunds
        """
        task_lower = task_description.lower()

        # High risk indicators
        high_risk_keywords = [
            "production", "deploy", "billing", "refund", "migration",
            "delete", "drop", "payment", "pricing"
        ]
        if any(kw in task_lower for kw in high_risk_keywords):
            return "high"

        # Low risk indicators
        low_risk_keywords = [
            "documentation", "readme", "comment", "draft", "read"
        ]
        if any(kw in task_lower for kw in low_risk_keywords):
            return "low"

        # Default to medium
        return "medium"


@workflow.defn
class SimpleTaskWorkflow:
    """Simple workflow for executing a single task without approval"""

    @workflow.run
    async def run(self, task: str, agent: str = "developer") -> Dict[str, Any]:
        """Execute a single task"""

        if agent == "developer":
            result = await workflow.execute_activity(
                invoke_developer,
                args=[{
                    "task": task,
                    "context": {},
                    "idempotency_key": workflow.info().workflow_id
                }],
                start_to_close_timeout=timedelta(minutes=5)
            )
        else:
            result = await workflow.execute_activity(
                invoke_overseer,
                args=[{
                    "task": task,
                    "context": {},
                    "idempotency_key": workflow.info().workflow_id
                }],
                start_to_close_timeout=timedelta(minutes=5)
            )

        return result
