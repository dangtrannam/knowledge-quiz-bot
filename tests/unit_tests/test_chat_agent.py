from unittest.mock import Mock, patch
import pytest
from agents.chat_agent import ChatAgent

class TestChatAgent:
    def setup_method(self):
        self.mock_retriever = Mock()
        self.agent = ChatAgent(self.mock_retriever, llm_provider=Mock())

    def test_generate_response_success(self):
        self.agent.llm_provider.chat = Mock(return_value='response')
        self.mock_retriever.similarity_search.return_value = [
            {'content': 'context', 'metadata': {'source_file': 'file1'}}
        ]
        result = self.agent.generate_response('msg', ['all'], [])
        assert result['success'] is True
        assert 'response' in result['response']

    def test_generate_response_no_context(self):
        self.mock_retriever.similarity_search.return_value = []
        result = self.agent.generate_response('msg', ['all'], [])
        assert result['success'] is False
        assert 'No relevant content' in result['error']

    def test_generate_response_llm_error(self):
        self.agent.llm_provider.chat = Mock(side_effect=Exception('LLM error'))
        self.mock_retriever.similarity_search.return_value = [
            {'content': 'context', 'metadata': {'source_file': 'file1'}}
        ]
        result = self.agent.generate_response('msg', ['all'], [])
        assert result['success'] is False
        assert 'LLM error' in result['error'] 