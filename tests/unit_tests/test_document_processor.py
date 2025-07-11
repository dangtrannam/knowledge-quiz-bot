import tempfile
import os
import shutil
import pytest
from unittest.mock import Mock, patch
from services.document_processor import DocumentProcessor

class TestDocumentProcessor:
    def setup_method(self):
        self.processor = DocumentProcessor()
    def test_process_text_content(self):
        text = "This is a test."
        chunks = self.processor.process_text_content(text, source_name="UnitTest")
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert hasattr(chunks[0], 'page_content')
        assert hasattr(chunks[0], 'metadata')
    def test_process_uploaded_file(self):
        # Patch loader to avoid real file IO
        with patch.object(self.processor, 'loader') as mock_loader:
            mock_loader.load_document.return_value = [Mock()]
            mock_loader.split_documents.return_value = [Mock(page_content="abc", metadata={})]
            class DummyFile:
                name = "test.txt"
                def getbuffer(self):
                    return b"abc"
            dummy = DummyFile()
            chunks = self.processor.process_uploaded_file(dummy)
            assert isinstance(chunks, list)
            assert len(chunks) > 0
            assert hasattr(chunks[0], 'page_content') or isinstance(chunks[0], Mock) 