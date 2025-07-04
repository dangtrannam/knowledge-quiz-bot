import pytest
from unittest.mock import Mock, patch
import embeddings.embedding_model as embedding_module

class TestEmbeddingModel:
    def test_device_selection_cpu(self):
        with patch('torch.cuda.is_available', return_value=False):
            model = embedding_module.EmbeddingModel(device="cpu")
            assert model.device == "cpu"

    def test_device_selection_cuda(self):
        with patch('torch.cuda.is_available', return_value=True):
            model = embedding_module.EmbeddingModel(device="cpu")
            assert model.device == "cuda"

    def test_embedding_generation(self):
        # Patch HuggingFaceEmbeddings to avoid real model download
        with patch('embeddings.embedding_model.HuggingFaceEmbeddings') as mock_embed:
            mock_instance = Mock()
            mock_embed.return_value = mock_instance
            model = embedding_module.EmbeddingModel(device="cpu")
            assert model.embeddings is mock_instance
            # get() should return the embeddings instance
            assert model.get() is mock_instance

    def test_invalid_model_name(self):
        # Simulate HuggingFaceEmbeddings raising an exception
        with patch('embeddings.embedding_model.HuggingFaceEmbeddings', side_effect=Exception("Invalid model")):
            model = embedding_module.EmbeddingModel(model_name="invalid-model", device="cpu")
            assert model.embeddings is None 