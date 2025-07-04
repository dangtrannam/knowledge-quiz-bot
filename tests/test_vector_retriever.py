import pytest
from unittest.mock import Mock
from retrievers.vector_retriever import VectorStoreRetriever

class TestVectorStoreRetriever:
    def test_similarity_search(self):
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search_with_score.return_value = [
            (Mock(page_content='A', metadata={'meta': 1}), 0.9),
            (Mock(page_content='B', metadata={'meta': 2}), 0.8)
        ]
        retriever = VectorStoreRetriever(mock_vectorstore)
        results = retriever.similarity_search('query', k=2)
        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]['content'] == 'A'
        assert results[1]['content'] == 'B'

    def test_similarity_search_empty(self):
        retriever = VectorStoreRetriever(None)
        results = retriever.similarity_search('query')
        assert results == []

    def test_get_random_context(self):
        docs = [Mock(page_content='short'), Mock(page_content='long enough' * 50)]
        retriever = VectorStoreRetriever(None, documents=docs)
        context = retriever.get_random_context(min_length=10)
        assert context is not None

    def test_get_random_context_empty(self):
        retriever = VectorStoreRetriever(None, documents=[])
        assert retriever.get_random_context() is None

    def test_get_context_by_topic(self):
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search.return_value = [Mock(page_content='topic1'), Mock(page_content='topic2')]
        retriever = VectorStoreRetriever(mock_vectorstore)
        results = retriever.get_context_by_topic('topic', k=2)
        assert results == ['topic1', 'topic2']

    def test_get_context_by_topic_empty(self):
        retriever = VectorStoreRetriever(None)
        assert retriever.get_context_by_topic('topic') == [] 