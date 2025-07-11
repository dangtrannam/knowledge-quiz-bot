import pytest
from unittest.mock import Mock, patch
import embeddings.embedding_model as embedding_module

class TestEmbeddingModel:
    def test_embedding_generation(self):
        # Patch LiteLLMEmbeddings to avoid real API call
        with patch('embeddings.embedding_model.LiteLLMEmbeddings') as mock_embed:
            mock_instance = Mock()
            mock_instance.embed_query.return_value = [0.1, 0.2]
            mock_embed.return_value = mock_instance
            model = embedding_module.EmbeddingModel()
            assert model.embeddings is mock_instance
            # get() should return the embeddings instance
            assert model.get() is mock_instance

    def test_invalid_model_name(self):
        # Simulate LiteLLMEmbeddings raising an exception
        with patch('embeddings.embedding_model.LiteLLMEmbeddings', side_effect=Exception("Invalid model")):
            model = embedding_module.EmbeddingModel(model_name="invalid-model")
            assert model.embeddings is None 