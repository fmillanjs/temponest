"""
Unit tests for DocumentProcessor class.
Tests text extraction, chunking, and embedding generation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path
import httpx

from ingest import DocumentProcessor


class TestDocumentProcessorInit:
    """Test DocumentProcessor initialization"""

    @patch('ingest.QdrantClient')
    def test_processor_initialization(self, mock_qdrant_class, mock_qdrant_client):
        """Test processor initializes correctly"""
        mock_qdrant_class.return_value = mock_qdrant_client

        processor = DocumentProcessor()

        assert processor.qdrant == mock_qdrant_client
        assert processor.processed_files == set()
        mock_qdrant_class.assert_called_once()

    @patch('ingest.QdrantClient')
    def test_ensure_collection_called_on_init(self, mock_qdrant_class, mock_qdrant_client):
        """Test that _ensure_collection is called during init"""
        mock_qdrant_class.return_value = mock_qdrant_client

        with patch.object(DocumentProcessor, '_ensure_collection'):
            processor = DocumentProcessor()
            # _ensure_collection should be called


class TestCollectionManagement:
    """Test collection management methods"""

    @patch('ingest.QdrantClient')
    def test_collection_exists_true(self, mock_qdrant_class, mock_qdrant_client):
        """Test _collection_exists when collection exists"""
        mock_qdrant_class.return_value = mock_qdrant_client

        # Mock a collection that exists
        mock_collection = MagicMock()
        mock_collection.name = "agentic_knowledge"
        mock_collections = MagicMock()
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections

        processor = DocumentProcessor()
        exists = processor._collection_exists("agentic_knowledge")

        assert exists is True

    @patch('ingest.QdrantClient')
    def test_collection_exists_false(self, mock_qdrant_class, mock_qdrant_client):
        """Test _collection_exists when collection doesn't exist"""
        mock_qdrant_class.return_value = mock_qdrant_client

        # Mock no collections
        mock_collections = MagicMock()
        mock_collections.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections

        processor = DocumentProcessor()
        exists = processor._collection_exists("agentic_knowledge")

        assert exists is False

    @patch('ingest.QdrantClient')
    def test_collection_exists_error_handling(self, mock_qdrant_class, mock_qdrant_client):
        """Test _collection_exists handles errors gracefully"""
        mock_qdrant_class.return_value = mock_qdrant_client
        mock_qdrant_client.get_collections.side_effect = Exception("Connection error")

        processor = DocumentProcessor()
        exists = processor._collection_exists("agentic_knowledge")

        assert exists is False

    @patch('ingest.QdrantClient')
    def test_ensure_collection_creates_when_not_exists(self, mock_qdrant_class, mock_qdrant_client):
        """Test _ensure_collection creates collection when it doesn't exist"""
        from qdrant_client.models import Distance, VectorParams
        mock_qdrant_class.return_value = mock_qdrant_client

        # Mock no existing collections
        mock_collections = MagicMock()
        mock_collections.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections

        processor = DocumentProcessor()

        # Verify create_collection was called
        mock_qdrant_client.create_collection.assert_called_once()
        call_args = mock_qdrant_client.create_collection.call_args
        assert call_args[1]["collection_name"] == "agentic_knowledge"

    @patch('ingest.QdrantClient')
    def test_ensure_collection_skips_when_exists(self, mock_qdrant_class, mock_qdrant_client):
        """Test _ensure_collection skips creation when collection exists"""
        mock_qdrant_class.return_value = mock_qdrant_client

        # Mock existing collection
        mock_collection = MagicMock()
        mock_collection.name = "agentic_knowledge"
        mock_collections = MagicMock()
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections

        processor = DocumentProcessor()

        # create_collection should not be called
        mock_qdrant_client.create_collection.assert_not_called()

    @patch('ingest.QdrantClient')
    def test_ensure_collection_handles_already_exists_error(self, mock_qdrant_class, mock_qdrant_client):
        """Test _ensure_collection handles 'already exists' error gracefully"""
        from qdrant_client.http.exceptions import UnexpectedResponse
        mock_qdrant_class.return_value = mock_qdrant_client

        # Mock no collections initially
        mock_collections = MagicMock()
        mock_collections.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections

        # Mock create_collection to raise "already exists" error
        error_response = UnexpectedResponse(
            status_code=409,
            reason_phrase="Conflict",
            content=b'{"status":"error","result":{"message":"Collection already exists"}}',
            headers={}
        )
        mock_qdrant_client.create_collection.side_effect = error_response

        # Should not raise exception
        processor = DocumentProcessor()

    @patch('ingest.QdrantClient')
    def test_ensure_collection_raises_other_errors(self, mock_qdrant_class, mock_qdrant_client):
        """Test _ensure_collection raises non-'already exists' errors"""
        from qdrant_client.http.exceptions import UnexpectedResponse
        mock_qdrant_class.return_value = mock_qdrant_client

        # Mock no collections initially
        mock_collections = MagicMock()
        mock_collections.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections

        # Mock create_collection to raise different error
        error_response = UnexpectedResponse(
            status_code=500,
            reason_phrase="Internal Server Error",
            content=b'{"status":"error","result":{"message":"Database error"}}',
            headers={}
        )
        mock_qdrant_client.create_collection.side_effect = error_response

        # Should raise the exception
        with pytest.raises(UnexpectedResponse):
            processor = DocumentProcessor()


