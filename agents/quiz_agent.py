import json
import re
from typing import Dict, Any
import logging
from llm.litellm_provider import LiteLLMProvider
from prompts.quiz_prompt import quiz_prompt
import string

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

    def _normalize_options(self, question):
        if isinstance(question, dict) and 'options' in question and isinstance(question['options'], dict):
            # Convert dict to list of "A) ..." strings, sorted by key
            question['options'] = [f"{k}) {v}" for k, v in sorted(question['options'].items())]
        return question

    def _ensure_type_field(self, question, question_type):
        import logging
        if isinstance(question, dict) and 'type' not in question:
            logging.info(f"Adding missing 'type' field to question. Setting type to {question_type}.")
            question['type'] = question_type
        return question

    def _validate_question_schema(self, question: dict, question_type: str) -> bool:
        """
        Validate that the question dict has all required fields and correct types.
        Returns True if valid, False otherwise.
        """
        required_fields = ["type", "question", "correct_answer", "explanation", "source", "difficulty"]
        if question_type == "multiple_choice":
            required_fields.append("options")
        for field in required_fields:
            if field not in question:
                logging.error(f"Missing required field '{field}' in question: {question}")
                return False
        if question_type == "multiple_choice":
            if not isinstance(question["options"], list) or len(question["options"]) != 4:
                logging.error(f"'options' field must be a list of 4 items in multiple_choice question: {question}")
                return False
        return True

    def _post_process_question(self, question, question_type):
        question = self._normalize_options(self._ensure_type_field(question, question_type))
        # Attempt to auto-correct missing fields
        required_fields = ["type", "question", "correct_answer", "explanation", "source", "difficulty"]
        if question_type == "multiple_choice":
            required_fields.append("options")
        corrected = False
        for field in required_fields:
            if field not in question:
                corrected = True
                if field == "options":
                    question[field] = ["A) N/A", "B) N/A", "C) N/A", "D) N/A"]
                elif field == "type":
                    question[field] = question_type
                elif field == "difficulty":
                    question[field] = "medium"
                else:
                    question[field] = "N/A"
        if corrected:
            import logging
            logging.warning(f"Auto-corrected missing fields in question: {question}")
        if not self._validate_question_schema(question, question_type):
            logging.error(f"Invalid question schema detected. Returning fallback question. Question: {question}")
            return self._generate_fallback_question(question_type, question.get('difficulty', 'medium'))
        return question

    def generate_question(self, question_type: str = "multiple_choice", difficulty: str = "medium", selected_documents: list = []) -> Dict[str, Any]:
        import logging
        logging.info(f"Generating single question: type={question_type}, difficulty={difficulty}, selected_documents={selected_documents}")
        context = self.get_aggregated_context(selected_documents=selected_documents)
        logging.info(f"Aggregated context length: {len(context)}")
        if not context:
            error_message = "No context found. The knowledge base is empty or retriever failed. Please upload documents."
            logging.info(error_message)
            return self._generate_fallback_question(question_type, difficulty, error_message=error_message)
        if difficulty == "adaptive":
            logging.warning("Adaptive difficulty is not implemented. Returning fallback question.")
            return self._generate_fallback_question(question_type, difficulty, error_message="Adaptive difficulty is not implemented. Please select easy, medium, or hard.")
        if question_type == "multiple_choice":
            q = self._generate_multiple_choice(context, difficulty)
        elif question_type == "true_false":
            q = self._generate_true_false(context, difficulty)
        elif question_type == "short_answer":
            q = self._generate_short_answer(context, difficulty)
        else:
            q = self._generate_multiple_choice(context, difficulty)
        logging.info(f"Generated question: {q.get('question', str(q))[:100]}")
        return self._post_process_question(q, question_type)

    def generate_question_from_context(self, context: str, question_type: str = "multiple_choice", difficulty: str = "medium") -> Dict[str, Any]:
        import logging
        logging.info(f"Generating question from provided context. Type={question_type}, Difficulty={difficulty}")
        if not context:
            error_message = "No context provided. The knowledge base is empty or retriever failed. Please upload documents."
            logging.info(error_message)
            return self._generate_fallback_question(question_type, difficulty, error_message=error_message)
        if difficulty == "adaptive":
            logging.warning("Adaptive difficulty is not implemented. Returning fallback question.")
            return self._generate_fallback_question(question_type, difficulty, error_message="Adaptive difficulty is not implemented. Please select easy, medium, or hard.")
        if question_type == "multiple_choice":
            q = self._generate_multiple_choice(context, difficulty)
        elif question_type == "true_false":
            q = self._generate_true_false(context, difficulty)
        elif question_type == "short_answer":
            q = self._generate_short_answer(context, difficulty)
        else:
            q = self._generate_multiple_choice(context, difficulty)
        logging.info(f"Generated question from context: {q.get('question', str(q))[:100]}")
        return self._post_process_question(q, question_type)

    def generate_questions_batch_from_context(self, context: str, num_questions: int, question_type: str = "multiple_choice", difficulty: str = "medium") -> list:
        import logging
        logging.info(f"Generating batch of {num_questions} questions: type={question_type}, difficulty={difficulty}")
        if not context:
            error_message = "No context found. The knowledge base is empty or retriever failed. Please upload documents."
            logging.info(error_message)
            return [self._generate_fallback_question(question_type, difficulty, error_message=error_message)] * num_questions
        if difficulty == "adaptive":
            logging.warning("Adaptive difficulty is not implemented. Returning fallback questions.")
            error_message = "Adaptive difficulty is not implemented. Please select easy, medium, or hard."
            return [self._generate_fallback_question(question_type, difficulty, error_message=error_message)] * num_questions
        prompt = quiz_prompt.format(
            context=context,
            difficulty=difficulty,
            num_questions=num_questions,
            question_type=question_type,
            user_message=""
        )
        try:
            logging.info("Calling LLM for batch question generation.")
            answer = self.llm_provider.completion(prompt=prompt, temperature=0.7, max_tokens=3000)
            import json, re
            questions = []
            # Try to extract a JSON list from the response
            if "```json" in answer and "```" in answer:
                json_match = re.search(r'```json\s*\n?(.*?)\n?```', answer, re.DOTALL)
                if json_match:
                    try:
                        questions = json.loads(json_match.group(1).strip())
                    except Exception as e:
                        logging.error(f"Failed to parse JSON from markdown block: {e}")
            else:
                try:
                    questions = json.loads(answer.strip())
                except Exception as e:
                    logging.error(f"Failed to parse raw JSON: {e}")
            # Salvage: If questions is not a list, try to extract valid question dicts
            if not isinstance(questions, list):
                questions = []
            valid_questions = []
            for q in questions:
                processed = self._post_process_question(q, question_type)
                # If fallback, skip
                if not processed.get('question', '').startswith('No context available'):
                    valid_questions.append(processed)
            if not valid_questions:
                error_message = "LLM output was malformed or empty. Please try again or check your prompt/model settings."
                logging.error(error_message)
                return [self._generate_fallback_question(question_type, difficulty, error_message=error_message)] * num_questions
            if len(valid_questions) < num_questions:
                logging.warning(f"Only {len(valid_questions)} valid questions recovered from LLM output out of {num_questions} requested.")
            return valid_questions
        except Exception as e:
            logging.error(f"Error during batch question generation: {e}")
            error_message = f"Error during batch question generation: {e}"
            return [self._generate_fallback_question(question_type, difficulty, error_message=error_message)] * num_questions

    def _generate_multiple_choice(self, context: str, difficulty: str) -> Dict[str, Any]:
        try:
            prompt = quiz_prompt.format(
                context=context,
                difficulty=difficulty,
                num_questions=1,
                question_type="multiple_choice",
                user_message=""
            )
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

    def _normalize_answer(self, answer: str) -> str:
        # Remove leading option letter (e.g., 'A)', 'B)') and punctuation, lower, strip
        answer = answer.strip().lower()
        answer = re.sub(r'^[a-d]\)\s*', '', answer)  # Remove 'A) ', 'B) ', etc.
        answer = answer.translate(str.maketrans('', '', string.punctuation))
        answer = answer.strip()
        return answer

    def check_answer(self, user_answer: str, question_data: Dict[str, Any]) -> bool:
        correct = question_data.get("correct_answer", "")
        user_norm = self._normalize_answer(user_answer)
        correct_norm = self._normalize_answer(correct)
        # Check synonyms if provided
        synonyms = question_data.get("synonyms", [])
        if isinstance(synonyms, list):
            synonyms_norm = [self._normalize_answer(s) for s in synonyms]
        else:
            synonyms_norm = []
        return user_norm == correct_norm or user_norm in synonyms_norm

    def _get_adaptive_difficulty(self) -> str:
        # Adaptive difficulty is not implemented
        return "medium"

    def _generate_fallback_question(self, question_type: str, difficulty: str, error_message: str = "") -> Dict[str, Any]:
        message = error_message if error_message else "No context available. Please upload documents to generate quiz questions."
        return {
            "type": question_type,
            "question": message,
            "options": ["A) N/A", "B) N/A", "C) N/A", "D) N/A"],
            "correct_answer": "A) N/A",
            "explanation": message,
            "source": "System",
            "difficulty": difficulty
        }

    def get_aggregated_context(self, selected_documents: list) -> str:
        import logging
        logging.info(f"Aggregating context for selected_documents: {selected_documents}")
        """
        Aggregate all content from selected documents into a single string using vector store filtering.
        """
        try:
            chunks = self.retriever.get_all_chunks(selected_documents=selected_documents)
            logging.info(f"Fetched {len(chunks)} chunks from vector store.")
            if not chunks:
                return ""
            return " ".join(chunk['content'] for chunk in chunks)
        except Exception as e:
            logging.error(f"QuizAgent: Error retrieving aggregated context: {e}")
            return ""
