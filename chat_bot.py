import os
import logging
import streamlit as st
from typing import List, Dict, Any, Optional
from openai import OpenAI
from knowledge_manager import KnowledgeManager

class ChatBot:
    def __init__(self, knowledge_manager: KnowledgeManager):
        self.knowledge_manager = knowledge_manager
        self.client = None
        
    def _get_openai_client(self):
        """Get or initialize OpenAI client"""
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                return None
                
            # Initialize client if not already done or if API key changed
            if self.client is None:
                self.client = OpenAI(api_key=api_key)
                logging.info("OpenAI client initialized successfully")
            
            return self.client
        except Exception as e:
            logging.error(f"Failed to initialize OpenAI client: {e}")
            return None
    
    def get_available_documents(self) -> List[Dict[str, str]]:
        """Get list of available documents for chat selection"""
        try:
            sources = self.knowledge_manager.get_sources()
            processed_files = self.knowledge_manager.get_processed_files_details()
            
            documents = []
            # Add "All Documents" option
            documents.append({
                'id': 'all',
                'name': '📚 All Documents',
                'description': f'Chat with all {len(sources)} documents'
            })
            
            # Add individual documents
            for file_info in processed_files:
                documents.append({
                    'id': file_info['file_hash'],
                    'name': f"📄 {file_info['filename']}",
                    'description': f"{file_info['file_type'].upper()} • {file_info['chunk_count']} chunks • {file_info['file_size_mb']} MB"
                })
            
            return documents
            
        except Exception as e:
            logging.error(f"Error getting available documents: {e}")
            return []
    
    def search_documents(self, query: str, selected_documents: List[str] = None, k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant content in selected documents"""
        try:
            if not self.knowledge_manager.vectorstore:
                return []
            
            # Get search results
            results = self.knowledge_manager.search_knowledge_base(query, k=k*2)  # Get more results to filter
            
            # Filter by selected documents if specified
            if selected_documents and 'all' not in selected_documents:
                filtered_results = []
                for result in results:
                    metadata = result.get('metadata', {})
                    file_hash = metadata.get('file_hash', '')
                    if file_hash in selected_documents:
                        filtered_results.append(result)
                results = filtered_results[:k]  # Limit to requested number
            else:
                results = results[:k]
            
            return results
            
        except Exception as e:
            logging.error(f"Error searching documents: {e}")
            return []
    
    def generate_response(self, user_message: str, selected_documents: List[str], chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Generate AI response based on user message and selected documents"""
        try:
            # Get OpenAI client (lazy initialization)
            client = self._get_openai_client()
            if not client:
                return {
                    'success': False,
                    'error': 'OpenAI client not initialized. Please check your API key.'
                }
            
            # Search for relevant context
            search_results = self.search_documents(user_message, selected_documents, k=5)
            
            if not search_results:
                return {
                    'success': False,
                    'error': 'No relevant content found in the selected documents.'
                }
            
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
            if chat_history:
                recent_history = chat_history[-6:]  # Last 3 exchanges
                history_parts = []
                for entry in recent_history:
                    if entry['role'] == 'user':
                        history_parts.append(f"User: {entry['content']}")
                    else:
                        history_parts.append(f"Assistant: {entry['content']}")
                history_context = "\n".join(history_parts)
            
            # Document selection context
            if 'all' in selected_documents:
                doc_context = "all available documents"
            else:
                doc_names = []
                for doc_id in selected_documents:
                    # Find document name by hash
                    processed_files = self.knowledge_manager.get_processed_files_details()
                    for file_info in processed_files:
                        if file_info['file_hash'] == doc_id:
                            doc_names.append(file_info['filename'])
                            break
                doc_context = ", ".join(doc_names) if doc_names else "selected documents"
            
            # Create system prompt
            system_prompt = f"""You are a helpful AI assistant that answers questions based on provided documents. 

The user is asking about content from: {doc_context}

Rules:
1. Answer based ONLY on the provided context from the documents
2. If the context doesn't contain enough information to answer the question, say so
3. Be specific and cite which document your information comes from when possible
4. Maintain conversational tone while being informative
5. If asked about something not in the documents, politely redirect to document content

Available context from documents:
{context}"""
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add recent chat history if available
            if history_context:
                messages.append({
                    "role": "system", 
                    "content": f"Recent conversation context:\n{history_context}"
                })
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                stream=False
            )
            
            assistant_response = response.choices[0].message.content.strip()
            
            return {
                'success': True,
                'response': assistant_response,
                'sources': list(sources),
                'context_used': len(search_results),
                'search_results': search_results
            }
            
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return {
                'success': False,
                'error': f'Error generating response: {str(e)}'
            }
    
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
            
            # Add document-specific starters if only one document is selected
            if len(selected_documents) == 1 and 'all' not in selected_documents:
                processed_files = self.knowledge_manager.get_processed_files_details()
                for file_info in processed_files:
                    if file_info['file_hash'] in selected_documents:
                        filename = file_info['filename']
                        starters.extend([
                            f"What is {filename} about?",
                            f"Tell me the main arguments in {filename}",
                            f"What conclusions does {filename} reach?"
                        ])
                        break
            
            return starters[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logging.error(f"Error getting conversation starters: {e}")
            return ["What can you tell me about these documents?"] 