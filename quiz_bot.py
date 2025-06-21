import os
import openai
import json
import random
import re
from typing import Dict, List, Any, Optional
from langchain_community.llms import OpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import logging
from datetime import datetime

# Configure logging with UTF-8 encoding to handle Unicode characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('quiz_bot.log', encoding='utf-8')
    ]
)

class QuizBot:
    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON content from markdown-wrapped response"""
        # Remove markdown code blocks if present
        if "```json" in response and "```" in response:
            # Find the JSON content between ```json and ```
            json_match = re.search(r'```json\s*\n?(.*?)\n?```', response, re.DOTALL)
            if json_match:
                return json_match.group(1).strip()
        
        # If no markdown wrapper, return the response as-is
        return response.strip()
    
    def __init__(self, knowledge_manager):
        self.knowledge_manager = knowledge_manager
        self.llm = None
        self.question_history = []
        self.difficulty_adjustment = 0
        self._last_config = None  # Track configuration changes
        
        # Log initialization
        logging.info("Initializing QuizBot with GPT-4o-mini model (lazy initialization)")
    
    def _get_llm(self):
        """Get or initialize the LLM client (lazy initialization)"""
        try:
            import streamlit as st
            
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                logging.warning("OpenAI API key not found")
                return None
            
            # Get configuration from session state
            base_url = getattr(st.session_state, 'openai_base_url', "")
            selected_model = getattr(st.session_state, 'selected_model', 'gpt-3.5-turbo')
            model_input_type = getattr(st.session_state, 'model_input_type', 'predefined')
            current_config = (api_key, base_url, selected_model, model_input_type)
                
            # Initialize LLM if not already done or if configuration changed
            if self.llm is None or self._last_config != current_config:
                if self._last_config != current_config:
                    logging.info("Configuration changed, reinitializing LLM")
                    self.llm = None  # Reset LLM
                logging.info(f"Initializing ChatOpenAI with {selected_model} model")
                
                llm_kwargs = {
                    "model": selected_model,
                    "api_key": api_key,
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
                
                # Add base_url if provided
                if base_url and base_url.strip():
                    llm_kwargs["base_url"] = base_url.strip()
                    logging.info(f"Using custom base URL: {base_url}")
                
                self.llm = ChatOpenAI(**llm_kwargs)
                self._last_config = current_config  # Store current config
                
                # Test the LLM connection
                try:
                    test_response = self.llm.invoke("Test connection")
                    logging.info(f"LLM connection successful: {test_response}")
                except Exception as e:
                    logging.error(f"LLM connection failed: {e}")
                    self.llm = None
                    return None
            
            return self.llm
        except Exception as e:
            logging.error(f"Failed to initialize LLM: {e}")
            self.llm = None
            return None
        
    def generate_question(self, question_type: str = "multiple_choice", difficulty: str = "medium") -> Dict[str, Any]:
        """Generate a quiz question based on the knowledge base"""
        logging.info(f"Starting question generation - Type: {question_type}, Difficulty: {difficulty}")
        
        try:
            # Check if LLM is available
            llm = self._get_llm()
            if not llm:
                logging.error("LLM not available - API key missing or invalid")
                return {
                    "type": question_type,
                    "question": "API Key Error: Please enter a valid OpenAI API key in the sidebar",
                    "options": ["A) Check your API key", "B) Restart the application", "C) Contact support", "D) Try again later"],
                    "correct_answer": "A) Check your API key",
                    "explanation": "You need to enter a valid OpenAI API key to generate quiz questions.",
                    "source": "System error",
                    "difficulty": difficulty
                }
            
            # Get relevant context from knowledge base
            context = self.knowledge_manager.get_random_context()
            
            if not context:
                logging.warning("No context available from knowledge base, using fallback question")
                return self._generate_fallback_question()
            
            # Log context safely, handling Unicode characters
            safe_context = context.encode('ascii', 'ignore').decode('ascii') if context else ""
            logging.info(f"Using context: {safe_context[:100]}..." if len(safe_context) > 100 else f"Using context: {safe_context}")
            
            # Adjust difficulty based on user performance
            if difficulty == "adaptive":
                difficulty = self._get_adaptive_difficulty()
                logging.info(f"Adaptive difficulty adjusted to: {difficulty}")
            
            # Generate question using the appropriate template
            if question_type == "multiple_choice":
                result = self._generate_multiple_choice(context, difficulty)
            elif question_type == "true_false":
                result = self._generate_true_false(context, difficulty)
            elif question_type == "short_answer":
                result = self._generate_short_answer(context, difficulty)
            elif question_type == "mixed":
                # Randomly select question type
                question_types = ["multiple_choice", "true_false", "short_answer"]
                selected_type = random.choice(question_types)
                logging.info(f"Mixed mode selected: {selected_type}")
                return self.generate_question(selected_type, difficulty)
            else:
                result = self._generate_multiple_choice(context, difficulty)
            
            logging.info(f"Question generation completed successfully")
            return result
                
        except Exception as e:
            logging.error(f"Error generating question: {str(e)}")
            import traceback
            logging.error(f"Full traceback: {traceback.format_exc()}")
            return self._generate_fallback_question()
    
    def _generate_multiple_choice(self, context: str, difficulty: str) -> Dict[str, Any]:
        """Generate a multiple choice question"""
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
            
            Difficulty guidelines:
            - Easy: Direct facts, obvious answers
            - Medium: Requires understanding concepts
            - Hard: Requires analysis, inference, or connecting multiple ideas
            
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
        
        # Get LLM instance
        llm = self._get_llm()
        if not llm:
            return self._generate_fallback_question()
            
        chain = LLMChain(llm=llm, prompt=prompt_template)
        
        # Log the request details
        logging.info(f"Generating multiple choice question - Difficulty: {difficulty}")
        logging.info(f"Context length: {len(context)} characters")
        
        try:
            response = chain.run(context=context, difficulty=difficulty)
            
            # Log the raw response
            logging.info(f"OpenAI Response: {response}")
            
            # Extract JSON from markdown-wrapped response
            json_content = self._extract_json_from_response(response)
            logging.info(f"Extracted JSON: {json_content}")
            
            question_data = json.loads(json_content)
            
            # Log successful parsing
            logging.info(f"Successfully parsed question: {question_data.get('question', 'N/A')}")
            
            return question_data
        except json.JSONDecodeError as e:
            # Log JSON parsing error
            logging.error(f"JSON parsing failed: {e}")
            logging.error(f"Raw response was: {response}")
            
            # Fallback parsing if JSON is malformed
            return self._parse_response_fallback(response, "multiple_choice")
        except Exception as e:
            # Log any other errors
            logging.error(f"Error in OpenAI request: {e}")
            return self._generate_fallback_question()
    
    def _generate_true_false(self, context: str, difficulty: str) -> Dict[str, Any]:
        """Generate a true/false question"""
        prompt_template = PromptTemplate(
            input_variables=["context", "difficulty"],
            template="""
            Based on the following text, create a {difficulty} level true/false question.
            
            Context: {context}
            
            Requirements:
            - Create 1 clear statement that can be definitively true or false
            - Avoid ambiguous or partially true statements
            - Include a brief explanation
            - Cite the source information
            
            Difficulty guidelines:
            - Easy: Direct facts from text
            - Medium: Requires understanding implications
            - Hard: Requires careful analysis of nuanced information
            
            Format your response as JSON:
            {{
                "type": "true_false",
                "question": "Your true/false statement here",
                "correct_answer": "True" or "False",
                "explanation": "Why this statement is true/false with evidence",
                "source": "Relevant excerpt from context",
                "difficulty": "{difficulty}"
            }}
            """
        )
        
        # Get LLM instance
        llm = self._get_llm()
        if not llm:
            return self._generate_fallback_question()
            
        chain = LLMChain(llm=llm, prompt=prompt_template)
        
        # Log the request details
        logging.info(f"Generating true/false question - Difficulty: {difficulty}")
        
        try:
            response = chain.run(context=context, difficulty=difficulty)
            
            # Log the raw response
            logging.info(f"OpenAI Response (True/False): {response}")
            
            # Extract JSON from markdown-wrapped response
            json_content = self._extract_json_from_response(response)
            logging.info(f"Extracted JSON (T/F): {json_content}")
            
            question_data = json.loads(json_content)
            
            # Log successful parsing
            logging.info(f"Successfully parsed T/F question: {question_data.get('question', 'N/A')}")
            
            return question_data
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing failed (T/F): {e}")
            logging.error(f"Raw response was: {response}")
            return self._parse_response_fallback(response, "true_false")
        except Exception as e:
            logging.error(f"Error in OpenAI request (T/F): {e}")
            return self._generate_fallback_question()
    
    def _generate_short_answer(self, context: str, difficulty: str) -> Dict[str, Any]:
        """Generate a short answer question"""
        prompt_template = PromptTemplate(
            input_variables=["context", "difficulty"],
            template="""
            Based on the following text, create a {difficulty} level short answer question.
            
            Context: {context}
            
            Requirements:
            - Create 1 question that requires a brief written response (1-3 sentences)
            - Provide the ideal answer
            - Include key points that should be mentioned
            - Include explanation and source
            
            Difficulty guidelines:
            - Easy: What, when, where questions
            - Medium: How, why questions requiring explanation
            - Hard: Analysis, comparison, or synthesis questions
            
            Format your response as JSON:
            {{
                "type": "short_answer",
                "question": "Your question here",
                "correct_answer": "Ideal answer with key points",
                "key_points": ["Point 1", "Point 2", "Point 3"],
                "explanation": "Additional context and information",
                "source": "Relevant excerpt from context",
                "difficulty": "{difficulty}"
            }}
            """
        )
        
        # Get LLM instance
        llm = self._get_llm()
        if not llm:
            return self._generate_fallback_question()
            
        chain = LLMChain(llm=llm, prompt=prompt_template)
        
        # Log the request details
        logging.info(f"Generating short answer question - Difficulty: {difficulty}")
        
        try:
            response = chain.run(context=context, difficulty=difficulty)
            
            # Log the raw response
            logging.info(f"OpenAI Response (Short Answer): {response}")
            
            # Extract JSON from markdown-wrapped response
            json_content = self._extract_json_from_response(response)
            logging.info(f"Extracted JSON (SA): {json_content}")
            
            question_data = json.loads(json_content)
            
            # Log successful parsing
            logging.info(f"Successfully parsed SA question: {question_data.get('question', 'N/A')}")
            
            return question_data
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing failed (SA): {e}")
            logging.error(f"Raw response was: {response}")
            return self._parse_response_fallback(response, "short_answer")
        except Exception as e:
            logging.error(f"Error in OpenAI request (SA): {e}")
            return self._generate_fallback_question()
    
    def check_answer(self, user_answer: str, question_data: Dict[str, Any]) -> bool:
        """Check if the user's answer is correct"""
        question_type = question_data.get('type', 'multiple_choice')
        correct_answer = question_data.get('correct_answer', '')
        
        if question_type in ['multiple_choice', 'true_false']:
            # Exact match for MC and T/F
            return user_answer.strip().lower() == correct_answer.strip().lower()
        
        elif question_type == 'short_answer':
            # Use AI to evaluate short answers
            return self._evaluate_short_answer(user_answer, question_data)
        
        return False
    
    def _evaluate_short_answer(self, user_answer: str, question_data: Dict[str, Any]) -> bool:
        """Use AI to evaluate short answer responses"""
        correct_answer = question_data.get('correct_answer', '')
        key_points = question_data.get('key_points', [])
        
        prompt_template = PromptTemplate(
            input_variables=["question", "user_answer", "correct_answer", "key_points"],
            template="""
            Evaluate if the user's answer is correct for this question.
            
            Question: {question}
            User's Answer: {user_answer}
            Correct Answer: {correct_answer}
            Key Points: {key_points}
            
            Consider:
            - Does the user answer contain the main ideas?
            - Are the key facts correct?
            - Is the overall understanding demonstrated?
            
            Respond with only "CORRECT" or "INCORRECT" followed by a brief explanation.
            """
        )
        
        # Get LLM instance
        llm = self._get_llm()
        if not llm:
            # If LLM is not available, do basic string matching as fallback
            return user_answer.lower() in correct_answer.lower() or correct_answer.lower() in user_answer.lower()
            
        chain = LLMChain(llm=llm, prompt=prompt_template)
        response = chain.run(
            question=question_data.get('question', ''),
            user_answer=user_answer,
            correct_answer=correct_answer,
            key_points=', '.join(key_points)
        )
        
        return response.strip().upper().startswith('CORRECT')
    
    def _get_adaptive_difficulty(self) -> str:
        """Determine difficulty based on user performance"""
        if len(self.question_history) < 3:
            return "medium"
        
        recent_performance = self.question_history[-3:]
        correct_count = sum(1 for q in recent_performance if q.get('correct', False))
        
        if correct_count >= 3:
            return "hard"
        elif correct_count >= 2:
            return "medium"
        else:
            return "easy"
    
    def _generate_fallback_question(self) -> Dict[str, Any]:
        """Generate a basic question when context is unavailable"""
        return {
            "type": "multiple_choice",
            "question": "What is the primary purpose of this knowledge-based quiz system?",
            "options": [
                "A) To test your knowledge on uploaded documents", 
                "B) To play games",
                "C) To browse the internet",
                "D) To write essays"
            ],
            "correct_answer": "A) To test your knowledge on uploaded documents",
            "explanation": "This quiz bot is designed to help you test and reinforce your understanding of the content in your uploaded documents.",
            "source": "System information",
            "difficulty": "easy"
        }
    
    def _parse_response_fallback(self, response: str, question_type: str) -> Dict[str, Any]:
        """Fallback parsing when JSON parsing fails"""
        logging.warning(f"Attempting fallback parsing for response: {response[:200]}...")
        
        # Try to extract JSON content from markdown wrapper first
        try:
            json_content = self._extract_json_from_response(response)
            if json_content != response:  # If we extracted something different
                logging.info(f"Fallback: Trying extracted JSON: {json_content[:100]}...")
                return json.loads(json_content)
        except Exception as e:
            logging.warning(f"Fallback JSON extraction failed: {e}")
        
        # If all JSON parsing fails, try to extract basic information
        question_data = {
            "type": question_type,
            "question": "JSON parsing failed - but OpenAI responded with valid content",
            "correct_answer": "A) API Error",
            "explanation": "The AI generated a response but it couldn't be parsed properly. Please check the logs for the full response.",
            "source": "System error",
            "difficulty": "medium"
        }
        
        # Try to extract basic information from the response
        lines = response.split('\n')
        for line in lines:
            if '"question"' in line and ':' in line:
                try:
                    # Extract question text
                    question_part = line.split(':', 1)[1].strip().strip('",')
                    if len(question_part) > 10:  # Make sure it's a real question
                        question_data["question"] = question_part
                except:
                    pass
            elif '"correct_answer"' in line and ':' in line:
                try:
                    answer_part = line.split(':', 1)[1].strip().strip('",')
                    if len(answer_part) > 1:
                        question_data["correct_answer"] = answer_part
                except:
                    pass
        
        if question_type == "multiple_choice":
            question_data["options"] = [
                "A) API Error - Check API Key", 
                "B) Model Access Denied", 
                "C) Configuration Issue", 
                "D) Network Problem"
            ]
        
        logging.warning(f"Fallback question created: {question_data['question']}")
        return question_data
    
    def add_question_to_history(self, question_data: Dict[str, Any], user_answer: str, is_correct: bool):
        """Track question history for adaptive difficulty"""
        self.question_history.append({
            'question': question_data,
            'user_answer': user_answer,
            'correct': is_correct,
            'timestamp': str(datetime.now())
        })
        
        # Keep only recent history
        if len(self.question_history) > 20:
            self.question_history = self.question_history[-20:] 