"""
Pytest configuration and shared fixtures for Ingestion Service tests.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from typing import Generator

# Set test environment variables
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
os.environ["EMBEDDING_MODEL"] = "nomic-embed-text"
os.environ["WATCH_DIR"] = "/tmp/test_documents"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_text_file(temp_dir):
    """Create a sample text file"""
    file_path = temp_dir / "test.txt"
    content = "This is a test document.\nIt has multiple lines.\nUsed for testing text extraction."
    file_path.write_text(content)
    return str(file_path), content


@pytest.fixture
def sample_md_file(temp_dir):
    """Create a sample markdown file"""
    file_path = temp_dir / "test.md"
    content = "# Test Document\n\nThis is **bold** text.\n\n## Section 2\n\nWith some content."
    file_path.write_text(content)
    return str(file_path), content


@pytest.fixture
def sample_long_text():
    """Generate a long text for chunking tests"""
    return "Lorem ipsum dolor sit amet. " * 100  # ~2800 characters


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client"""
    client = MagicMock()

    # Mock collections response
    mock_collections = MagicMock()
    mock_collections.collections = []
    client.get_collections.return_value = mock_collections

    # Mock create_collection
    client.create_collection = MagicMock()

    # Mock upsert
    client.upsert = MagicMock()

    # Mock get_collection
    mock_collection_info = MagicMock()
    mock_collection_info.points_count = 42
    client.get_collection.return_value = mock_collection_info

    return client


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response for embeddings"""
    return {
        "embedding": [0.1] * 768  # 768-dimensional embedding
    }


@pytest.fixture
async def mock_httpx_client(mock_ollama_response):
    """Mock httpx AsyncClient for Ollama requests"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value=mock_ollama_response)
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=mock_response)

    return mock_client


@pytest.fixture
def sample_embedding():
    """Sample embedding vector"""
    return [0.1, 0.2, 0.3] * 256  # 768 dimensions
