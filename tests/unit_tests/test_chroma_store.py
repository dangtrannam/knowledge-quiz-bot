import pytest
from unittest.mock import patch, Mock
from vectorstores.chroma_store import ChromaStoreManager

class TestChromaStoreManager:
    def setup_method(self):
        self.manager = ChromaStoreManager(persist_directory='test_chroma_db')

    def test_create_from_documents(self):
        with patch('vectorstores.chroma_store.Chroma') as mock_chroma:
            mock_instance = Mock()
            mock_chroma.from_documents.return_value = mock_instance
            docs = [Mock()]
            embeddings = Mock()
            result = self.manager.create_from_documents(docs, embeddings)
            assert result is mock_instance
            mock_chroma.from_documents.assert_called_once_with(documents=docs, embedding=embeddings, persist_directory='test_chroma_db')

    def test_load_existing(self):
        with patch('os.path.exists', return_value=True), \
             patch('vectorstores.chroma_store.Chroma') as mock_chroma:
            mock_instance = Mock()
            mock_chroma.return_value = mock_instance
            embeddings = Mock()
            result = self.manager.load_existing(embeddings)
            assert result is mock_instance
            mock_chroma.assert_called_once_with(persist_directory='test_chroma_db', embedding_function=embeddings)

    def test_add_documents(self):
        self.manager.vectorstore = Mock()
        docs = [Mock()]
        self.manager.add_documents(docs)
        self.manager.vectorstore.add_documents.assert_called_once_with(docs)

    def test_persist(self):
        self.manager.vectorstore = Mock()
        self.manager.persist()
        # Just check that logging does not raise and method exists

    def test_clear(self):
        with patch('os.path.exists', return_value=True), \
             patch('shutil.rmtree') as mock_rmtree:
            self.manager.vectorstore = Mock()
            self.manager.clear()
            mock_rmtree.assert_called_once_with('test_chroma_db')
            assert self.manager.vectorstore is None 