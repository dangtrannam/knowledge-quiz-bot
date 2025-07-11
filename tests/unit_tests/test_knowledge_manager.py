import os
import tempfile
import shutil
import gc
import json
from unittest.mock import Mock, patch
import pytest
from knowledge_manager import KnowledgeManager

class TestKnowledgeManager:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_metadata = os.path.join(self.temp_dir, 'metadata.json')
        self.km = KnowledgeManager(persist_directory=self.temp_dir, metadata_file=self.temp_metadata)
    def teardown_method(self):
        del self.km.vectorstore
        gc.collect()
        try:
            shutil.rmtree(self.temp_dir)
        except PermissionError:
            pass
    def test_initialization(self):
        assert self.km.documents == []
        assert self.km.vectorstore is None or hasattr(self.km.vectorstore, 'similarity_search_with_score')
        assert self.km.processed_files == {} or self.km.processed_files == set()
    def test_process_text_content(self):
        sample_text = """
        This is a test document about machine learning.
        Machine learning is a subset of artificial intelligence.
        It uses algorithms to find patterns in data.
        """
        with patch('embeddings.embedding_model.HuggingFaceEmbeddings') as mock_embeddings:
            mock_instance = Mock()
            mock_instance.embed_query.return_value = [0.1, 0.2]
            mock_embeddings.return_value = mock_instance
            with patch('vectorstores.chroma_store.Chroma') as mock_chroma:
                mock_vectorstore = Mock()
                mock_chroma.from_documents.return_value = mock_vectorstore
                km = KnowledgeManager(persist_directory=self.temp_dir, metadata_file=self.temp_metadata)
                result = km.process_text_content(sample_text, "Test Document")
                assert result is True
                assert len(km.documents) > 0
    def test_get_file_hash(self):
        mock_file = Mock()
        mock_file.getbuffer.return_value = b'test content'
        hash1 = self.km._get_file_hash(mock_file)
        hash2 = self.km._get_file_hash(mock_file)
        assert hash1 == hash2
        assert len(hash1) == 32
    def test_search_knowledge_base_empty(self):
        results = self.km.search_knowledge_base("test query")
        assert results == []
    def test_get_random_context_empty(self):
        context = self.km.get_random_context()
        assert context is None
    def test_get_stats_empty(self):
        stats = self.km.get_stats()
        assert stats['doc_count'] == 0
        assert stats['chunk_count'] == 0
        assert stats['total_chars'] == 0
        assert stats['topic_count'] == 0
    def test_duplicate_file_upload(self):
        # Simulate uploading the same file twice
        mock_file = Mock()
        mock_file.getbuffer.return_value = b'test content'
        file_hash = self.km._get_file_hash(mock_file)
        self.km.processed_files = {file_hash: {'filename': 'test.pdf'}}
        # Should detect as already processed
        assert self.km.is_file_already_processed(mock_file) is True
        # Should not process again
        # (simulate process_documents logic if needed)
    def test_corrupted_metadata_file(self):
        # Write invalid/corrupt JSON to metadata file
        with open(self.temp_metadata, 'w') as f:
            f.write('{invalid json')
        # Should handle error and reset processed_files
        km = KnowledgeManager(persist_directory=self.temp_dir, metadata_file=self.temp_metadata)
        assert isinstance(km.processed_files, dict)
        assert len(km.processed_files) == 0 