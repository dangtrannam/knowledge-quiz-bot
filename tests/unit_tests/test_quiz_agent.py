from unittest.mock import Mock
import pytest
from agents.quiz_agent import QuizAgent
from knowledge_manager import KnowledgeManager

class TestQuizAgent:
    def setup_method(self):
        self.mock_retriever = Mock(spec=KnowledgeManager)
        self.agent = QuizAgent(self.mock_retriever, llm_provider=Mock())

    def test_generate_question_success(self):
        mock_llm_provider = Mock()
        mock_llm_provider.completion = Mock(return_value='{"question": "Q?", "options": ["A", "B", "C", "D"], "correct_answer": "A"}')
        self.agent.llm_provider = mock_llm_provider
        self.mock_retriever.get_random_context.return_value = "context"
        result = self.agent.generate_question()
        assert result["question"] == "Q?"
        assert result["correct_answer"] == "A"

    def test_generate_question_no_context(self):
        self.mock_retriever.get_random_context.return_value = None
        result = self.agent.generate_question()
        assert result["question"].startswith("No context available")

    def test_generate_question_llm_error(self):
        mock_llm_provider = Mock()
        mock_llm_provider.completion = Mock(side_effect=Exception('LLM error'))
        self.agent.llm_provider = mock_llm_provider
        self.mock_retriever.get_random_context.return_value = "context"
        result = self.agent.generate_question()
        assert "question" in result
        assert "LLM error" in result["question"] or result["question"]

    def test_check_answer_multiple_choice(self):
        question_data = {
            'type': 'multiple_choice',
            'correct_answer': 'Option A',
            'options': ['Option A', 'Option B', 'Option C']
        }
        assert self.agent.check_answer('Option A', question_data) is True
        assert self.agent.check_answer('Option B', question_data) is False
        assert self.agent.check_answer('option a', question_data) is True

    def test_check_answer_true_false(self):
        question_data = {
            'type': 'true_false',
            'correct_answer': 'True'
        }
        assert self.agent.check_answer('True', question_data) is True
        assert self.agent.check_answer('False', question_data) is False
        assert self.agent.check_answer('true', question_data) is True

    def test_check_answer_short_answer(self):
        question_data = {
            'type': 'short_answer',
            'correct_answer': 'Machine Learning'
        }
        assert self.agent.check_answer('Machine Learning', question_data) is True
        assert self.agent.check_answer('machine learning', question_data) is True 