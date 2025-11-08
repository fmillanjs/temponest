"""
RAG Memory - Qdrant-based retrieval augmented generation.
Handles document retrieval with citations and metadata.
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import UnexpectedResponse
import httpx


class RAGMemory:
    """RAG memory backed by Qdrant vector database"""

    def __init__(
        self,
        qdrant_url: str,
        collection_name: str = "agentic_knowledge",
        embedding_model: str = "nomic-embed-text",
        embedding_dim: int = 768
    ):
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.embedding_dim = embedding_dim
        self.client: Optional[QdrantClient] = None
        self._ollama_url = qdrant_url.replace(":6333", ":11434").replace("qdrant", "ollama")

    async def initialize(self):
        """Initialize Qdrant client and create collection if needed"""
        self.client = QdrantClient(url=self.qdrant_url, timeout=30)

        # Create collection if it doesn't exist
        try:
            self.client.get_collection(self.collection_name)
            print(f"✅ Collection '{self.collection_name}' exists")
        except (UnexpectedResponse, Exception):
            print(f"📝 Creating collection '{self.collection_name}'...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Collection '{self.collection_name}' created")

    def is_healthy(self) -> bool:
        """Check if Qdrant is healthy"""
        try:
            if not self.client:
                return False
            self.client.get_collections()
            return True
        except Exception:
            return False

    async def get_collection_size(self) -> int:
        """Get number of documents in collection"""
        if not self.client:
            return 0
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count
        except Exception:
            return 0

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text using Ollama"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._ollama_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents with citations.

        Returns list of dicts with:
        - content: document text
        - source: source file/URL
        - version: document version
        - product: product name (if applicable)
        - date: document date
        - score: similarity score
        """
        if not self.client:
            raise RuntimeError("RAGMemory not initialized")

        # Generate query embedding
        query_vector = await self.embed_text(query)

        # Build filter if provided
        search_filter = None
        if filters:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filters.items()
            ]
            search_filter = Filter(must=conditions)

        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=min_score,
            query_filter=search_filter
        )

        # Format results
        documents = []
        for result in results:
            payload = result.payload or {}
            documents.append({
                "content": payload.get("content", ""),
                "source": payload.get("source", "unknown"),
                "version": payload.get("version", "unknown"),
                "product": payload.get("product", ""),
                "date": payload.get("date", ""),
                "score": result.score,
                "metadata": payload.get("metadata", {})
            })

        return documents

    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ):
        """
        Add documents to the collection.

        Each document should have:
        - content: text content
        - source: source identifier
        - version: version string
        - product: optional product name
        - date: optional date
        - metadata: optional additional metadata
        """
        if not self.client:
            raise RuntimeError("RAGMemory not initialized")

        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            points = []

            for idx, doc in enumerate(batch):
                # Generate embedding
                embedding = await self.embed_text(doc["content"])

                # Create point - generate ID if not provided
                point_id = doc.get("id") if doc.get("id") is not None else (i + idx)

                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "content": doc["content"],
                        "source": doc.get("source", "unknown"),
                        "version": doc.get("version", "1.0"),
                        "product": doc.get("product", ""),
                        "date": doc.get("date", ""),
                        "metadata": doc.get("metadata", {})
                    }
                )
                points.append(point)

            # Upsert batch
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

        print(f"✅ Added {len(documents)} documents to '{self.collection_name}'")

    async def delete_by_source(self, source: str):
        """Delete all documents from a specific source"""
        if not self.client:
            raise RuntimeError("RAGMemory not initialized")

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=source)
                    )
                ]
            )
        )
        print(f"✅ Deleted documents from source '{source}'")
