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


async def connect_with_retry(max_retries: int = 10, initial_delay: float = 1.0) -> Client:
    """Connect to Temporal with exponential backoff retry"""
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔌 Connecting to Temporal at {TEMPORAL_HOST} (attempt {attempt}/{max_retries})...")
            client = await Client.connect(
                TEMPORAL_HOST,
                namespace=TEMPORAL_NAMESPACE
            )
            print(f"✅ Connected to Temporal namespace: {TEMPORAL_NAMESPACE}")
            return client
        except Exception as e:
            if attempt == max_retries:
                print(f"❌ Failed to connect to Temporal after {max_retries} attempts: {e}")
                raise
            print(f"⚠️  Connection attempt {attempt} failed: {e}")
            print(f"⏳ Retrying in {delay:.1f} seconds...")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30.0)  # Exponential backoff, max 30s


async def main():
    """Start the Temporal worker"""

    # Connect to Temporal with retry logic
    client = await connect_with_retry()

    print(f"✅ Connection established to Temporal")

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
