"""
RAG Document Ingestion Service

Watches a directory for new documents and:
1. Extracts text from various formats (PDF, DOCX, MD, TXT)
2. Chunks text into manageable pieces
3. Generates embeddings using Ollama
4. Stores in Qdrant vector database with metadata
"""

import os
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import asyncio

import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# PDF processing
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# DOCX processing
try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

import markdown


# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
WATCH_DIR = os.getenv("WATCH_DIR", "/data/documents")
COLLECTION_NAME = "agentic_knowledge"
EMBEDDING_DIM = 768
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50


class DocumentProcessor:
    """Process documents and ingest into Qdrant"""

    def __init__(self):
        self.ollama_url = OLLAMA_BASE_URL
        self.processed_files = set()
        self.qdrant = self._connect_with_retry()
        self._ensure_collection()

    def _connect_with_retry(self, max_retries: int = 10, initial_delay: float = 1.0) -> QdrantClient:
        """Connect to Qdrant with exponential backoff retry"""
        delay = initial_delay
        for attempt in range(1, max_retries + 1):
            try:
                print(f"🔌 Connecting to Qdrant at {QDRANT_URL} (attempt {attempt}/{max_retries})...")
                client = QdrantClient(url=QDRANT_URL, timeout=30)
                # Test connection
                client.get_collections()
                print(f"✅ Connected to Qdrant successfully")
                return client
            except Exception as e:
                if attempt == max_retries:
                    print(f"❌ Failed to connect to Qdrant after {max_retries} attempts: {e}")
                    raise
                print(f"⚠️  Connection attempt {attempt} failed: {e}")
                print(f"⏳ Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
                delay = min(delay * 2, 30.0)  # Exponential backoff, max 30s

    def _collection_exists(self, name: str) -> bool:
        """Check if collection exists"""
        try:
            collections = self.qdrant.get_collections()
            return any(col.name == name for col in collections.collections)
        except Exception as e:
            print(f"⚠️  Error checking collections: {e}")
            return False

    def _ensure_collection(self):
        """Create collection if it doesn't exist (idempotent)"""
        if self._collection_exists(COLLECTION_NAME):
            print(f"✅ Collection '{COLLECTION_NAME}' exists")
            return

        try:
            print(f"📝 Creating collection '{COLLECTION_NAME}'...")
            self.qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Collection '{COLLECTION_NAME}' created")
        except UnexpectedResponse as e:
            if "already exists" in str(e).lower():
                print(f"✅ Collection '{COLLECTION_NAME}' already exists")
            else:
                raise

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": EMBEDDING_MODEL,
                    "prompt": text
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]

    def extract_text(self, file_path: str) -> str:
        """Extract text from various file formats"""
        file_ext = Path(file_path).suffix.lower()

        if file_ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        elif file_ext == ".md":
            with open(file_path, "r", encoding="utf-8") as f:
                md_content = f.read()
                # Convert markdown to plain text
                html = markdown.markdown(md_content)
                # Simple HTML tag removal
                import re
                text = re.sub('<[^<]+?>', '', html)
                return text

        elif file_ext == ".pdf" and PdfReader:
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())
            return "\n".join(text_parts)

        elif file_ext in [".docx", ".doc"] and DocxDocument:
            doc = DocxDocument(file_path)
            text_parts = []
            for para in doc.paragraphs:
                text_parts.append(para.text)
            return "\n".join(text_parts)

        else:
            print(f"⚠️  Unsupported file type: {file_ext}")
            return ""

    def chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind(". ")
                if last_period > chunk_size // 2:
                    end = start + last_period + 2
                    chunk = text[start:end]

            chunks.append(chunk.strip())
            start = end - overlap

        return chunks

    async def process_file(self, file_path: str):
        """Process a single file and add to Qdrant"""
        file_path_obj = Path(file_path)

        if file_path in self.processed_files:
            print(f"⏭️  Already processed: {file_path_obj.name}")
            return

        print(f"📄 Processing: {file_path_obj.name}")

        try:
            # Extract text
            text = self.extract_text(file_path)
            if not text or len(text.strip()) < 50:
                print(f"⚠️  No substantial text extracted from {file_path_obj.name}")
                return

            # Chunk text
            chunks = self.chunk_text(text)
            print(f"   Split into {len(chunks)} chunks")

            # Get file metadata
            stat = file_path_obj.stat()
            source = file_path_obj.name
            version = "1.0"

            # Generate document hash for deduplication
            doc_hash = hashlib.sha256(text.encode()).hexdigest()[:16]

            # Process each chunk
            points = []
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = await self.generate_embedding(chunk)

                # Create point
                point_id = f"{doc_hash}-{i}"
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "content": chunk,
                        "source": source,
                        "version": version,
                        "product": "agentic-company",
                        "date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "file_path": str(file_path),
                        "metadata": {
                            "file_size": stat.st_size,
                            "file_type": file_path_obj.suffix
                        }
                    }
                )
                points.append(point)

            # Upsert to Qdrant
            self.qdrant.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )

            print(f"✅ Ingested {len(chunks)} chunks from {file_path_obj.name}")
            self.processed_files.add(file_path)

        except Exception as e:
            print(f"❌ Error processing {file_path_obj.name}: {e}")

    async def process_directory(self, directory: str):
        """Process all files in a directory"""
        dir_path = Path(directory)

        if not dir_path.exists():
            print(f"⚠️  Directory does not exist: {directory}")
            return

        files = list(dir_path.rglob("*"))
        doc_files = [
            f for f in files
            if f.is_file() and f.suffix.lower() in [".txt", ".md", ".pdf", ".docx", ".doc"]
        ]

        print(f"📚 Found {len(doc_files)} documents to process")

        for file_path in doc_files:
            await self.process_file(str(file_path))


class DocumentWatcher(FileSystemEventHandler):
    """Watch directory for new files"""

    def __init__(self, processor: DocumentProcessor):
        self.processor = processor

    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return

        file_path = event.src_path
        file_ext = Path(file_path).suffix.lower()

        if file_ext in [".txt", ".md", ".pdf", ".docx", ".doc"]:
            print(f"🆕 New file detected: {Path(file_path).name}")
            # Wait a bit to ensure file is fully written
            time.sleep(2)
            asyncio.run(self.processor.process_file(file_path))


async def main():
    """Main ingestion service"""
    print("🚀 Starting RAG Ingestion Service...")
    print(f"   Qdrant: {QDRANT_URL}")
    print(f"   Ollama: {OLLAMA_BASE_URL}")
    print(f"   Embedding Model: {EMBEDDING_MODEL}")
    print(f"   Watch Directory: {WATCH_DIR}")

    # Create watch directory if it doesn't exist
    Path(WATCH_DIR).mkdir(parents=True, exist_ok=True)

    # Initialize processor
    processor = DocumentProcessor()

    # Process existing files
    print("\n📂 Processing existing files...")
    await processor.process_directory(WATCH_DIR)

    # Start watching for new files
    print(f"\n👀 Watching {WATCH_DIR} for new documents...")
    event_handler = DocumentWatcher(processor)
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=True)
    observer.start()

    try:
        while True:
            await asyncio.sleep(60)
            # Periodically check collection size
            try:
                collection_info = processor.qdrant.get_collection(COLLECTION_NAME)
                points_count = getattr(collection_info, 'points_count', 'unknown')
                print(f"📊 Collection size: {points_count} vectors")
            except Exception as e:
                print(f"⚠️  Could not get collection stats: {e}")
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 Stopping ingestion service...")

    observer.join()


if __name__ == "__main__":
    asyncio.run(main())
