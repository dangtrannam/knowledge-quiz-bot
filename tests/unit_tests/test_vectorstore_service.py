import pytest
from unittest.mock import Mock, patch
from services.vector_store_service import VectorStoreService

class TestVectorStoreService:
    def setup_method(self):
        self.service = VectorStoreService(persist_directory="/tmp/test_chroma_db")
    def test_create_from_documents(self):
        with patch.object(self.service.manager, 'create_from_documents') as mock_create:
            mock_create.return_value = Mock()
            result = self.service.create_from_documents([Mock()], Mock())
            assert result is mock_create.return_value
            assert self.service.vector_store is result
    def test_add_documents(self):
        with patch.object(self.service.manager, 'add_documents') as mock_add:
            self.service.add_documents([Mock()])
            mock_add.assert_called()
    def test_load_existing(self):
        with patch.object(self.service.manager, 'load_existing') as mock_load:
            mock_load.return_value = Mock()
            result = self.service.load_existing(Mock())
            assert result is mock_load.return_value
            assert self.service.vector_store is result
    def test_persist(self):
        with patch.object(self.service.manager, 'persist') as mock_persist:
            self.service.persist()
            mock_persist.assert_called() 