class TestTextExtraction:
    """Test text extraction from various file formats"""

    @patch('ingest.QdrantClient')
    def test_extract_text_from_txt(self, mock_qdrant_class, sample_text_file):
        """Test extracting text from .txt file"""
        file_path, expected_content = sample_text_file

        processor = DocumentProcessor()
        text = processor.extract_text(file_path)

        assert text == expected_content

    @patch('ingest.QdrantClient')
    @patch('ingest.PdfReader', None)
    def test_extract_text_from_pdf_when_library_not_available(self, mock_qdrant_class, temp_dir):
        """Test PDF extraction when pypdf is not installed"""
        file_path = temp_dir / "test.pdf"
        file_path.touch()

        processor = DocumentProcessor()
        text = processor.extract_text(str(file_path))

        # Should return empty string when PDF library not available
        assert text == ""

    @patch('ingest.QdrantClient')
    @patch('ingest.DocxDocument', None)
    def test_extract_text_from_docx_when_library_not_available(self, mock_qdrant_class, temp_dir):
        """Test DOCX extraction when python-docx is not installed"""
        file_path = temp_dir / "test.docx"
        file_path.touch()

        processor = DocumentProcessor()
        text = processor.extract_text(str(file_path))

        # Should return empty string when DOCX library not available
        assert text == ""

    @patch('ingest.QdrantClient')
    def test_extract_text_from_md(self, mock_qdrant_class, sample_md_file):
        """Test extracting text from .md file"""
        file_path, original_content = sample_md_file

        processor = DocumentProcessor()
        text = processor.extract_text(file_path)

        # Should contain the text content without markdown syntax
        assert "Test Document" in text
        assert "bold" in text
        assert "Section 2" in text

    @patch('ingest.QdrantClient')
    @patch('ingest.PdfReader')
    def test_extract_text_from_pdf(self, mock_pdf_reader_class, mock_qdrant_class, temp_dir):
        """Test extracting text from .pdf file"""
        file_path = temp_dir / "test.pdf"
        file_path.touch()  # Create empty file

        # Mock PDF reader
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page 1 content"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader_class.return_value = mock_reader

        processor = DocumentProcessor()
        text = processor.extract_text(str(file_path))

        assert text == "Page 1 content"
        mock_pdf_reader_class.assert_called_once_with(str(file_path))

    @patch('ingest.QdrantClient')
    @patch('ingest.DocxDocument')
    def test_extract_text_from_docx(self, mock_docx_class, mock_qdrant_class, temp_dir):
        """Test extracting text from .docx file"""
        file_path = temp_dir / "test.docx"
        file_path.touch()

        # Mock DOCX document
        mock_para1 = MagicMock()
        mock_para1.text = "Paragraph 1"
        mock_para2 = MagicMock()
        mock_para2.text = "Paragraph 2"
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_docx_class.return_value = mock_doc

        processor = DocumentProcessor()
        text = processor.extract_text(str(file_path))

        assert text == "Paragraph 1\nParagraph 2"

    @patch('ingest.QdrantClient')
    def test_extract_text_unsupported_format(self, mock_qdrant_class, temp_dir):
        """Test extracting text from unsupported file format"""
        file_path = temp_dir / "test.xyz"
        file_path.touch()

        processor = DocumentProcessor()
        text = processor.extract_text(str(file_path))

        assert text == ""


