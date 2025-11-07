"""
Integration tests for the complete ingestion pipeline.
Tests end-to-end document processing workflow.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import hashlib

from ingest import DocumentProcessor, DocumentWatcher


class TestProcessFile:
    """Test processing individual files"""

    @pytest.mark.asyncio
    @patch('ingest.QdrantClient')
    @patch('ingest.httpx.AsyncClient')
    async def test_process_file_complete_workflow(
        self, mock_httpx_class, mock_qdrant_class,
        mock_qdrant_client, mock_httpx_client, sample_text_file
    ):
        """Test complete file processing workflow"""
        mock_qdrant_class.return_value = mock_qdrant_client
        mock_httpx_class.return_value = mock_httpx_client

        file_path, content = sample_text_file

        processor = DocumentProcessor()
        await processor.process_file(file_path)

        # Verify file was added to processed set
        assert file_path in processor.processed_files

        # Verify embedding generation was called
        assert mock_httpx_client.post.called

        # Verify upsert to Qdrant was called
        assert mock_qdrant_client.upsert.called

    @pytest.mark.asyncio
    @patch('ingest.QdrantClient')
    async def test_process_file_already_processed(
        self, mock_qdrant_class, mock_qdrant_client, sample_text_file
    ):
        """Test that already processed files are skipped"""
        mock_qdrant_class.return_value = mock_qdrant_client

        file_path, content = sample_text_file

        processor = DocumentProcessor()
        processor.processed_files.add(file_path)

        # Mock upsert to verify it's NOT called
        mock_qdrant_client.upsert = MagicMock()

        await processor.process_file(file_path)

        # Upsert should not be called for already processed files
        mock_qdrant_client.upsert.assert_not_called()

    @pytest.mark.asyncio
    @patch('ingest.QdrantClient')
    async def test_process_file_empty_content(
        self, mock_qdrant_class, mock_qdrant_client, temp_dir
    ):
        """Test processing file with minimal content"""
        mock_qdrant_class.return_value = mock_qdrant_client

        # Create file with very little content
        file_path = temp_dir / "empty.txt"
        file_path.write_text("hi")  # Less than 50 characters

        processor = DocumentProcessor()
        mock_qdrant_client.upsert = MagicMock()

        await processor.process_file(str(file_path))

        # Should not process files with insufficient content
        mock_qdrant_client.upsert.assert_not_called()

    @pytest.mark.asyncio
    @patch('ingest.QdrantClient')
    @patch('ingest.httpx.AsyncClient')
    async def test_process_file_with_chunks(
        self, mock_httpx_class, mock_qdrant_class,
        mock_qdrant_client, mock_httpx_client, temp_dir
    ):
        """Test processing file that generates multiple chunks"""
        mock_qdrant_class.return_value = mock_qdrant_client
        mock_httpx_class.return_value = mock_httpx_client

        # Create file with long content
        file_path = temp_dir / "long.txt"
        content = "This is a sentence. " * 100  # Long enough to create multiple chunks
        file_path.write_text(content)

        processor = DocumentProcessor()
        await processor.process_file(str(file_path))

        # Verify upsert was called with multiple points
        assert mock_qdrant_client.upsert.called
        call_args = mock_qdrant_client.upsert.call_args
        points = call_args[1]["points"]
        assert len(points) > 1  # Should have multiple chunks

    @pytest.mark.asyncio
    @patch('ingest.QdrantClient')
    @patch('ingest.httpx.AsyncClient')
    async def test_process_file_metadata(
        self, mock_httpx_class, mock_qdrant_class,
        mock_qdrant_client, mock_httpx_client, sample_text_file
    ):
        """Test that file metadata is correctly included"""
        mock_qdrant_class.return_value = mock_qdrant_client
        mock_httpx_class.return_value = mock_httpx_client

        file_path, content = sample_text_file

        processor = DocumentProcessor()
        await processor.process_file(file_path)

        # Check upsert call
        call_args = mock_qdrant_client.upsert.call_args
        points = call_args[1]["points"]

        # Verify metadata in points
        for point in points:
            payload = point.payload
            assert "source" in payload
            assert "version" in payload
            assert "product" in payload
            assert "date" in payload
            assert "chunk_index" in payload
            assert "total_chunks" in payload
            assert "file_path" in payload
            assert "metadata" in payload
            assert "content" in payload

    @pytest.mark.asyncio
    @patch('ingest.QdrantClient')
    async def test_process_file_error_handling(
        self, mock_qdrant_class, mock_qdrant_client, temp_dir
    ):
        """Test error handling when processing fails"""
        mock_qdrant_class.return_value = mock_qdrant_client

        # Create a file that will cause extraction to work but embedding to fail
        file_path = temp_dir / "test.txt"
        file_path.write_text("Some test content for processing that is long enough.")

        processor = DocumentProcessor()

        # Mock generate_embedding to raise an error
        with patch.object(processor, 'generate_embedding', side_effect=Exception("Embedding failed")):
            # Should not raise, just print error
            await processor.process_file(str(file_path))

            # File should not be added to processed set
            assert str(file_path) not in processor.processed_files


class TestProcessDirectory:
    """Test processing entire directories"""

    @pytest.mark.asyncio
    @patch('ingest.QdrantClient')
    async def test_process_directory_nonexistent(
        self, mock_qdrant_class, mock_qdrant_client
    ):
        """Test processing non-existent directory"""
        mock_qdrant_class.return_value = mock_qdrant_client

        processor = DocumentProcessor()

        # Should handle gracefully
        await processor.process_directory("/nonexistent/path")

    @pytest.mark.asyncio
    @patch('ingest.QdrantClient')
    @patch('ingest.httpx.AsyncClient')
    async def test_process_directory_multiple_files(
        self, mock_httpx_class, mock_qdrant_class,
        mock_qdrant_client, mock_httpx_client, temp_dir
    ):
        """Test processing directory with multiple files"""
        mock_qdrant_class.return_value = mock_qdrant_client
        mock_httpx_class.return_value = mock_httpx_client

        # Create multiple test files with sufficient content (>50 chars)
        (temp_dir / "file1.txt").write_text("Content of file 1 that is definitely long enough to process and meet the minimum requirement.")
        (temp_dir / "file2.md").write_text("# File 2\n\nContent of file 2 that is also long enough to process completely.")
        (temp_dir / "ignored.xyz").write_text("This should be ignored")

        processor = DocumentProcessor()
        await processor.process_directory(str(temp_dir))

        # Should process 2 files (txt and md, not xyz)
        assert len(processor.processed_files) == 2

    @pytest.mark.asyncio
    @patch('ingest.QdrantClient')
    @patch('ingest.httpx.AsyncClient')
    async def test_process_directory_recursive(
        self, mock_httpx_class, mock_qdrant_class,
        mock_qdrant_client, mock_httpx_client, temp_dir
    ):
        """Test recursive directory processing"""
        mock_qdrant_class.return_value = mock_qdrant_client
        mock_httpx_class.return_value = mock_httpx_client

        # Create nested directory structure
        subdir = temp_dir / "subdir"
        subdir.mkdir()

        (temp_dir / "root.txt").write_text("Root file content that is definitely long enough to process.")
        (subdir / "nested.txt").write_text("Nested file content that is also long enough to process.")

        processor = DocumentProcessor()
        await processor.process_directory(str(temp_dir))

        # Should process both files recursively
        assert len(processor.processed_files) == 2

    @pytest.mark.asyncio
    @patch('ingest.QdrantClient')
    async def test_process_directory_empty(
        self, mock_qdrant_class, mock_qdrant_client, temp_dir
    ):
        """Test processing empty directory"""
        mock_qdrant_class.return_value = mock_qdrant_client

        processor = DocumentProcessor()
        await processor.process_directory(str(temp_dir))

        # Should complete without errors
        assert len(processor.processed_files) == 0


class TestQdrantIntegration:
    """Test Qdrant database integration"""

    @pytest.mark.asyncio
    @patch('ingest.QdrantClient')
    @patch('ingest.httpx.AsyncClient')
    async def test_upsert_to_qdrant(
        self, mock_httpx_class, mock_qdrant_class,
        mock_qdrant_client, mock_httpx_client, sample_text_file
    ):
        """Test data is correctly upserted to Qdrant"""
        mock_qdrant_class.return_value = mock_qdrant_client
        mock_httpx_class.return_value = mock_httpx_client

        file_path, content = sample_text_file

        processor = DocumentProcessor()
        await processor.process_file(file_path)

        # Verify upsert was called with correct collection
        mock_qdrant_client.upsert.assert_called_once()
        call_args = mock_qdrant_client.upsert.call_args
        assert call_args[1]["collection_name"] == "agentic_knowledge"

    @pytest.mark.asyncio
    @patch('ingest.QdrantClient')
    @patch('ingest.httpx.AsyncClient')
    async def test_point_structure(
        self, mock_httpx_class, mock_qdrant_class,
        mock_qdrant_client, mock_httpx_client, sample_text_file
    ):
        """Test that points have correct structure"""
        mock_qdrant_class.return_value = mock_qdrant_client
        mock_httpx_class.return_value = mock_httpx_client

        file_path, content = sample_text_file

        processor = DocumentProcessor()
        await processor.process_file(file_path)

        call_args = mock_qdrant_client.upsert.call_args
        points = call_args[1]["points"]

        # Check first point structure
        point = points[0]
        assert hasattr(point, 'id')
        assert hasattr(point, 'vector')
        assert hasattr(point, 'payload')
        assert isinstance(point.vector, list)
        assert len(point.vector) == 768  # Embedding dimension

    @pytest.mark.asyncio
    @patch('ingest.QdrantClient')
    @patch('ingest.httpx.AsyncClient')
    async def test_document_hash_consistency(
        self, mock_httpx_class, mock_qdrant_class,
        mock_qdrant_client, mock_httpx_client, sample_text_file
    ):
        """Test that document hash is consistent for same content"""
        mock_qdrant_class.return_value = mock_qdrant_client
        mock_httpx_class.return_value = mock_httpx_client

        file_path, content = sample_text_file

        processor = DocumentProcessor()
        await processor.process_file(file_path)

        call_args = mock_qdrant_client.upsert.call_args
        points = call_args[1]["points"]

        # All points from same document should have same base hash
        if len(points) > 1:
            point_ids = [point.id for point in points]
            base_hashes = [pid.rsplit('-', 1)[0] for pid in point_ids]
            assert all(h == base_hashes[0] for h in base_hashes)


class TestDocumentWatcher:
    """Test DocumentWatcher file system monitoring"""

    @patch('ingest.QdrantClient')
    def test_watcher_initialization(self, mock_qdrant_class, mock_qdrant_client):
        """Test DocumentWatcher initializes correctly"""
        mock_qdrant_class.return_value = mock_qdrant_client

        processor = DocumentProcessor()
        watcher = DocumentWatcher(processor)

        assert watcher.processor == processor

    @patch('ingest.QdrantClient')
    @patch('ingest.asyncio.run')
    def test_watcher_on_created_valid_file(
        self, mock_asyncio_run, mock_qdrant_class, mock_qdrant_client
    ):
        """Test watcher handles new file creation"""
        mock_qdrant_class.return_value = mock_qdrant_client

        processor = DocumentProcessor()
        watcher = DocumentWatcher(processor)

        # Mock event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "/test/document.txt"

        watcher.on_created(mock_event)

        # Should call process_file
        mock_asyncio_run.assert_called_once()

    @patch('ingest.QdrantClient')
    @patch('ingest.asyncio.run')
    def test_watcher_ignores_directories(
        self, mock_asyncio_run, mock_qdrant_class, mock_qdrant_client
    ):
        """Test watcher ignores directory creation"""
        mock_qdrant_class.return_value = mock_qdrant_client

        processor = DocumentProcessor()
        watcher = DocumentWatcher(processor)

        mock_event = MagicMock()
        mock_event.is_directory = True
        mock_event.src_path = "/test/newdir"

        watcher.on_created(mock_event)

        # Should NOT process directories
        mock_asyncio_run.assert_not_called()

    @patch('ingest.QdrantClient')
    @patch('ingest.asyncio.run')
    def test_watcher_ignores_unsupported_files(
        self, mock_asyncio_run, mock_qdrant_class, mock_qdrant_client
    ):
        """Test watcher ignores unsupported file types"""
        mock_qdrant_class.return_value = mock_qdrant_client

        processor = DocumentProcessor()
        watcher = DocumentWatcher(processor)

        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "/test/document.xyz"

        watcher.on_created(mock_event)

        # Should NOT process unsupported file types
        mock_asyncio_run.assert_not_called()
