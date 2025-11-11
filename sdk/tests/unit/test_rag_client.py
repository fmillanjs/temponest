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

    def test_update_collection(self, clean_env, mock_collection_data):
        """Test updating collection"""
        updated_data = {**mock_collection_data, "name": "Updated Collection"}
        with patch.object(BaseClient, 'patch', return_value=updated_data):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            collection = rag_client.update_collection(
                "collection-123",
                name="Updated Collection",
                description="New description"
            )

            assert collection.name == "Updated Collection"

    def test_update_collection_not_found(self, clean_env):
        """Test updating non-existent collection"""
        with patch.object(BaseClient, 'patch', side_effect=Exception("404")):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            with pytest.raises(CollectionNotFoundError):
                rag_client.update_collection("collection-123", name="New Name")

    def test_delete_collection(self, clean_env):
        """Test deleting collection"""
        with patch.object(BaseClient, 'delete', return_value=None):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            rag_client.delete_collection("collection-123")
            # No exception means success

    def test_delete_collection_not_found(self, clean_env):
        """Test deleting non-existent collection"""
        with patch.object(BaseClient, 'delete', side_effect=Exception("404")):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            with pytest.raises(CollectionNotFoundError):
                rag_client.delete_collection("collection-123")

    def test_upload_documents(self, clean_env, mock_document_data):
        """Test uploading multiple documents"""
        with patch('builtins.open', create=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch.object(BaseClient, 'post', return_value=mock_document_data):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            documents = rag_client.upload_documents(
                collection_id="collection-123",
                file_paths=["/tmp/file1.txt", "/tmp/file2.txt"]
            )

            assert len(documents) == 2


class TestRAGClientDocuments:
    """Test document management"""

    def test_add_document_text(self, clean_env, mock_document_data):
        """Test uploading document from file path"""
        with patch('builtins.open', create=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch.object(BaseClient, 'post', return_value=mock_document_data):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            document = rag_client.upload_document(
                collection_id="collection-123",
                file_path="/tmp/test.txt",
                metadata={"source": "test"}
            )

            assert isinstance(document, Document)
            assert document.id == "doc-123"

    def test_add_document_file(self, clean_env, mock_document_data):
        """Test uploading document with metadata"""
        with patch('builtins.open', create=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch.object(BaseClient, 'post', return_value=mock_document_data):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            document = rag_client.upload_document(
                collection_id="collection-123",
                file_path="/tmp/test.pdf"
            )

            assert document.id == "doc-123"

    def test_upload_document_file_not_found(self, clean_env):
        """Test uploading non-existent file"""
        with patch('pathlib.Path.exists', return_value=False):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            with pytest.raises(FileNotFoundError):
                rag_client.upload_document(
                    collection_id="collection-123",
                    file_path="/nonexistent/file.txt"
                )

    def test_upload_document_collection_not_found(self, clean_env):
        """Test uploading to non-existent collection"""
        with patch('builtins.open', create=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch.object(BaseClient, 'post', side_effect=Exception("404")):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            with pytest.raises(CollectionNotFoundError):
                rag_client.upload_document(
                    collection_id="collection-123",
                    file_path="/tmp/test.txt"
                )

    def test_upload_documents_with_error(self, clean_env, mock_document_data):
        """Test uploading multiple documents with one failure"""
        def side_effect(*args, **kwargs):
            if "/tmp/file2.txt" in str(args):
                raise Exception("Upload failed")
            return mock_document_data

        with patch('builtins.open', create=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch.object(RAGClient, 'upload_document', side_effect=side_effect):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            # Should handle errors gracefully and return uploaded docs
            documents = rag_client.upload_documents(
                collection_id="collection-123",
                file_paths=["/tmp/file1.txt", "/tmp/file2.txt"]
            )

            # Only one document should succeed (mocked)
            assert len(documents) == 1

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
                filter={"category": "guide"}
            )

            call_args = mock_post.call_args
            assert call_args[1]['json']['filter'] == {"category": "guide"}

    def test_query_collection_not_found(self, clean_env):
        """Test querying non-existent collection"""
        with patch.object(BaseClient, 'post', side_effect=Exception("404")):
            client = BaseClient(base_url="http://test.com")
            rag_client = RAGClient(client)

            with pytest.raises(CollectionNotFoundError):
                rag_client.query(
                    collection_id="collection-123",
                    query="How to install?"
                )


class TestAsyncRAGClient:
    """Test async RAG client"""

    @pytest.mark.asyncio
    async def test_async_create_collection(self, clean_env, mock_collection_data):
        """Test creating collection (async)"""
        from temponest_sdk.rag import AsyncRAGClient
        from temponest_sdk.client import AsyncBaseClient

        with patch.object(AsyncBaseClient, 'post', return_value=mock_collection_data):
            client = AsyncBaseClient(base_url="http://test.com", auth_token="test-token")
            rag_client = AsyncRAGClient(client)

            collection = await rag_client.create_collection(
                name="Documentation",
                description="Product docs",
                embedding_model="nomic-embed-text",
                chunk_size=500,
                chunk_overlap=100
            )

            assert isinstance(collection, Collection)
            assert collection.id == "collection-123"

    @pytest.mark.asyncio
    async def test_async_get_collection(self, clean_env, mock_collection_data):
        """Test getting collection (async)"""
        from temponest_sdk.rag import AsyncRAGClient
        from temponest_sdk.client import AsyncBaseClient

        with patch.object(AsyncBaseClient, 'get', return_value=mock_collection_data):
            client = AsyncBaseClient(base_url="http://test.com", auth_token="test-token")
            rag_client = AsyncRAGClient(client)

            collection = await rag_client.get_collection("collection-123")

            assert isinstance(collection, Collection)
            assert collection.id == "collection-123"

    @pytest.mark.asyncio
    async def test_async_get_collection_not_found(self, clean_env):
        """Test getting non-existent collection (async)"""
        from temponest_sdk.rag import AsyncRAGClient
        from temponest_sdk.client import AsyncBaseClient

        with patch.object(AsyncBaseClient, 'get', side_effect=Exception("404")):
            client = AsyncBaseClient(base_url="http://test.com", auth_token="test-token")
            rag_client = AsyncRAGClient(client)

            with pytest.raises(CollectionNotFoundError):
                await rag_client.get_collection("collection-123")

    @pytest.mark.asyncio
    async def test_async_list_collections(self, clean_env, mock_collection_data):
        """Test listing collections (async)"""
        from temponest_sdk.rag import AsyncRAGClient
        from temponest_sdk.client import AsyncBaseClient

        with patch.object(AsyncBaseClient, 'get', return_value=[mock_collection_data]):
            client = AsyncBaseClient(base_url="http://test.com", auth_token="test-token")
            rag_client = AsyncRAGClient(client)

            collections = await rag_client.list_collections()

            assert len(collections) == 1
            assert isinstance(collections[0], Collection)

    @pytest.mark.asyncio
    async def test_async_list_collections_with_search(self, clean_env, mock_collection_data):
        """Test listing collections with search (async)"""
        from temponest_sdk.rag import AsyncRAGClient
        from temponest_sdk.client import AsyncBaseClient

        with patch.object(AsyncBaseClient, 'get', return_value=[mock_collection_data]) as mock_get:
            client = AsyncBaseClient(base_url="http://test.com", auth_token="test-token")
            rag_client = AsyncRAGClient(client)

            collections = await rag_client.list_collections(search="docs")

            call_args = mock_get.call_args
            assert call_args[1]['params']['search'] == "docs"

    @pytest.mark.asyncio
    async def test_async_update_collection(self, clean_env, mock_collection_data):
        """Test updating collection (async)"""
        from temponest_sdk.rag import AsyncRAGClient
        from temponest_sdk.client import AsyncBaseClient

        updated_data = {**mock_collection_data, "name": "Updated Collection"}
        with patch.object(AsyncBaseClient, 'patch', return_value=updated_data):
            client = AsyncBaseClient(base_url="http://test.com", auth_token="test-token")
            rag_client = AsyncRAGClient(client)

            collection = await rag_client.update_collection(
                "collection-123",
                name="Updated Collection",
                description="New description"
            )

            assert collection.name == "Updated Collection"

    @pytest.mark.asyncio
    async def test_async_update_collection_not_found(self, clean_env):
        """Test updating non-existent collection (async)"""
        from temponest_sdk.rag import AsyncRAGClient
        from temponest_sdk.client import AsyncBaseClient

        with patch.object(AsyncBaseClient, 'patch', side_effect=Exception("404")):
            client = AsyncBaseClient(base_url="http://test.com", auth_token="test-token")
            rag_client = AsyncRAGClient(client)

            with pytest.raises(CollectionNotFoundError):
                await rag_client.update_collection("collection-123", name="New Name")

    @pytest.mark.asyncio
    async def test_async_delete_collection(self, clean_env):
        """Test deleting collection (async)"""
        from temponest_sdk.rag import AsyncRAGClient
        from temponest_sdk.client import AsyncBaseClient

        with patch.object(AsyncBaseClient, 'delete', return_value=None):
            client = AsyncBaseClient(base_url="http://test.com", auth_token="test-token")
            rag_client = AsyncRAGClient(client)

            await rag_client.delete_collection("collection-123")
            # No exception means success

    @pytest.mark.asyncio
    async def test_async_delete_collection_not_found(self, clean_env):
        """Test deleting non-existent collection (async)"""
        from temponest_sdk.rag import AsyncRAGClient
        from temponest_sdk.client import AsyncBaseClient

        with patch.object(AsyncBaseClient, 'delete', side_effect=Exception("404")):
            client = AsyncBaseClient(base_url="http://test.com", auth_token="test-token")
            rag_client = AsyncRAGClient(client)

            with pytest.raises(CollectionNotFoundError):
                await rag_client.delete_collection("collection-123")

    @pytest.mark.asyncio
    async def test_async_upload_document(self, clean_env, mock_document_data):
        """Test uploading document (async)"""
        from temponest_sdk.rag import AsyncRAGClient
        from temponest_sdk.client import AsyncBaseClient

        with patch('builtins.open', create=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch.object(AsyncBaseClient, 'post', return_value=mock_document_data):
            client = AsyncBaseClient(base_url="http://test.com", auth_token="test-token")
            rag_client = AsyncRAGClient(client)

            document = await rag_client.upload_document(
                collection_id="collection-123",
                file_path="/tmp/test.txt",
                metadata={"source": "test"}
            )

            assert isinstance(document, Document)
            assert document.id == "doc-123"

    @pytest.mark.asyncio
    async def test_async_upload_document_file_not_found(self, clean_env):
        """Test uploading non-existent file (async)"""
        from temponest_sdk.rag import AsyncRAGClient
        from temponest_sdk.client import AsyncBaseClient

        with patch('pathlib.Path.exists', return_value=False):
            client = AsyncBaseClient(base_url="http://test.com", auth_token="test-token")
            rag_client = AsyncRAGClient(client)

            with pytest.raises(FileNotFoundError):
                await rag_client.upload_document(
                    collection_id="collection-123",
                    file_path="/nonexistent/file.txt"
                )

    @pytest.mark.asyncio
    async def test_async_upload_document_collection_not_found(self, clean_env):
        """Test uploading to non-existent collection (async)"""
        from temponest_sdk.rag import AsyncRAGClient
        from temponest_sdk.client import AsyncBaseClient

        with patch('builtins.open', create=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch.object(AsyncBaseClient, 'post', side_effect=Exception("404")):
            client = AsyncBaseClient(base_url="http://test.com", auth_token="test-token")
            rag_client = AsyncRAGClient(client)

            with pytest.raises(CollectionNotFoundError):
                await rag_client.upload_document(
                    collection_id="collection-123",
                    file_path="/tmp/test.txt"
                )

    @pytest.mark.asyncio
    async def test_async_query(self, clean_env, mock_query_result_data):
        """Test querying collection (async)"""
        from temponest_sdk.rag import AsyncRAGClient
        from temponest_sdk.client import AsyncBaseClient

        with patch.object(AsyncBaseClient, 'post', return_value=mock_query_result_data):
            client = AsyncBaseClient(base_url="http://test.com", auth_token="test-token")
            rag_client = AsyncRAGClient(client)

            result = await rag_client.query(
                collection_id="collection-123",
                query="How to install?",
                top_k=5,
                filter={"category": "guide"}
            )

            assert isinstance(result, QueryResult)
            assert result.query == "How to install?"

    @pytest.mark.asyncio
    async def test_async_query_not_found(self, clean_env):
        """Test querying non-existent collection (async)"""
        from temponest_sdk.rag import AsyncRAGClient
        from temponest_sdk.client import AsyncBaseClient

        with patch.object(AsyncBaseClient, 'post', side_effect=Exception("404")):
            client = AsyncBaseClient(base_url="http://test.com", auth_token="test-token")
            rag_client = AsyncRAGClient(client)

            with pytest.raises(CollectionNotFoundError):
                await rag_client.query(
                    collection_id="collection-123",
                    query="How to install?"
                )
