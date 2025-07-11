import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any, Optional
from llm.litellm_provider import LiteLLMProvider
from prompts.chat_prompt import chat_prompt
load_dotenv()

class ChatAgent:
    """
    Agent for generating chat responses based on retrieved document context and LLM.
    """
    def __init__(self, retriever, llm_provider: LiteLLMProvider):
        self.retriever = retriever
        self.llm_provider = llm_provider

    def generate_response(self, user_message: str, selected_documents: List[str], chat_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate AI response based on user message and selected documents.
        """
        # Use LiteLLMProvider for chat completions
        # Search for relevant context
        search_results = self.retriever.similarity_search(user_message, k=5)
        if not search_results:
            return {'success': False, 'error': 'No relevant content found in the selected documents.'}
        # Prepare context from search results
        context_chunks = []
        sources = set()
        for result in search_results:
            content = result['content']
            metadata = result['metadata']
            source_file = metadata.get('source_file', metadata.get('original_filename', 'Unknown'))
            context_chunks.append(f"[From: {source_file}]\n{content}")
            sources.add(source_file)
        context = "\n\n---\n\n".join(context_chunks)
        # Prepare chat history context
        history_context = ""
        if chat_history is None:
            chat_history = []
        if chat_history:
            recent_history = chat_history[-6:]
            history_parts = []
            for entry in recent_history:
                if entry['role'] == 'user':
                    history_parts.append(f"User: {entry['content']}")
                else:
                    history_parts.append(f"Assistant: {entry['content']}")
            history_context = "\n".join(history_parts)
        # Document selection context
        doc_context = "all available documents" if 'all' in selected_documents else "selected documents"
        # Use chat_prompt to construct messages
        prompt_inputs = {
            "doc_context": doc_context,
            "context": context,
            "history_context": history_context,
            "user_message": user_message
        }
        # Convert LangChain BaseMessage objects to OpenAI API message dicts
        lc_messages = chat_prompt.format_messages(**prompt_inputs)
        messages = []
        for msg in lc_messages:
            # Map LangChain message types to OpenAI roles
            if hasattr(msg, 'type'):
                if msg.type == 'system':
                    role = 'system'
                elif msg.type == 'human':
                    role = 'user'
                elif msg.type == 'ai':
                    role = 'assistant'
                elif msg.type == 'tool':
                    role = 'tool'
                else:
                    role = msg.type
            else:
                role = 'user'
            messages.append({"role": role, "content": msg.content})
        # Generate response
        try:
            logging.info(f"Generating response with model: {self.llm_provider.model}")
            logging.info(f"Messages: {messages}")
            answer = self.llm_provider.chat(
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return {'success': True, 'response': answer, 'sources': list(sources)}
        except Exception as e:
            logging.error(f"Error generating chat response: {e}")
            return {'success': False, 'error': str(e)}

    def get_conversation_starters(self, selected_documents: List[str]) -> List[str]:
        """Generate conversation starter suggestions based on selected documents"""
        try:
            starters = [
                "What are the main topics covered in these documents?",
                "Can you summarize the key points?",
                "What are the most important insights?",
                "How do these documents relate to each other?",
                "What questions can I ask about this content?"
            ]

            # Add document-specific starters if only one document is selected (not 'all')
            if len(selected_documents) == 1 and 'all' not in selected_documents:
                file_hash = selected_documents[0]
                # Search for filename in retriever.documents metadata
                filename = None
                for doc in getattr(self.retriever, 'documents', []):
                    metadata = getattr(doc, 'metadata', {})
                    if metadata.get('file_hash') == file_hash:
                        filename = metadata.get('source_file') or metadata.get('original_filename') or metadata.get('filename')
                        break
                if filename:
                    starters.extend([
                        f"What is {filename} about?",
                        f"Tell me the main arguments in {filename}",
                        f"What conclusions does {filename} reach?"
                    ])
            return starters[:5]
        except Exception as e:
            logging.error(f"Error getting conversation starters: {e}")
            return ["What can you tell me about these documents?"] 