from unittest.mock import Mock, patch
import pytest
from agents.chat_agent import ChatAgent

class TestChatAgent:
    def setup_method(self):
        self.mock_retriever = Mock()
        self.agent = ChatAgent(self.mock_retriever)

    def test_get_openai_client_success(self):
        with patch('agents.chat_agent.OpenAI') as mock_openai:
            mock_instance = Mock()
            mock_openai.return_value = mock_instance
            client = self.agent._get_openai_client(api_key='sk-test', base_url='http://test', model='gpt-3.5-turbo')
            assert client is mock_instance
            mock_openai.assert_called_once()

    def test_get_openai_client_missing_key(self):
        with patch('agents.chat_agent.OpenAI') as mock_openai:
            client = self.agent._get_openai_client(api_key='', base_url=None, model='gpt-3.5-turbo')
            assert client is None

    def test_generate_response_success(self):
        with patch.object(self.agent, '_get_openai_client', return_value=Mock()) as mock_client:
            with patch.object(self.agent.retriever, 'similarity_search', return_value=[{'content': 'context', 'metadata': {'source_file': 'file1'}}]):
                mock_client.return_value.chat.completions.create.return_value = Mock(
                    choices=[Mock(message=Mock(content='response'))]
                )
                result = self.agent.generate_response('msg', ['all'], [])
                assert result['success'] is True
                assert 'response' in result['response']

    def test_generate_response_no_client(self):
        with patch.object(self.agent, '_get_openai_client', return_value=None):
            result = self.agent.generate_response('msg', ['all'], [])
            assert result['success'] is False
            assert 'not initialized' in result['error']

    def test_generate_response_no_context(self):
        with patch.object(self.agent, '_get_openai_client', return_value=Mock()):
            with patch.object(self.agent.retriever, 'similarity_search', return_value=[]):
                result = self.agent.generate_response('msg', ['all'], [])
                assert result['success'] is False
                assert 'No relevant content' in result['error'] 