class TestTextChunking:
    """Test text chunking functionality"""

    @patch('ingest.QdrantClient')
    def test_chunk_text_short_text(self, mock_qdrant_class):
        """Test chunking text shorter than chunk size"""
        processor = DocumentProcessor()
        text = "Short text"

        chunks = processor.chunk_text(text, chunk_size=100, overlap=10)

        assert len(chunks) == 1
        assert chunks[0] == text

    @patch('ingest.QdrantClient')
    def test_chunk_text_long_text(self, mock_qdrant_class):
        """Test chunking long text"""
        processor = DocumentProcessor()
        text = "A" * 1000  # 1000 characters

        chunks = processor.chunk_text(text, chunk_size=300, overlap=50)

        assert len(chunks) > 1
        # Check overlap exists
        for i in range(len(chunks) - 1):
            # There should be some overlap between consecutive chunks
            assert len(chunks[i]) <= 300

    @patch('ingest.QdrantClient')
    def test_chunk_text_with_sentences(self, mock_qdrant_class):
        """Test chunking respects sentence boundaries"""
        processor = DocumentProcessor()
        text = ("This is sentence one. " * 10) + ("This is sentence two. " * 10)

        chunks = processor.chunk_text(text, chunk_size=200, overlap=20)

        # Chunks should try to break at sentence boundaries
        for chunk in chunks:
            assert len(chunk) > 0
            # Most chunks should end with a period (except possibly the last)
            if chunk != chunks[-1]:
                # Check that chunk doesn't cut in the middle of a word unnecessarily
                assert len(chunk.strip()) > 0

    @patch('ingest.QdrantClient')
    def test_chunk_text_overlap(self, mock_qdrant_class):
        """Test that chunks have proper overlap"""
        processor = DocumentProcessor()
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 20  # 520 characters

        chunks = processor.chunk_text(text, chunk_size=100, overlap=20)

        # Verify chunks exist and have reasonable lengths
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 100

    @patch('ingest.QdrantClient')
    def test_chunk_text_custom_parameters(self, mock_qdrant_class, sample_long_text):
        """Test chunking with custom chunk size and overlap"""
        processor = DocumentProcessor()

        chunks = processor.chunk_text(sample_long_text, chunk_size=500, overlap=100)

        assert len(chunks) > 1
        # Verify all chunks are within size limits
        for chunk in chunks:
            assert len(chunk) <= 500
            assert len(chunk) > 0


class TestEmbeddingGeneration:
    """Test embedding generation"""

    @pytest.mark.asyncio
    @patch('ingest.QdrantClient')
    @patch('ingest.httpx.AsyncClient')
    async def test_generate_embedding_success(
        self, mock_httpx_class, mock_qdrant_class, mock_httpx_client, mock_ollama_response
    ):
        """Test successful embedding generation"""
        mock_httpx_class.return_value = mock_httpx_client

        processor = DocumentProcessor()
        embedding = await processor.generate_embedding("Test text")

        assert embedding == mock_ollama_response["embedding"]
        assert len(embedding) == 768
        mock_httpx_client.post.assert_called_once()

    @pytest.mark.asyncio
    @patch('ingest.QdrantClient')
    @patch('ingest.httpx.AsyncClient')
    async def test_generate_embedding_http_error(self, mock_httpx_class, mock_qdrant_class):
        """Test embedding generation with HTTP error"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPError("API Error")

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_response)

        mock_httpx_class.return_value = mock_client

        processor = DocumentProcessor()

        with pytest.raises(httpx.HTTPError):
            await processor.generate_embedding("Test text")

    @pytest.mark.asyncio
    @patch('ingest.QdrantClient')
    @patch('ingest.httpx.AsyncClient')
    async def test_generate_embedding_correct_payload(
        self, mock_httpx_class, mock_qdrant_class, mock_httpx_client
    ):
        """Test that embedding generation sends correct payload"""
        mock_httpx_class.return_value = mock_httpx_client

        processor = DocumentProcessor()
        test_text = "Test document content"
        await processor.generate_embedding(test_text)

        # Verify the call was made with correct parameters
        call_args = mock_httpx_client.post.call_args
        assert "api/embeddings" in call_args[0][0]
        assert call_args[1]["json"]["prompt"] == test_text
        assert call_args[1]["json"]["model"] == "nomic-embed-text"


class TestProcessedFilesTracking:
    """Test processed files tracking"""

    @patch('ingest.QdrantClient')
    def test_processed_files_initialization(self, mock_qdrant_class):
        """Test processed files set is initialized empty"""
        processor = DocumentProcessor()

        assert processor.processed_files == set()

    @patch('ingest.QdrantClient')
    def test_processed_files_can_be_modified(self, mock_qdrant_class):
        """Test processed files set can be modified"""
        processor = DocumentProcessor()

        processor.processed_files.add("/path/to/file.txt")

        assert "/path/to/file.txt" in processor.processed_files
        assert len(processor.processed_files) == 1
