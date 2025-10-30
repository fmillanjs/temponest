"""
Temporal Worker - Starts workflow and activity workers.

This worker connects to Temporal and processes workflows and activities.
"""

import os
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from workflows import ProjectPipelineWorkflow, SimpleTaskWorkflow
from activities import (
    invoke_overseer,
    invoke_developer,
    request_approval,
    check_approval_status,
    send_telegram_notification,
    execute_deployment,
    validate_output
)


TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "temporal:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
TASK_QUEUE = "agentic-task-queue"


async def main():
    """Start the Temporal worker"""

    print(f"🔌 Connecting to Temporal at {TEMPORAL_HOST}...")

    # Connect to Temporal
    client = await Client.connect(
        TEMPORAL_HOST,
        namespace=TEMPORAL_NAMESPACE
    )

    print(f"✅ Connected to Temporal namespace: {TEMPORAL_NAMESPACE}")

    # Create worker
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[ProjectPipelineWorkflow, SimpleTaskWorkflow],
        activities=[
            invoke_overseer,
            invoke_developer,
            request_approval,
            check_approval_status,
            send_telegram_notification,
            execute_deployment,
            validate_output
        ]
    )

    print(f"🚀 Starting Temporal worker on task queue: {TASK_QUEUE}")

    # Run worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
