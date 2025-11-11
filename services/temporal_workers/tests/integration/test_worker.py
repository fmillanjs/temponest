"""
Integration tests for Temporal worker.
Tests worker initialization and configuration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os


class TestWorkerConfiguration:
    """Test worker configuration"""

    def test_temporal_host_env_variable(self):
        """Test TEMPORAL_HOST environment variable"""
        from worker import TEMPORAL_HOST
        assert TEMPORAL_HOST is not None

    def test_temporal_namespace_env_variable(self):
        """Test TEMPORAL_NAMESPACE environment variable"""
        from worker import TEMPORAL_NAMESPACE
        assert TEMPORAL_NAMESPACE is not None

    def test_task_queue_configured(self):
        """Test task queue is configured"""
        from worker import TASK_QUEUE
        assert TASK_QUEUE == "agentic-task-queue"


class TestWorkerImports:
    """Test worker imports all required components"""

    def test_workflow_imports(self):
        """Test workflows are imported"""
        from worker import ProjectPipelineWorkflow, SimpleTaskWorkflow
        assert ProjectPipelineWorkflow is not None
        assert SimpleTaskWorkflow is not None

    def test_activity_imports(self):
        """Test all activities are imported"""
        from worker import (
            invoke_overseer,
            invoke_developer,
            request_approval,
            check_approval_status,
            send_telegram_notification,
            execute_deployment,
            validate_output
        )

        assert invoke_overseer is not None
        assert invoke_developer is not None
        assert request_approval is not None
        assert check_approval_status is not None
        assert send_telegram_notification is not None
        assert execute_deployment is not None
        assert validate_output is not None


@pytest.mark.asyncio
class TestWorkerInitialization:
    """Test worker initialization (mocked)"""

    @patch('worker.Client.connect')
    @patch('worker.Worker')
    async def test_worker_main_function_connects_to_temporal(self, mock_worker_class, mock_client_connect):
        """Test main function connects to Temporal"""
        from worker import main

        # Mock client
        mock_client = AsyncMock()
        mock_client_connect.return_value = mock_client

        # Mock worker
        mock_worker = MagicMock()
        mock_worker.run = AsyncMock(side_effect=KeyboardInterrupt)  # Stop after init
        mock_worker_class.return_value = mock_worker

        # Run main (will exit due to KeyboardInterrupt)
        try:
            await main()
        except KeyboardInterrupt:
            pass

        # Verify client.connect was called
        mock_client_connect.assert_called_once()

    @patch('worker.Client.connect')
    @patch('worker.Worker')
    async def test_worker_main_function_creates_worker(self, mock_worker_class, mock_client_connect):
        """Test main function creates worker"""
        from worker import main, TASK_QUEUE

        # Mock client
        mock_client = AsyncMock()
        mock_client_connect.return_value = mock_client

        # Mock worker
        mock_worker = MagicMock()
        mock_worker.run = AsyncMock(side_effect=KeyboardInterrupt)
        mock_worker_class.return_value = mock_worker

        # Run main
        try:
            await main()
        except KeyboardInterrupt:
            pass

        # Verify worker was created
        mock_worker_class.assert_called_once()
        call_args = mock_worker_class.call_args

        # Check task queue
        assert call_args[1]['task_queue'] == TASK_QUEUE

        # Check workflows are registered
        workflows = call_args[1]['workflows']
        assert len(workflows) == 2

        # Check activities are registered
        activities = call_args[1]['activities']
        assert len(activities) == 7

    @patch('worker.Client.connect')
    @patch('worker.Worker')
    async def test_worker_main_function_starts_worker(self, mock_worker_class, mock_client_connect):
        """Test main function starts worker"""
        from worker import main

        # Mock client
        mock_client = AsyncMock()
        mock_client_connect.return_value = mock_client

        # Mock worker
        mock_worker = MagicMock()
        mock_worker.run = AsyncMock(side_effect=KeyboardInterrupt)
        mock_worker_class.return_value = mock_worker

        # Run main
        try:
            await main()
        except KeyboardInterrupt:
            pass

        # Verify worker.run was called
        mock_worker.run.assert_called_once()
