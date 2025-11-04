"""
Temponest SDK - RAG Service Client
"""
from typing import List, Optional, Dict, Any, BinaryIO
from pathlib import Path
from .client import BaseClient, AsyncBaseClient
from .models import (
    Collection,
    Document,
    QueryResult,
    CollectionCreateRequest,
    QueryRequest,
)
from .exceptions import CollectionNotFoundError


class RAGClient:
    """Client for RAG (Retrieval-Augmented Generation) operations"""

    def __init__(self, client: BaseClient):
        self.client = client

    def create_collection(
        self,
        name: str,
        description: Optional[str] = None,
        embedding_model: str = "nomic-embed-text",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> Collection:
        """
        Create a new RAG collection

        Args:
            name: Collection name
            description: Collection description
            embedding_model: Model to use for embeddings
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks

        Returns:
            Created collection

        Raises:
            TemponestAPIError: On API errors
        """
        request = CollectionCreateRequest(
            name=name,
            description=description,
            embedding_model=embedding_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        response = self.client.post("/rag/collections/", json=request.model_dump())
        return Collection(**response)

    def get_collection(self, collection_id: str) -> Collection:
        """
        Get a collection by ID

        Args:
            collection_id: Collection ID

        Returns:
            Collection object

        Raises:
            CollectionNotFoundError: If collection not found
        """
        try:
            response = self.client.get(f"/rag/collections/{collection_id}")
            return Collection(**response)
        except Exception as e:
            if "404" in str(e):
                raise CollectionNotFoundError(f"Collection {collection_id} not found")
            raise

    def list_collections(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> List[Collection]:
        """
        List RAG collections

        Args:
            skip: Number to skip
            limit: Maximum to return
            search: Search query

        Returns:
            List of collections
        """
        params = {"skip": skip, "limit": limit}
        if search:
            params["search"] = search

        response = self.client.get("/rag/collections/", params=params)
        return [Collection(**collection) for collection in response]

    def update_collection(
        self,
        collection_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Collection:
        """
        Update a collection

        Args:
            collection_id: Collection ID
            name: New name
            description: New description

        Returns:
            Updated collection

        Raises:
            CollectionNotFoundError: If collection not found
        """
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description

        try:
            response = self.client.patch(
                f"/rag/collections/{collection_id}",
                json=update_data
            )
            return Collection(**response)
        except Exception as e:
            if "404" in str(e):
                raise CollectionNotFoundError(f"Collection {collection_id} not found")
            raise

    def delete_collection(self, collection_id: str) -> None:
        """
        Delete a collection

        Args:
            collection_id: Collection ID

        Raises:
            CollectionNotFoundError: If collection not found
        """
        try:
            self.client.delete(f"/rag/collections/{collection_id}")
        except Exception as e:
            if "404" in str(e):
                raise CollectionNotFoundError(f"Collection {collection_id} not found")
            raise

    def upload_document(
        self,
        collection_id: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """
        Upload a document to a collection

        Args:
            collection_id: Collection ID
            file_path: Path to the file
            metadata: Optional metadata

        Returns:
            Created document

        Raises:
            CollectionNotFoundError: If collection not found
            FileNotFoundError: If file not found
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, 'rb') as f:
            files = {
                'file': (path.name, f, 'application/octet-stream')
            }
            data = {}
            if metadata:
                data['metadata'] = str(metadata)

            try:
                response = self.client.post(
                    f"/rag/collections/{collection_id}/documents",
                    files=files,
                    data=data
                )
                return Document(**response)
            except Exception as e:
                if "404" in str(e):
                    raise CollectionNotFoundError(f"Collection {collection_id} not found")
                raise

    def upload_documents(
        self,
        collection_id: str,
        file_paths: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        Upload multiple documents to a collection

        Args:
            collection_id: Collection ID
            file_paths: List of file paths
            metadata: Optional metadata for all documents

        Returns:
            List of created documents
        """
        documents = []
        for file_path in file_paths:
            try:
                doc = self.upload_document(collection_id, file_path, metadata)
                documents.append(doc)
            except Exception as e:
                print(f"Failed to upload {file_path}: {e}")
        return documents

    def get_document(self, document_id: str) -> Document:
        """
        Get a document by ID

        Args:
            document_id: Document ID

        Returns:
            Document object
        """
        response = self.client.get(f"/rag/documents/{document_id}")
        return Document(**response)

    def list_documents(
        self,
        collection_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Document]:
        """
        List documents in a collection

        Args:
            collection_id: Collection ID
            skip: Number to skip
            limit: Maximum to return

        Returns:
            List of documents
        """
        params = {"skip": skip, "limit": limit}
        response = self.client.get(
            f"/rag/collections/{collection_id}/documents",
            params=params
        )
        return [Document(**doc) for doc in response]

    def delete_document(self, document_id: str) -> None:
        """
        Delete a document

        Args:
            document_id: Document ID
        """
        self.client.delete(f"/rag/documents/{document_id}")

    def query(
        self,
        collection_id: str,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        """
        Query a RAG collection

        Args:
            collection_id: Collection ID
            query: Query text
            top_k: Number of results to return
            filter: Optional metadata filter

        Returns:
            Query results

        Raises:
            CollectionNotFoundError: If collection not found
        """
        request = QueryRequest(
            query=query,
            top_k=top_k,
            filter=filter,
        )

        try:
            response = self.client.post(
                f"/rag/collections/{collection_id}/query",
                json=request.model_dump()
            )
            return QueryResult(**response)
        except Exception as e:
            if "404" in str(e):
                raise CollectionNotFoundError(f"Collection {collection_id} not found")
            raise


class AsyncRAGClient:
    """Async client for RAG operations"""

    def __init__(self, client: AsyncBaseClient):
        self.client = client

    async def create_collection(
        self,
        name: str,
        description: Optional[str] = None,
        embedding_model: str = "nomic-embed-text",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> Collection:
        """Create a new RAG collection (async)"""
        request = CollectionCreateRequest(
            name=name,
            description=description,
            embedding_model=embedding_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        response = await self.client.post("/rag/collections/", json=request.model_dump())
        return Collection(**response)

    async def get_collection(self, collection_id: str) -> Collection:
        """Get a collection by ID (async)"""
        try:
            response = await self.client.get(f"/rag/collections/{collection_id}")
            return Collection(**response)
        except Exception as e:
            if "404" in str(e):
                raise CollectionNotFoundError(f"Collection {collection_id} not found")
            raise

    async def list_collections(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> List[Collection]:
        """List RAG collections (async)"""
        params = {"skip": skip, "limit": limit}
        if search:
            params["search"] = search

        response = await self.client.get("/rag/collections/", params=params)
        return [Collection(**collection) for collection in response]

    async def update_collection(
        self,
        collection_id: str,
        **kwargs
    ) -> Collection:
        """Update a collection (async)"""
        update_data = {k: v for k, v in kwargs.items() if v is not None}

        try:
            response = await self.client.patch(
                f"/rag/collections/{collection_id}",
                json=update_data
            )
            return Collection(**response)
        except Exception as e:
            if "404" in str(e):
                raise CollectionNotFoundError(f"Collection {collection_id} not found")
            raise

    async def delete_collection(self, collection_id: str) -> None:
        """Delete a collection (async)"""
        try:
            await self.client.delete(f"/rag/collections/{collection_id}")
        except Exception as e:
            if "404" in str(e):
                raise CollectionNotFoundError(f"Collection {collection_id} not found")
            raise

    async def upload_document(
        self,
        collection_id: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """Upload a document to a collection (async)"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, 'rb') as f:
            files = {
                'file': (path.name, f, 'application/octet-stream')
            }
            data = {}
            if metadata:
                data['metadata'] = str(metadata)

            try:
                response = await self.client.post(
                    f"/rag/collections/{collection_id}/documents",
                    files=files,
                    data=data
                )
                return Document(**response)
            except Exception as e:
                if "404" in str(e):
                    raise CollectionNotFoundError(f"Collection {collection_id} not found")
                raise

    async def query(
        self,
        collection_id: str,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        """Query a RAG collection (async)"""
        request = QueryRequest(
            query=query,
            top_k=top_k,
            filter=filter,
        )

        try:
            response = await self.client.post(
                f"/rag/collections/{collection_id}/query",
                json=request.model_dump()
            )
            return QueryResult(**response)
        except Exception as e:
            if "404" in str(e):
                raise CollectionNotFoundError(f"Collection {collection_id} not found")
            raise
