import json
import re
from typing import Dict, Any
import logging
from llm.litellm_provider import LiteLLMProvider
from prompts.quiz_prompt import quiz_prompt

class QuizAgent:
    """
    Agent for generating and evaluating quiz questions using an LLM and a knowledge retriever.
    """
    def __init__(self, retriever, llm_provider: LiteLLMProvider):
        self.retriever = retriever
        self.question_history = []
        self.difficulty_adjustment = 0
        self.llm_provider = llm_provider
        logging.info("Initializing QuizAgent (LLM lazy initialization)")

    def generate_question(self, question_type: str = "multiple_choice", difficulty: str = "medium") -> Dict[str, Any]:
        """
        Generate a quiz question based on the knowledge base.
        """
        context = self.retriever.get_random_context()
        if not context:
            return self._generate_fallback_question(question_type, difficulty)
        if difficulty == "adaptive":
            difficulty = self._get_adaptive_difficulty()
        if question_type == "multiple_choice":
            return self._generate_multiple_choice(context, difficulty)
        elif question_type == "true_false":
            return self._generate_true_false(context, difficulty)
        elif question_type == "short_answer":
            return self._generate_short_answer(context, difficulty)
        else:
            return self._generate_multiple_choice(context, difficulty)

    def _generate_multiple_choice(self, context: str, difficulty: str) -> Dict[str, Any]:
        try:
            prompt = quiz_prompt.format(context=context, difficulty=difficulty, user_message="")
            answer = self.llm_provider.completion(prompt=prompt, temperature=0.7, max_tokens=1000)
            return self._extract_json_from_response(answer)
        except Exception as e:
            return {
                "question": f"LLM error: {e}",
                "options": [],
                "correct_answer": "",
                "explanation": "",
                "source": "",
                "difficulty": difficulty
            }

    def _generate_true_false(self, context: str, difficulty: str) -> Dict[str, Any]:
        prompt = f"Based on the following text, create a {difficulty} level true/false question.\nContext: {context}"
        answer = self.llm_provider.completion(prompt=prompt, temperature=0.7, max_tokens=1000)
        return self._extract_json_from_response(answer)

    def _generate_short_answer(self, context: str, difficulty: str) -> Dict[str, Any]:
        prompt = f"Based on the following text, create a {difficulty} level short answer question.\nContext: {context}"
        answer = self.llm_provider.completion(prompt=prompt, temperature=0.7, max_tokens=1000)
        return self._extract_json_from_response(answer)

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        if "```json" in response and "```" in response:
            json_match = re.search(r'```json\s*\n?(.*?)\n?```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1).strip())
        try:
            return json.loads(response.strip())
        except Exception:
            return {"question": response.strip()}

    def check_answer(self, user_answer: str, question_data: Dict[str, Any]) -> bool:
        correct = question_data.get("correct_answer", "").strip().lower()
        return user_answer.strip().lower() == correct

    def _get_adaptive_difficulty(self) -> str:
        # Implement adaptive difficulty logic as needed
        return "medium"

    def _generate_fallback_question(self, question_type: str, difficulty: str) -> Dict[str, Any]:
        return {
            "type": question_type,
            "question": "No context available. Please upload documents to generate quiz questions.",
            "options": ["A) N/A", "B) N/A", "C) N/A", "D) N/A"],
            "correct_answer": "A) N/A",
            "explanation": "No data available.",
            "source": "System",
            "difficulty": difficulty
        } 