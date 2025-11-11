"""
Unit tests for RAGClient
"""
import pytest
from unittest.mock import Mock, patch
from temponest_sdk.rag import RAGClient
from temponest_sdk.client import BaseClient
from temponest_sdk.models import Collection, Document, QueryResult
from temponest_sdk.exceptions import CollectionNotFoundError


class TestRAGClientCollections:
    """Test collection management"""

    def test_create_collection_minimal(self, clean_env, mock_collection_data):
        """Test creating collection with minimal parameters"""
        with patch.object(BaseClient, 'post', return_value=mock_collection_data):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            collection = rag_client.create_collection(name="Documentation")

            assert isinstance(collection, Collection)
            assert collection.id == "collection-123"
            assert collection.name == "Documentation"

    def test_create_collection_full(self, clean_env, mock_collection_data):
        """Test creating collection with all parameters"""
        with patch.object(BaseClient, 'post', return_value=mock_collection_data):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            collection = rag_client.create_collection(
                name="Documentation",
                description="Product docs",
                embedding_model="nomic-embed-text",
                chunk_size=500,
                chunk_overlap=100
            )

            assert collection.id == "collection-123"

    def test_get_collection_success(self, clean_env, mock_collection_data):
        """Test getting collection by ID"""
        with patch.object(BaseClient, 'get', return_value=mock_collection_data):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            collection = rag_client.get_collection("collection-123")

            assert isinstance(collection, Collection)
            assert collection.id == "collection-123"

    def test_get_collection_not_found(self, clean_env):
        """Test getting non-existent collection"""
        with patch.object(BaseClient, 'get', side_effect=Exception("404")):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            with pytest.raises(CollectionNotFoundError):
                rag_client.get_collection("collection-123")

    def test_list_collections(self, clean_env, mock_collection_data):
        """Test listing collections"""
        with patch.object(BaseClient, 'get', return_value=[mock_collection_data]):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            collections = rag_client.list_collections()

            assert len(collections) == 1
            assert isinstance(collections[0], Collection)

    def test_list_collections_with_search(self, clean_env, mock_collection_data):
        """Test listing collections with search"""
        with patch.object(BaseClient, 'get', return_value=[mock_collection_data]) as mock_get:
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            collections = rag_client.list_collections(search="docs")

            call_args = mock_get.call_args
            assert call_args[1]['params']['search'] == "docs"

    def test_delete_collection(self, clean_env):
        """Test deleting collection"""
        with patch.object(BaseClient, 'delete', return_value=None):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            rag_client.delete_collection("collection-123")
            # No exception means success


class TestRAGClientDocuments:
    """Test document management"""

    def test_add_document_text(self, clean_env, mock_document_data):
        """Test adding document from text"""
        with patch.object(BaseClient, 'post', return_value=mock_document_data):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            document = rag_client.add_document(
                collection_id="collection-123",
                content="Test content",
                metadata={"source": "test"}
            )

            assert isinstance(document, Document)
            assert document.id == "doc-123"

    def test_add_document_file(self, clean_env, mock_document_data):
        """Test adding document from file"""
        with patch.object(BaseClient, 'post', return_value=mock_document_data):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            # Mock file object
            mock_file = Mock()
            document = rag_client.upload_document(
                collection_id="collection-123",
                file=mock_file,
                filename="test.txt"
            )

            assert document.id == "doc-123"

    def test_get_document(self, clean_env, mock_document_data):
        """Test getting document by ID"""
        with patch.object(BaseClient, 'get', return_value=mock_document_data):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            document = rag_client.get_document("doc-123")

            assert isinstance(document, Document)
            assert document.id == "doc-123"

    def test_list_documents(self, clean_env, mock_document_data):
        """Test listing documents in collection"""
        with patch.object(BaseClient, 'get', return_value=[mock_document_data]):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            documents = rag_client.list_documents("collection-123")

            assert len(documents) == 1
            assert isinstance(documents[0], Document)

    def test_delete_document(self, clean_env):
        """Test deleting document"""
        with patch.object(BaseClient, 'delete', return_value=None):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            rag_client.delete_document("doc-123")
            # No exception means success


class TestRAGClientQuery:
    """Test query operations"""

    def test_query_collection(self, clean_env, mock_query_result_data):
        """Test querying a collection"""
        with patch.object(BaseClient, 'post', return_value=mock_query_result_data):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            result = rag_client.query(
                collection_id="collection-123",
                query="How to install?"
            )

            assert isinstance(result, QueryResult)
            assert result.query == "How to install?"
            assert len(result.chunks) == 2

    def test_query_with_limit(self, clean_env, mock_query_result_data):
        """Test querying with result limit"""
        with patch.object(BaseClient, 'post', return_value=mock_query_result_data) as mock_post:
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            result = rag_client.query(
                collection_id="collection-123",
                query="How to install?",
                top_k=5
            )

            call_args = mock_post.call_args
            assert call_args[1]['json']['top_k'] == 5

    def test_query_with_filters(self, clean_env, mock_query_result_data):
        """Test querying with metadata filters"""
        with patch.object(BaseClient, 'post', return_value=mock_query_result_data) as mock_post:
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            result = rag_client.query(
                collection_id="collection-123",
                query="How to install?",
                filters={"category": "guide"}
            )

            call_args = mock_post.call_args
            assert call_args[1]['json']['filters'] == {"category": "guide"}
