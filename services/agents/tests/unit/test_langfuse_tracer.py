"""
Unit tests for Langfuse Tracer.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from app.memory.langfuse_tracer import LangfuseTracer


class TestLangfuseTracerInit:
    """Test suite for LangfuseTracer initialization"""

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_init_with_keys(self, mock_langfuse):
        """Test initialization with valid keys"""
        mock_client = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key",
            host="http://custom-host:3000"
        )

        assert tracer.enabled is True
        assert tracer.client == mock_client
        assert tracer.trace_count == 0
        mock_langfuse.assert_called_once_with(
            public_key="test_public_key",
            secret_key="test_secret_key",
            host="http://custom-host:3000"
        )

    def test_init_without_public_key(self):
        """Test initialization without public key disables tracer"""
        tracer = LangfuseTracer(
            public_key=None,
            secret_key="test_secret_key"
        )

        assert tracer.enabled is False
        assert tracer.client is None
        assert tracer.trace_count == 0

    def test_init_without_secret_key(self):
        """Test initialization without secret key disables tracer"""
        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key=None
        )

        assert tracer.enabled is False
        assert tracer.client is None
        assert tracer.trace_count == 0

    def test_init_with_empty_keys(self):
        """Test initialization with empty keys disables tracer"""
        tracer = LangfuseTracer(
            public_key="",
            secret_key=""
        )

        assert tracer.enabled is False
        assert tracer.client is None
        assert tracer.trace_count == 0

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_init_default_host(self, mock_langfuse):
        """Test initialization with default host"""
        mock_client = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        mock_langfuse.assert_called_once_with(
            public_key="test_public_key",
            secret_key="test_secret_key",
            host="http://langfuse:3000"
        )


class TestLangfuseTracerHealth:
    """Test suite for health check functionality"""

    def test_is_healthy_when_disabled(self):
        """Test is_healthy returns True when disabled"""
        tracer = LangfuseTracer(
            public_key=None,
            secret_key=None
        )

        assert tracer.is_healthy() is True

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_is_healthy_success(self, mock_langfuse):
        """Test is_healthy when flush succeeds"""
        mock_client = Mock()
        mock_client.flush = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        assert tracer.is_healthy() is True
        mock_client.flush.assert_called_once()

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_is_healthy_failure(self, mock_langfuse):
        """Test is_healthy when flush fails"""
        mock_client = Mock()
        mock_client.flush = Mock(side_effect=Exception("Connection failed"))
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        assert tracer.is_healthy() is False


class TestLangfuseTracerTraceCount:
    """Test suite for trace count functionality"""

    def test_get_trace_count_initial(self):
        """Test get_trace_count returns 0 initially"""
        tracer = LangfuseTracer(
            public_key=None,
            secret_key=None
        )

        assert tracer.get_trace_count() == 0

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_get_trace_count_increments(self, mock_langfuse):
        """Test get_trace_count increments after trace_agent_execution"""
        mock_client = Mock()
        mock_trace = Mock()
        mock_trace.id = "trace_123"
        mock_client.trace = Mock(return_value=mock_trace)
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        tracer.trace_agent_execution(
            agent_name="test_agent",
            task_id="task_123",
            task="test task",
            context={},
            model_info={}
        )

        assert tracer.get_trace_count() == 1


class TestLangfuseTracerAgentExecution:
    """Test suite for trace_agent_execution functionality"""

    def test_trace_agent_execution_when_disabled(self):
        """Test trace_agent_execution returns None when disabled"""
        tracer = LangfuseTracer(
            public_key=None,
            secret_key=None
        )

        trace_id = tracer.trace_agent_execution(
            agent_name="test_agent",
            task_id="task_123",
            task="test task",
            context={"key": "value"},
            model_info={"model": "gpt-4"}
        )

        assert trace_id is None

    @patch('app.memory.langfuse_tracer.Langfuse')
    @patch('app.memory.langfuse_tracer.datetime')
    def test_trace_agent_execution_success(self, mock_datetime, mock_langfuse):
        """Test trace_agent_execution creates trace with all metadata"""
        mock_datetime.utcnow.return_value.isoformat.return_value = "2024-01-01T00:00:00"

        mock_client = Mock()
        mock_trace = Mock()
        mock_trace.id = "trace_123"
        mock_client.trace = Mock(return_value=mock_trace)
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        context = {"key": "value"}
        model_info = {
            "model": "gpt-4",
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 1000,
            "seed": 42
        }

        trace_id = tracer.trace_agent_execution(
            agent_name="test_agent",
            task_id="task_123",
            task="test task",
            context=context,
            model_info=model_info
        )

        assert trace_id == "trace_123"
        assert tracer.trace_count == 1

        mock_client.trace.assert_called_once_with(
            name="agent.test_agent",
            user_id="system",
            session_id="task_123",
            metadata={
                "agent": "test_agent",
                "task_id": "task_123",
                "task": "test task",
                "context": context,
                "model": "gpt-4",
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 1000,
                "seed": 42,
                "timestamp": "2024-01-01T00:00:00"
            }
        )

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_agent_execution_with_minimal_model_info(self, mock_langfuse):
        """Test trace_agent_execution with minimal model info"""
        mock_client = Mock()
        mock_trace = Mock()
        mock_trace.id = "trace_456"
        mock_client.trace = Mock(return_value=mock_trace)
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        trace_id = tracer.trace_agent_execution(
            agent_name="simple_agent",
            task_id="task_456",
            task="simple task",
            context={},
            model_info={}
        )

        assert trace_id == "trace_456"
        call_metadata = mock_client.trace.call_args[1]["metadata"]
        assert call_metadata["model"] is None
        assert call_metadata["temperature"] is None


class TestLangfuseTracerLLMCall:
    """Test suite for trace_llm_call functionality"""

    def test_trace_llm_call_when_disabled(self):
        """Test trace_llm_call does nothing when disabled"""
        tracer = LangfuseTracer(
            public_key=None,
            secret_key=None
        )

        # Should not raise an error
        tracer.trace_llm_call(
            trace_id="trace_123",
            model="gpt-4",
            prompt="test prompt",
            response="test response",
            tokens_used=100,
            latency_ms=500
        )

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_llm_call_without_trace_id(self, mock_langfuse):
        """Test trace_llm_call does nothing without trace_id"""
        mock_client = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        tracer.trace_llm_call(
            trace_id=None,
            model="gpt-4",
            prompt="test prompt",
            response="test response",
            tokens_used=100,
            latency_ms=500
        )

        mock_client.generation.assert_not_called()

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_llm_call_success(self, mock_langfuse):
        """Test trace_llm_call creates generation with all parameters"""
        mock_client = Mock()
        mock_client.generation = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        metadata = {
            "temperature": 0.8,
            "top_p": 0.95,
            "max_tokens": 2000,
            "seed": 123
        }

        tracer.trace_llm_call(
            trace_id="trace_123",
            model="gpt-4",
            prompt="test prompt",
            response="test response",
            tokens_used=150,
            latency_ms=750,
            metadata=metadata
        )

        mock_client.generation.assert_called_once_with(
            trace_id="trace_123",
            name="llm_call",
            model="gpt-4",
            model_parameters={
                "temperature": 0.8,
                "top_p": 0.95,
                "max_tokens": 2000,
                "seed": 123
            },
            input="test prompt",
            output="test response",
            usage={
                "input": 150,
                "output": 150,
                "total": 150
            },
            metadata={
                "temperature": 0.8,
                "top_p": 0.95,
                "max_tokens": 2000,
                "seed": 123,
                "latency_ms": 750
            }
        )

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_llm_call_without_metadata(self, mock_langfuse):
        """Test trace_llm_call without metadata"""
        mock_client = Mock()
        mock_client.generation = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        tracer.trace_llm_call(
            trace_id="trace_123",
            model="gpt-3.5",
            prompt="test prompt",
            response="test response",
            tokens_used=100,
            latency_ms=500
        )

        call_args = mock_client.generation.call_args[1]
        assert call_args["model_parameters"]["temperature"] is None
        assert call_args["metadata"]["latency_ms"] == 500


class TestLangfuseTracerRAGRetrieval:
    """Test suite for trace_rag_retrieval functionality"""

    def test_trace_rag_retrieval_when_disabled(self):
        """Test trace_rag_retrieval does nothing when disabled"""
        tracer = LangfuseTracer(
            public_key=None,
            secret_key=None
        )

        tracer.trace_rag_retrieval(
            trace_id="trace_123",
            query="test query",
            citations=[],
            top_k=5,
            min_score=0.7
        )

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_rag_retrieval_without_trace_id(self, mock_langfuse):
        """Test trace_rag_retrieval does nothing without trace_id"""
        mock_client = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        tracer.trace_rag_retrieval(
            trace_id=None,
            query="test query",
            citations=[],
            top_k=5,
            min_score=0.7
        )

        mock_client.span.assert_not_called()

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_rag_retrieval_with_citations(self, mock_langfuse):
        """Test trace_rag_retrieval creates span with citations"""
        mock_client = Mock()
        mock_client.span = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        citations = [
            {
                "source": "doc1.pdf",
                "version": "v1.0",
                "score": 0.95,
                "content": "This is a test content " * 20  # Long content
            },
            {
                "source": "doc2.pdf",
                "version": "v2.0",
                "score": 0.85,
                "content": "Another test content"
            },
            {
                "source": "doc3.pdf",
                "version": "v1.5",
                "score": 0.75,
                "content": "Third test content"
            }
        ]

        tracer.trace_rag_retrieval(
            trace_id="trace_123",
            query="test query",
            citations=citations,
            top_k=2,
            min_score=0.8
        )

        mock_client.span.assert_called_once()
        call_args = mock_client.span.call_args[1]

        assert call_args["trace_id"] == "trace_123"
        assert call_args["name"] == "rag_retrieval"
        assert call_args["input"]["query"] == "test query"
        assert call_args["input"]["top_k"] == 2
        assert call_args["input"]["min_score"] == 0.8

        # Check citations are limited to top_k
        assert len(call_args["output"]["citations"]) == 2
        assert call_args["output"]["count"] == 3

        # Check first citation
        first_citation = call_args["output"]["citations"][0]
        assert first_citation["rank"] == 1
        assert first_citation["source"] == "doc1.pdf"
        assert first_citation["version"] == "v1.0"
        assert first_citation["score"] == 0.95
        assert len(first_citation["content_preview"]) <= 200

        # Check metadata
        assert call_args["metadata"]["grounding_quality"] == "sufficient"

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_rag_retrieval_insufficient_citations(self, mock_langfuse):
        """Test trace_rag_retrieval marks insufficient grounding quality"""
        mock_client = Mock()
        mock_client.span = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        citations = [
            {"source": "doc1.pdf", "version": "v1.0", "score": 0.8, "content": "content"}
        ]

        tracer.trace_rag_retrieval(
            trace_id="trace_123",
            query="test query",
            citations=citations,
            top_k=5,
            min_score=0.7
        )

        call_args = mock_client.span.call_args[1]
        assert call_args["metadata"]["grounding_quality"] == "insufficient"

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_rag_retrieval_missing_citation_fields(self, mock_langfuse):
        """Test trace_rag_retrieval handles missing citation fields"""
        mock_client = Mock()
        mock_client.span = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        citations = [
            {},  # Empty citation
            {"source": "doc2.pdf"}  # Partial citation
        ]

        tracer.trace_rag_retrieval(
            trace_id="trace_123",
            query="test query",
            citations=citations,
            top_k=5,
            min_score=0.7
        )

        call_args = mock_client.span.call_args[1]
        first_citation = call_args["output"]["citations"][0]

        assert first_citation["source"] == "unknown"
        assert first_citation["version"] == "unknown"
        assert first_citation["score"] == 0.0
        assert first_citation["content_preview"] == ""


class TestLangfuseTracerToolExecution:
    """Test suite for trace_tool_execution functionality"""

    def test_trace_tool_execution_when_disabled(self):
        """Test trace_tool_execution does nothing when disabled"""
        tracer = LangfuseTracer(
            public_key=None,
            secret_key=None
        )

        tracer.trace_tool_execution(
            trace_id="trace_123",
            tool_name="test_tool",
            inputs={"param": "value"},
            output="result",
            success=True
        )

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_tool_execution_without_trace_id(self, mock_langfuse):
        """Test trace_tool_execution does nothing without trace_id"""
        mock_client = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        tracer.trace_tool_execution(
            trace_id=None,
            tool_name="test_tool",
            inputs={"param": "value"},
            output="result",
            success=True
        )

        mock_client.span.assert_not_called()

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_tool_execution_success(self, mock_langfuse):
        """Test trace_tool_execution for successful execution"""
        mock_client = Mock()
        mock_client.span = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        inputs = {"file": "test.txt", "operation": "read"}
        output = "file contents"

        tracer.trace_tool_execution(
            trace_id="trace_123",
            tool_name="file_reader",
            inputs=inputs,
            output=output,
            success=True
        )

        mock_client.span.assert_called_once_with(
            trace_id="trace_123",
            name="tool.file_reader",
            input=inputs,
            output={"result": output, "success": True, "error": None},
            metadata={
                "tool_type": "file_reader",
                "status": "success"
            }
        )

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_tool_execution_failure(self, mock_langfuse):
        """Test trace_tool_execution for failed execution"""
        mock_client = Mock()
        mock_client.span = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        tracer.trace_tool_execution(
            trace_id="trace_123",
            tool_name="api_call",
            inputs={"url": "https://api.example.com"},
            output=None,
            success=False,
            error="Connection timeout"
        )

        call_args = mock_client.span.call_args[1]
        assert call_args["output"]["success"] is False
        assert call_args["output"]["error"] == "Connection timeout"
        assert call_args["metadata"]["status"] == "failed"


class TestLangfuseTracerApprovalRequest:
    """Test suite for trace_approval_request functionality"""

    def test_trace_approval_request_when_disabled(self):
        """Test trace_approval_request does nothing when disabled"""
        tracer = LangfuseTracer(
            public_key=None,
            secret_key=None
        )

        tracer.trace_approval_request(
            trace_id="trace_123",
            risk_level="high",
            task_description="Delete production database",
            approval_status="rejected"
        )

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_approval_request_without_trace_id(self, mock_langfuse):
        """Test trace_approval_request does nothing without trace_id"""
        mock_client = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        tracer.trace_approval_request(
            trace_id=None,
            risk_level="high",
            task_description="Delete production database",
            approval_status="rejected"
        )

        mock_client.span.assert_not_called()

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_approval_request_approved(self, mock_langfuse):
        """Test trace_approval_request for approved request"""
        mock_client = Mock()
        mock_client.span = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        tracer.trace_approval_request(
            trace_id="trace_123",
            risk_level="medium",
            task_description="Deploy to staging",
            approval_status="approved",
            approved_by="admin@example.com"
        )

        mock_client.span.assert_called_once_with(
            trace_id="trace_123",
            name="human_approval",
            input={"risk_level": "medium", "task": "Deploy to staging"},
            output={"status": "approved", "approved_by": "admin@example.com"},
            metadata={
                "approval_type": "human_in_loop",
                "risk_level": "medium"
            }
        )

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_approval_request_rejected(self, mock_langfuse):
        """Test trace_approval_request for rejected request"""
        mock_client = Mock()
        mock_client.span = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        tracer.trace_approval_request(
            trace_id="trace_123",
            risk_level="high",
            task_description="Delete production database",
            approval_status="rejected"
        )

        call_args = mock_client.span.call_args[1]
        assert call_args["output"]["status"] == "rejected"
        assert call_args["output"]["approved_by"] is None


class TestLangfuseTracerBudgetCheck:
    """Test suite for trace_budget_check functionality"""

    def test_trace_budget_check_when_disabled(self):
        """Test trace_budget_check does nothing when disabled"""
        tracer = LangfuseTracer(
            public_key=None,
            secret_key=None
        )

        tracer.trace_budget_check(
            trace_id="trace_123",
            tokens_used=500,
            budget=1000,
            within_budget=True
        )

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_budget_check_without_trace_id(self, mock_langfuse):
        """Test trace_budget_check does nothing without trace_id"""
        mock_client = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        tracer.trace_budget_check(
            trace_id=None,
            tokens_used=500,
            budget=1000,
            within_budget=True
        )

        mock_client.event.assert_not_called()

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_budget_check_within_budget(self, mock_langfuse):
        """Test trace_budget_check when within budget"""
        mock_client = Mock()
        mock_client.event = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        tracer.trace_budget_check(
            trace_id="trace_123",
            tokens_used=500,
            budget=1000,
            within_budget=True
        )

        mock_client.event.assert_called_once_with(
            trace_id="trace_123",
            name="budget_check",
            metadata={
                "tokens_used": 500,
                "budget": 1000,
                "within_budget": True,
                "utilization_pct": 50.0
            }
        )

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_budget_check_exceeded_budget(self, mock_langfuse):
        """Test trace_budget_check when budget exceeded"""
        mock_client = Mock()
        mock_client.event = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        tracer.trace_budget_check(
            trace_id="trace_123",
            tokens_used=1200,
            budget=1000,
            within_budget=False
        )

        call_args = mock_client.event.call_args[1]
        assert call_args["metadata"]["utilization_pct"] == 120.0
        assert call_args["metadata"]["within_budget"] is False

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_trace_budget_check_zero_budget(self, mock_langfuse):
        """Test trace_budget_check with zero budget"""
        mock_client = Mock()
        mock_client.event = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        tracer.trace_budget_check(
            trace_id="trace_123",
            tokens_used=500,
            budget=0,
            within_budget=False
        )

        call_args = mock_client.event.call_args[1]
        assert call_args["metadata"]["utilization_pct"] == 0


class TestLangfuseTracerFlush:
    """Test suite for flush functionality"""

    def test_flush_when_disabled(self):
        """Test flush does nothing when disabled"""
        tracer = LangfuseTracer(
            public_key=None,
            secret_key=None
        )

        # Should not raise an error
        tracer.flush()

    @patch('app.memory.langfuse_tracer.Langfuse')
    def test_flush_when_enabled(self, mock_langfuse):
        """Test flush calls client.flush when enabled"""
        mock_client = Mock()
        mock_client.flush = Mock()
        mock_langfuse.return_value = mock_client

        tracer = LangfuseTracer(
            public_key="test_public_key",
            secret_key="test_secret_key"
        )

        tracer.flush()

        mock_client.flush.assert_called_once()
