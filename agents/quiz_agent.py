import os
from dotenv import load_dotenv
import json
import random
import re
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import logging
load_dotenv()

class QuizAgent:
    """
    Agent for generating and evaluating quiz questions using an LLM and a knowledge retriever.
    """
    def __init__(self, retriever):
        self.retriever = retriever
        self.llm = None
        self.question_history = []
        self.difficulty_adjustment = 0
        self._last_config = None
        logging.info("Initializing QuizAgent (LLM lazy initialization)")

    def _get_llm(self, api_key: str, model: str = 'gpt-3.5-turbo', base_url: Optional[str] = None) -> Optional[ChatOpenAI]:
        """
        Get or initialize the LLM client.
        """
        try:
            llm_kwargs = {
                "model": model,
                "api_key": api_key,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            if base_url:
                llm_kwargs["base_url"] = base_url
            if self.llm is None or self._last_config != (api_key, model, base_url):
                self.llm = ChatOpenAI(**llm_kwargs)
                self._last_config = (api_key, model, base_url)
            return self.llm
        except Exception as e:
            logging.error(f"Failed to initialize LLM: {e}")
            self.llm = None
            return None

    def generate_question(self, api_key: str, model: str = 'gpt-3.5-turbo', base_url: Optional[str] = None, question_type: str = "multiple_choice", difficulty: str = "medium") -> Dict[str, Any]:
        """
        Generate a quiz question based on the knowledge base.
        """
        llm = self._get_llm(api_key, model, base_url)
        if not llm:
            return self._generate_fallback_question(question_type, difficulty)
        context = self.retriever.get_random_context()
        if not context:
            return self._generate_fallback_question(question_type, difficulty)
        if difficulty == "adaptive":
            difficulty = self._get_adaptive_difficulty()
        if question_type == "multiple_choice":
            return self._generate_multiple_choice(llm, context, difficulty)
        elif question_type == "true_false":
            return self._generate_true_false(llm, context, difficulty)
        elif question_type == "short_answer":
            return self._generate_short_answer(llm, context, difficulty)
        elif question_type == "mixed":
            return self.generate_question(api_key, model, base_url, random.choice(["multiple_choice", "true_false", "short_answer"]), difficulty)
        else:
            return self._generate_multiple_choice(llm, context, difficulty)

    def _generate_multiple_choice(self, llm, context: str, difficulty: str) -> Dict[str, Any]:
        prompt_template = PromptTemplate(
            input_variables=["context", "difficulty"],
            template="""
            Based on the following text, create a {difficulty} level multiple choice question.
            Context: {context}
            Requirements:
            - Create 1 clear, specific question
            - Provide exactly 4 answer options (A, B, C, D)
            - Only 1 option should be correct
            - Make incorrect options plausible but clearly wrong
            - Include a brief explanation for the correct answer
            - Cite the source information when possible
            Format your response as JSON:
            {{
                "type": "multiple_choice",
                "question": "Your question here",
                "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
                "correct_answer": "A) Correct option",
                "explanation": "Why this answer is correct and others are wrong",
                "source": "Relevant excerpt from context",
                "difficulty": "{difficulty}"
            }}
            """
        )
        chain = LLMChain(llm=llm, prompt=prompt_template)
        response = chain.invoke({"context": context, "difficulty": difficulty})
        return self._extract_json_from_response(response["text"] if isinstance(response, dict) else response)

    def _generate_true_false(self, llm, context: str, difficulty: str) -> Dict[str, Any]:
        # Similar to _generate_multiple_choice, but for true/false
        # ... (implement as needed)
        return {}

    def _generate_short_answer(self, llm, context: str, difficulty: str) -> Dict[str, Any]:
        # Similar to _generate_multiple_choice, but for short answer
        # ... (implement as needed)
        return {}

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