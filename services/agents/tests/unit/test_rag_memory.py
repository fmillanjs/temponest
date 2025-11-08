"""
Unit tests for RAG Memory.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from qdrant_client.http.exceptions import UnexpectedResponse
from app.memory.rag import RAGMemory


class TestRAGMemory:
    """Test suite for RAGMemory"""

    @pytest.fixture
    def rag_memory(self):
        """Create RAGMemory instance"""
        return RAGMemory(
            qdrant_url="http://test-qdrant:6333",
            collection_name="test_collection",
            embedding_model="test-embed-model",
            embedding_dim=384
        )

    def test_init_default_params(self):
        """Test RAGMemory initialization with default parameters"""
        rag = RAGMemory(qdrant_url="http://qdrant:6333")

        assert rag.qdrant_url == "http://qdrant:6333"
        assert rag.collection_name == "agentic_knowledge"
        assert rag.embedding_model == "nomic-embed-text"
        assert rag.embedding_dim == 768
        assert rag.client is None
        assert rag._ollama_url == "http://ollama:11434"

    def test_init_custom_params(self):
        """Test RAGMemory initialization with custom parameters"""
        rag = RAGMemory(
            qdrant_url="http://custom-qdrant:6333",
            collection_name="custom_collection",
            embedding_model="custom-model",
            embedding_dim=512
        )

        assert rag.qdrant_url == "http://custom-qdrant:6333"
        assert rag.collection_name == "custom_collection"
        assert rag.embedding_model == "custom-model"
        assert rag.embedding_dim == 512
        assert rag._ollama_url == "http://custom-ollama:11434"

    @pytest.mark.asyncio
    async def test_initialize_existing_collection(self, rag_memory):
        """Test initialize when collection already exists"""
        mock_client = Mock()
        mock_client.get_collection = Mock(return_value={"name": "test_collection"})

        with patch('app.memory.rag.QdrantClient', return_value=mock_client):
            await rag_memory.initialize()

        assert rag_memory.client is not None
        mock_client.get_collection.assert_called_once_with("test_collection")
        # Should not try to create collection
        assert not hasattr(mock_client, 'create_collection') or not mock_client.create_collection.called

    @pytest.mark.asyncio
    async def test_initialize_create_new_collection(self, rag_memory):
        """Test initialize when collection doesn't exist"""
        mock_client = Mock()
        mock_client.get_collection = Mock(side_effect=Exception("Collection not found"))
        mock_client.create_collection = Mock()

        with patch('app.memory.rag.QdrantClient', return_value=mock_client):
            await rag_memory.initialize()

        assert rag_memory.client is not None
        mock_client.create_collection.assert_called_once()
        # Verify collection creation parameters
        call_args = mock_client.create_collection.call_args
        assert call_args[1]["collection_name"] == "test_collection"

    def test_is_healthy_no_client(self, rag_memory):
        """Test is_healthy when client is not initialized"""
        assert rag_memory.is_healthy() is False

    def test_is_healthy_success(self, rag_memory):
        """Test is_healthy when Qdrant is available"""
        mock_client = Mock()
        mock_client.get_collections = Mock(return_value=[])
        rag_memory.client = mock_client

        assert rag_memory.is_healthy() is True
        mock_client.get_collections.assert_called_once()

    def test_is_healthy_failure(self, rag_memory):
        """Test is_healthy when Qdrant fails"""
        mock_client = Mock()
        mock_client.get_collections = Mock(side_effect=Exception("Connection failed"))
        rag_memory.client = mock_client

        assert rag_memory.is_healthy() is False

    @pytest.mark.asyncio
    async def test_get_collection_size_no_client(self, rag_memory):
        """Test get_collection_size when client is not initialized"""
        size = await rag_memory.get_collection_size()
        assert size == 0

    @pytest.mark.asyncio
    async def test_get_collection_size_success(self, rag_memory):
        """Test get_collection_size when collection exists"""
        mock_collection_info = Mock()
        mock_collection_info.points_count = 42

        mock_client = Mock()
        mock_client.get_collection = Mock(return_value=mock_collection_info)
        rag_memory.client = mock_client

        size = await rag_memory.get_collection_size()
        assert size == 42
        mock_client.get_collection.assert_called_once_with("test_collection")

    @pytest.mark.asyncio
    async def test_get_collection_size_error(self, rag_memory):
        """Test get_collection_size when error occurs"""
        mock_client = Mock()
        mock_client.get_collection = Mock(side_effect=Exception("Error"))
        rag_memory.client = mock_client

        size = await rag_memory.get_collection_size()
        assert size == 0

    @pytest.mark.asyncio
    async def test_embed_text_success(self, rag_memory):
        """Test embed_text generates embeddings"""
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(return_value={
            "embedding": [0.1, 0.2, 0.3, 0.4]
        })

        with patch('httpx.AsyncClient') as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__.return_value = mock_client_instance

            embedding = await rag_memory.embed_text("test text")

        assert embedding == [0.1, 0.2, 0.3, 0.4]
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        assert "test-ollama:11434/api/embeddings" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_retrieve_not_initialized(self, rag_memory):
        """Test retrieve raises error when not initialized"""
        with pytest.raises(RuntimeError, match="RAGMemory not initialized"):
            await rag_memory.retrieve("test query")

    @pytest.mark.asyncio
    async def test_retrieve_success(self, rag_memory):
        """Test retrieve returns formatted results"""
        # Mock embedding
        mock_embedding = [0.1] * 384

        # Mock search results
        mock_result_1 = Mock()
        mock_result_1.score = 0.95
        mock_result_1.payload = {
            "content": "Document 1 content",
            "source": "doc1.md",
            "version": "v1.0",
            "product": "ProductA",
            "date": "2025-01-01",
            "metadata": {"author": "Alice"}
        }

        mock_result_2 = Mock()
        mock_result_2.score = 0.87
        mock_result_2.payload = {
            "content": "Document 2 content",
            "source": "doc2.md",
            "version": "v2.0"
        }

        mock_client = Mock()
        mock_client.search = Mock(return_value=[mock_result_1, mock_result_2])
        rag_memory.client = mock_client

        # Mock embed_text
        rag_memory.embed_text = AsyncMock(return_value=mock_embedding)

        results = await rag_memory.retrieve(
            query="test query",
            top_k=5,
            min_score=0.7
        )

        assert len(results) == 2

        # Check first result
        assert results[0]["content"] == "Document 1 content"
        assert results[0]["source"] == "doc1.md"
        assert results[0]["version"] == "v1.0"
        assert results[0]["product"] == "ProductA"
        assert results[0]["date"] == "2025-01-01"
        assert results[0]["score"] == 0.95
        assert results[0]["metadata"] == {"author": "Alice"}

        # Check second result (missing optional fields)
        assert results[1]["content"] == "Document 2 content"
        assert results[1]["source"] == "doc2.md"
        assert results[1]["version"] == "v2.0"
        assert results[1]["product"] == ""
        assert results[1]["date"] == ""
        assert results[1]["score"] == 0.87

        # Verify search was called correctly
        mock_client.search.assert_called_once()
        call_args = mock_client.search.call_args[1]
        assert call_args["collection_name"] == "test_collection"
        assert call_args["query_vector"] == mock_embedding
        assert call_args["limit"] == 5
        assert call_args["score_threshold"] == 0.7

    @pytest.mark.asyncio
    async def test_retrieve_with_filters(self, rag_memory):
        """Test retrieve with metadata filters"""
        mock_embedding = [0.1] * 384

        mock_client = Mock()
        mock_client.search = Mock(return_value=[])
        rag_memory.client = mock_client
        rag_memory.embed_text = AsyncMock(return_value=mock_embedding)

        await rag_memory.retrieve(
            query="test query",
            top_k=3,
            min_score=0.8,
            filters={"product": "ProductA", "version": "v1.0"}
        )

        # Verify filter was applied
        call_args = mock_client.search.call_args[1]
        assert call_args["query_filter"] is not None

    @pytest.mark.asyncio
    async def test_retrieve_empty_results(self, rag_memory):
        """Test retrieve with no results"""
        mock_client = Mock()
        mock_client.search = Mock(return_value=[])
        rag_memory.client = mock_client
        rag_memory.embed_text = AsyncMock(return_value=[0.1] * 384)

        results = await rag_memory.retrieve("no match query")

        assert results == []

    @pytest.mark.asyncio
    async def test_add_documents_not_initialized(self, rag_memory):
        """Test add_documents raises error when not initialized"""
        with pytest.raises(RuntimeError, match="RAGMemory not initialized"):
            await rag_memory.add_documents([{"content": "test"}])

    @pytest.mark.asyncio
    async def test_add_documents_success(self, rag_memory):
        """Test add_documents successfully adds documents"""
        documents = [
            {
                "content": "Document 1",
                "source": "doc1.md",
                "version": "v1.0",
                "product": "ProductA"
            },
            {
                "content": "Document 2",
                "source": "doc2.md"
            }
        ]

        mock_client = Mock()
        mock_client.upsert = Mock()
        rag_memory.client = mock_client

        # Mock embed_text
        rag_memory.embed_text = AsyncMock(side_effect=[[0.1] * 384, [0.2] * 384])

        await rag_memory.add_documents(documents)

        # Verify upsert was called
        mock_client.upsert.assert_called_once()
        call_args = mock_client.upsert.call_args[1]
        assert call_args["collection_name"] == "test_collection"
        assert len(call_args["points"]) == 2

    @pytest.mark.asyncio
    async def test_add_documents_batching(self, rag_memory):
        """Test add_documents handles batching correctly"""
        # Create 150 documents to test batching (batch_size=100)
        documents = [
            {"content": f"Document {i}", "source": "docs.md"}
            for i in range(150)
        ]

        mock_client = Mock()
        mock_client.upsert = Mock()
        rag_memory.client = mock_client

        # Mock embed_text to return different embeddings
        rag_memory.embed_text = AsyncMock(return_value=[0.1] * 384)

        await rag_memory.add_documents(documents, batch_size=100)

        # Should be called twice (100 + 50)
        assert mock_client.upsert.call_count == 2

    @pytest.mark.asyncio
    async def test_delete_by_source_not_initialized(self, rag_memory):
        """Test delete_by_source raises error when not initialized"""
        with pytest.raises(RuntimeError, match="RAGMemory not initialized"):
            await rag_memory.delete_by_source("test.md")

    @pytest.mark.asyncio
    async def test_delete_by_source_success(self, rag_memory):
        """Test delete_by_source successfully deletes documents"""
        mock_client = Mock()
        mock_client.delete = Mock()
        rag_memory.client = mock_client

        await rag_memory.delete_by_source("old_docs.md")

        # Verify delete was called
        mock_client.delete.assert_called_once()
        call_args = mock_client.delete.call_args[1]
        assert call_args["collection_name"] == "test_collection"
        # Verify filter contains source matching
        assert call_args["points_selector"] is not None
