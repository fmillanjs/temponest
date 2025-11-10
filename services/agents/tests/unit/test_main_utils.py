"""
Unit tests for main.py utility functions and helpers.
Focuses on pure function testing to boost coverage.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal


class TestTokenCounting:
    """Test token counting utilities"""

    def test_count_tokens_basic(self):
        """Test basic token counting"""
        from app.main import count_tokens

        text = "Hello, world!"
        tokens = count_tokens(text)

        assert isinstance(tokens, int)
        assert tokens > 0
        assert tokens < 10

    def test_count_tokens_empty(self):
        """Test token counting with empty string"""
        from app.main import count_tokens

        text = ""
        tokens = count_tokens(text)

        assert tokens == 0

    def test_count_tokens_long_text(self):
        """Test token counting with long text"""
        from app.main import count_tokens

        text = "A" * 1000
        tokens = count_tokens(text)

        assert tokens > 0
        assert tokens < 2000  # Should be reasonable

    def test_count_tokens_with_model_fallback(self):
        """Test token counting falls back to cl100k_base for unknown models"""
        from app.main import count_tokens

        text = "Test message"
        # Use a made-up model name that doesn't exist
        tokens = count_tokens(text, model="unknown-model-xyz")

        assert isinstance(tokens, int)
        assert tokens > 0


class TestBudgetEnforcement:
    """Test budget enforcement guardrail"""

    def test_enforce_budget_within_limit(self):
        """Test budget allows text within limit"""
        from app.main import enforce_budget

        text = "This is a small task"
        result = enforce_budget(text, budget=1000)

        assert result is True

    def test_enforce_budget_exactly_at_limit(self):
        """Test budget at exact limit"""
        from app.main import enforce_budget

        text = "A" * 100
        tokens = len(text)  # Rough approximation
        result = enforce_budget(text, budget=tokens * 2)

        assert result is True

    def test_enforce_budget_exceeds_limit(self):
        """Test budget blocks text over limit"""
        from app.main import enforce_budget

        large_text = "A" * 10000
        result = enforce_budget(large_text, budget=10)

        assert result is False

    def test_enforce_budget_with_default(self):
        """Test budget enforcement with default budget"""
        from app.main import enforce_budget

        small_text = "Hello"
        result = enforce_budget(small_text)

        assert result is True


class TestCitationValidation:
    """Test citation validation guardrail"""

    def test_validate_citations_sufficient_good_citations(self):
        """Test accepts sufficient good citations"""
        from app.main import validate_citations

        citations = [
            {"source": "doc1.md", "version": "v1", "score": 0.9},
            {"source": "doc2.md", "version": "v1", "score": 0.85}
        ]

        result = validate_citations(citations)
        assert result is True

    def test_validate_citations_more_than_minimum(self):
        """Test accepts more than 2 citations"""
        from app.main import validate_citations

        citations = [
            {"source": "doc1.md", "version": "v1", "score": 0.9},
            {"source": "doc2.md", "version": "v1", "score": 0.85},
            {"source": "doc3.md", "version": "v1", "score": 0.80}
        ]

        result = validate_citations(citations)
        assert result is True

    def test_validate_citations_insufficient_count_zero(self):
        """Test rejects zero citations"""
        from app.main import validate_citations

        citations = []

        result = validate_citations(citations)
        assert result is False

    def test_validate_citations_insufficient_count_one(self):
        """Test rejects single citation"""
        from app.main import validate_citations

        citations = [
            {"source": "doc1.md", "version": "v1", "score": 0.9}
        ]

        result = validate_citations(citations)
        assert result is False

    def test_validate_citations_low_scores(self):
        """Test rejects low-scoring citations"""
        from app.main import validate_citations

        citations = [
            {"source": "doc1.md", "version": "v1", "score": 0.3},
            {"source": "doc2.md", "version": "v1", "score": 0.2}
        ]

        result = validate_citations(citations)
        assert result is False

    def test_validate_citations_mixed_scores(self):
        """Test rejects when first citations have low scores"""
        from app.main import validate_citations

        citations = [
            {"source": "doc1.md", "version": "v1", "score": 0.3},
            {"source": "doc2.md", "version": "v1", "score": 0.9}
        ]

        result = validate_citations(citations)
        assert result is False

    def test_validate_citations_missing_source(self):
        """Test rejects citations missing source field"""
        from app.main import validate_citations

        citations = [
            {"version": "v1", "score": 0.9},
            {"source": "doc2.md", "version": "v1", "score": 0.85}
        ]

        result = validate_citations(citations)
        assert result is False

    def test_validate_citations_missing_version(self):
        """Test rejects citations missing version field"""
        from app.main import validate_citations

        citations = [
            {"source": "doc1.md", "score": 0.9},
            {"source": "doc2.md", "version": "v1", "score": 0.85}
        ]

        result = validate_citations(citations)
        assert result is False

    def test_validate_citations_missing_score(self):
        """Test rejects citations missing score field"""
        from app.main import validate_citations

        citations = [
            {"source": "doc1.md", "version": "v1"},
            {"source": "doc2.md", "version": "v1", "score": 0.85}
        ]

        result = validate_citations(citations)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_citations_at_threshold(self):
        """Test citations exactly at RAG_MIN_SCORE threshold"""
        from app.main import validate_citations
        from app.settings import settings

        citations = [
            {"source": "doc1.md", "version": "v1", "score": settings.RAG_MIN_SCORE},
            {"source": "doc2.md", "version": "v1", "score": settings.RAG_MIN_SCORE}
        ]

        result = validate_citations(citations)
        # Should be valid at exactly the threshold
        assert result is True


class TestRecordExecutionCost:
    """Test cost recording helper function"""

    @pytest.mark.asyncio
    @patch("app.main.cost_tracker")
    async def test_record_execution_cost_success(self, mock_cost_tracker, test_auth_context):
        """Test successful cost recording"""
        from app.main import record_execution_cost

        mock_cost_tracker.record_execution = AsyncMock(return_value={
            "task_id": "test-123",
            "total_cost_usd": "0.0150",
            "input_tokens": 1000,
            "output_tokens": 500,
            "budget_status": {"within_budget": True}
        })

        result = await record_execution_cost(
            task_id="test-123",
            agent_name="overseer",
            user_context=test_auth_context,
            model_provider="anthropic",
            model_name="claude-3-sonnet-20240229",
            tokens_used=1500,
            latency_ms=2500,
            status="completed",
            project_id="proj-123",
            workflow_id="wf-456",
            citations_count=3
        )

        assert result is not None
        assert result["task_id"] == "test-123"
        assert "total_cost_usd" in result

        # Verify the call was made with correct parameters
        mock_cost_tracker.record_execution.assert_called_once()
        call_args = mock_cost_tracker.record_execution.call_args[1]
        assert call_args["task_id"] == "test-123"
        assert call_args["agent_name"] == "overseer"
        assert call_args["model_provider"] == "anthropic"
        assert call_args["project_id"] == "proj-123"
        assert call_args["workflow_id"] == "wf-456"

    @pytest.mark.asyncio
    async def test_record_execution_cost_no_tracker(self, test_auth_context):
        """Test cost recording when tracker is None"""
        from app.main import record_execution_cost

        with patch("app.main.cost_tracker", None):
            result = await record_execution_cost(
                task_id="test-123",
                agent_name="overseer",
                user_context=test_auth_context,
                model_provider="anthropic",
                model_name="claude-3-sonnet-20240229",
                tokens_used=1500,
                latency_ms=2500
            )

            assert result is None

    @pytest.mark.asyncio
    @patch("app.main.cost_tracker")
    async def test_record_execution_cost_error_handling(self, mock_cost_tracker, test_auth_context):
        """Test cost recording handles errors gracefully"""
        from app.main import record_execution_cost

        mock_cost_tracker.record_execution = AsyncMock(side_effect=Exception("Database error"))

        result = await record_execution_cost(
            task_id="test-123",
            agent_name="overseer",
            user_context=test_auth_context,
            model_provider="anthropic",
            model_name="claude-3-sonnet-20240229",
            tokens_used=1500,
            latency_ms=2500
        )

        # Should return None on error
        assert result is None

    @pytest.mark.asyncio
    @patch("app.main.cost_tracker")
    async def test_record_execution_cost_optional_params(self, mock_cost_tracker, test_auth_context):
        """Test cost recording with optional parameters omitted"""
        from app.main import record_execution_cost

        mock_cost_tracker.record_execution = AsyncMock(return_value={
            "task_id": "test-456",
            "total_cost_usd": "0.0100"
        })

        result = await record_execution_cost(
            task_id="test-456",
            agent_name="developer",
            user_context=test_auth_context,
            model_provider="openai",
            model_name="gpt-4",
            tokens_used=1000,
            latency_ms=1500
        )

        assert result is not None

        # Verify optional params were passed as None
        call_args = mock_cost_tracker.record_execution.call_args[1]
        assert call_args["project_id"] is None
        assert call_args["workflow_id"] is None

    @pytest.mark.asyncio
    @patch("app.main.cost_tracker")
    async def test_record_execution_cost_token_split(self, mock_cost_tracker, test_auth_context):
        """Test that tokens are split 40/60 input/output"""
        from app.main import record_execution_cost

        mock_cost_tracker.record_execution = AsyncMock(return_value={
            "task_id": "test-789",
            "total_cost_usd": "0.0200"
        })

        total_tokens = 1000
        result = await record_execution_cost(
            task_id="test-789",
            agent_name="qa_tester",
            user_context=test_auth_context,
            model_provider="anthropic",
            model_name="claude-3-haiku-20240307",
            tokens_used=total_tokens,
            latency_ms=2000
        )

        assert result is not None

        # Verify 40/60 split
        call_args = mock_cost_tracker.record_execution.call_args[1]
        assert call_args["input_tokens"] == 400  # 40% of 1000
        assert call_args["output_tokens"] == 600  # 60% of 1000

    @pytest.mark.asyncio
    @patch("app.main.cost_tracker")
    async def test_record_execution_cost_different_statuses(self, mock_cost_tracker, test_auth_context):
        """Test cost recording with different status values"""
        from app.main import record_execution_cost

        statuses = ["completed", "failed", "timeout", "cancelled"]

        for status in statuses:
            mock_cost_tracker.record_execution = AsyncMock(return_value={
                "task_id": f"test-{status}",
                "total_cost_usd": "0.0100"
            })

            result = await record_execution_cost(
                task_id=f"test-{status}",
                agent_name="devops",
                user_context=test_auth_context,
                model_provider="anthropic",
                model_name="claude-3-opus-20240229",
                tokens_used=1000,
                latency_ms=3000,
                status=status
            )

            assert result is not None
            call_args = mock_cost_tracker.record_execution.call_args[1]
            assert call_args["status"] == status


class TestUpdateMetricsPeriodically:
    """Test background metrics update task"""

    @pytest.mark.asyncio
    @patch("app.main.rag_memory")
    @patch("app.main.langfuse_tracer")
    @patch("app.main.db_pool")
    @patch("app.main.MetricsRecorder")
    async def test_update_metrics_all_healthy(
        self,
        mock_metrics,
        mock_db,
        mock_langfuse,
        mock_rag
    ):
        """Test metrics update when all services healthy"""
        from app.main import update_metrics_periodically

        mock_rag.is_healthy.return_value = True
        mock_langfuse.is_healthy.return_value = True
        mock_db.get_size.return_value = 10
        mock_db.get_idle_size.return_value = 5

        # Run one iteration
        task = asyncio.create_task(update_metrics_periodically())
        await asyncio.sleep(0.1)  # Let it run once
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # Verify metrics were updated
        assert mock_metrics.update_service_health.called

    @pytest.mark.asyncio
    @patch("app.main.rag_memory", None)
    @patch("app.main.langfuse_tracer", None)
    @patch("app.main.db_pool", None)
    async def test_update_metrics_no_services(self):
        """Test metrics update when no services initialized"""
        from app.main import update_metrics_periodically

        # Should not crash even if services are None
        task = asyncio.create_task(update_metrics_periodically())
        await asyncio.sleep(0.1)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # Just verify it doesn't crash

    @pytest.mark.asyncio
    @patch("app.main.rag_memory")
    @patch("app.main.MetricsRecorder")
    async def test_update_metrics_handles_errors(self, mock_metrics, mock_rag):
        """Test metrics update handles errors gracefully"""
        from app.main import update_metrics_periodically

        # Make is_healthy raise an exception
        mock_rag.is_healthy.side_effect = Exception("Service error")

        task = asyncio.create_task(update_metrics_periodically())
        await asyncio.sleep(0.1)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # Should not crash, just continue


# Import asyncio for async tests
import asyncio
