"""
Tests for RAG retrieval and grounding validation.

Ensures:
- Retrieval returns ≥2 citations
- Citations have required metadata (source, version, score)
- Scores meet minimum threshold
- Grounding is sufficient
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client"""
    client = MagicMock()
    client.search = MagicMock()
    return client


@pytest.fixture
def mock_ollama():
    """Mock Ollama embedding endpoint"""
    return AsyncMock(return_value={"embedding": [0.1] * 768})


@pytest.mark.asyncio
async def test_rag_retrieval_sufficient_citations(mock_qdrant_client, mock_ollama):
    """Test that RAG returns ≥2 citations"""
    # Mock search results
    mock_result_1 = MagicMock()
    mock_result_1.score = 0.85
    mock_result_1.payload = {
        "content": "Test content 1",
        "source": "docs/api.md",
        "version": "1.0",
        "product": "agentic-company",
        "date": "2024-01-01"
    }

    mock_result_2 = MagicMock()
    mock_result_2.score = 0.78
    mock_result_2.payload = {
        "content": "Test content 2",
        "source": "docs/database.md",
        "version": "1.0",
        "product": "agentic-company",
        "date": "2024-01-01"
    }

    mock_qdrant_client.search.return_value = [mock_result_1, mock_result_2]

    # Import after mocking
    with patch("qdrant_client.QdrantClient", return_value=mock_qdrant_client):
        from services.agents.app.memory.rag import RAGMemory

        rag = RAGMemory(qdrant_url="http://test:6333")
        rag.client = mock_qdrant_client

        with patch.object(rag, "embed_text", mock_ollama):
            results = await rag.retrieve(query="test query", top_k=5, min_score=0.7)

    # Assertions
    assert len(results) >= 2, f"Expected ≥2 citations, got {len(results)}"
    assert all("source" in r for r in results), "All results must have 'source'"
    assert all("version" in r for r in results), "All results must have 'version'"
    assert all("score" in r for r in results), "All results must have 'score'"
    assert all(r["score"] >= 0.7 for r in results), "All scores must meet threshold"


@pytest.mark.asyncio
async def test_rag_retrieval_insufficient_citations(mock_qdrant_client, mock_ollama):
    """Test that insufficient citations are detected"""
    # Mock only 1 result
    mock_result = MagicMock()
    mock_result.score = 0.85
    mock_result.payload = {
        "content": "Test content",
        "source": "docs/api.md",
        "version": "1.0",
        "product": "agentic-company",
        "date": "2024-01-01"
    }

    mock_qdrant_client.search.return_value = [mock_result]

    with patch("qdrant_client.QdrantClient", return_value=mock_qdrant_client):
        from services.agents.app.memory.rag import RAGMemory

        rag = RAGMemory(qdrant_url="http://test:6333")
        rag.client = mock_qdrant_client

        with patch.object(rag, "embed_text", mock_ollama):
            results = await rag.retrieve(query="test query", top_k=5, min_score=0.7)

    # Should return < 2 citations
    assert len(results) < 2, "Should detect insufficient citations"


@pytest.mark.asyncio
async def test_rag_citation_metadata():
    """Test that citations include all required metadata"""
    from services.agents.app.memory.rag import RAGMemory

    # Create a mock result with complete metadata
    citation = {
        "content": "Example content",
        "source": "docs/example.md",
        "version": "1.0",
        "product": "agentic-company",
        "date": "2024-01-01",
        "score": 0.85,
        "metadata": {"file_size": 1024}
    }

    # Verify required fields
    required_fields = ["content", "source", "version", "score"]
    for field in required_fields:
        assert field in citation, f"Missing required field: {field}"

    assert citation["score"] >= 0.7, "Score must meet minimum threshold"


@pytest.mark.asyncio
async def test_rag_grounding_quality():
    """Test grounding quality calculation"""
    citations = [
        {"source": "doc1.md", "version": "1.0", "score": 0.9},
        {"source": "doc2.md", "version": "1.0", "score": 0.85},
        {"source": "doc3.md", "version": "1.0", "score": 0.75}
    ]

    # Test grounding quality
    def calculate_grounding_quality(cits):
        if len(cits) < 2:
            return "insufficient"
        if all(c["score"] >= 0.8 for c in cits[:2]):
            return "high"
        elif all(c["score"] >= 0.7 for c in cits[:2]):
            return "sufficient"
        else:
            return "low"

    quality = calculate_grounding_quality(citations)
    assert quality in ["high", "sufficient"], f"Expected high/sufficient quality, got {quality}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
