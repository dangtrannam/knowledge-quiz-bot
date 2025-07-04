import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
load_dotenv()

class ChatAgent:
    """
    Agent for generating chat responses based on retrieved document context and LLM.
    """
    def __init__(self, retriever):
        self.retriever = retriever
        self.client = None
        self._last_config = None

    def _get_openai_client(self, api_key: str, base_url: Optional[str] = None, model: str = 'gpt-3.5-turbo') -> Optional[OpenAI]:
        try:
            logging.debug(f"_get_openai_client called with api_key: {repr(api_key)}, base_url: {repr(base_url)}, model: {repr(model)}")
            if not api_key:
                logging.error(f"OPENAI_API_KEY not provided. Received api_key: {repr(api_key)}")
                raise ValueError("OPENAI_API_KEY not provided.")
            if base_url and isinstance(base_url, str) and base_url.strip():
                self.client = OpenAI(api_key=api_key, base_url=base_url.strip())
            else:
                self.client = OpenAI(api_key=api_key)
            self._last_config = (api_key, base_url, model)
            return self.client
        except Exception as e:
            logging.error(f"Failed to initialize OpenAI client: {e}")
            return None

    def generate_response(self, user_message: str, selected_documents: List[str], chat_history: Optional[List[Dict[str, Any]]] = None, api_key: str = '', base_url: Optional[str] = None, model: str = 'gpt-3.5-turbo') -> Dict[str, Any]:
        """
        Generate AI response based on user message and selected documents.
        """
        client = self._get_openai_client(api_key, base_url, model)
        if not client:
            return {'success': False, 'error': 'OpenAI client not initialized. Please check your API key.'}
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
        # Create system prompt
        system_prompt = f"""You are a helpful AI assistant that answers questions based on provided documents.\n\nThe user is asking about content from: {doc_context}\n\nRules:\n1. Answer based ONLY on the provided context from the documents\n2. If the context doesn't contain enough information to answer the question, say so\n3. Be specific and cite which document your information comes from when possible\n4. Maintain conversational tone while being informative\n5. If asked about something not in the documents, politely redirect to document content\n\nAvailable context from documents:\n{context}"""
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
        ]
        if history_context:
            messages.append({"role": "system", "content": f"Recent conversation context:\n{history_context}"})
        messages.append({"role": "user", "content": user_message})
        # Generate response
        try:
            logging.info(f"Generating response with model: {model}")
            logging.info(f"Messages: {messages}")
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            logging.info(f"Response: {response}")
            answer = response.choices[0].message.content
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