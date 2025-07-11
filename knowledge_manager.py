import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import random
from services.document_processor import DocumentProcessor   
from services.vector_store_service import VectorStoreService
from embeddings.embedding_model import EmbeddingModel
from retrievers.vector_retriever import VectorStoreRetriever
from langchain.schema import Document

class KnowledgeManager:
    """
    Orchestrates document ingestion, embedding, vector storage, and retrieval using modular components.
    """
    def __init__(self, persist_directory: str = "./chroma_db", metadata_file: str = "./processed_files.json"):
        self.persist_directory = persist_directory
        self.metadata_file = metadata_file
        self.document_processor = DocumentProcessor()
        self.vector_store_service = VectorStoreService(persist_directory)
        self.embedder = EmbeddingModel()
        self.documents = []
        self.is_preloaded = False
        self.vector_store = None
        self.retriever = None
        self._preload_existing_documents()
    
    def _preload_existing_documents(self):
        """Preload existing vector database if available"""
        self.metadata_out_of_sync = False
        try:
            embeddings = self.embedder.get()
            if not embeddings:
                logging.warning("Embeddings not available during preload. Vector store will not be loaded.")
                return
            self.vector_store = self.vector_store_service.load_existing(embeddings)
            if self.vector_store:
                self.is_preloaded = True
                self.retriever = VectorStoreRetriever(self.vector_store)
                logging.info("Preloaded vectorstore and retriever.")
                # Use Chroma as the source of truth for all documents
                try:
                    # Chroma.get() returns a dict with 'documents' and 'metadatas' (lists)
                    result = self.vector_store.get()
                    docs = []
                    if result and 'documents' in result and 'metadatas' in result:
                        from langchain.schema import Document
                        for content, meta in zip(result['documents'], result['metadatas']):
                            docs.append(Document(page_content=content, metadata=meta))
                    self.documents = docs
                    logging.info(f"Loaded {len(self.documents)} documents from Chroma vector store.")
                except Exception as e:
                    self.documents = []
                    logging.error(f"Failed to load documents from Chroma vector store: {e}")
            else:
                logging.info("No existing vector store found to preload.")
                self.metadata_out_of_sync = False
        except Exception as e:
            logging.error(f"Error during preload: {e}")
            self.is_preloaded = False
            self.metadata_out_of_sync = False

    @property
    def is_metadata_out_of_sync(self):
        return getattr(self, 'metadata_out_of_sync', False)
    
    def process_documents(self, uploaded_files) -> Dict[str, Any]:
        """Process uploaded documents and build vector database"""
        try:
            new_files = []
            skipped_files = []
            
            for uploaded_file in uploaded_files:
                # Check if file was already processed
                file_hash = self._get_file_hash(uploaded_file)
                file_name = uploaded_file.name
                
                # The original code had self.processed_files, which is removed.
                # This logic will now always process new files.
                new_files.append((uploaded_file, file_hash))
            
            if not new_files:
                logging.info("No new files to process")
                return {
                    'success': True,
                    'new_files': 0,
                    'skipped_files': len(skipped_files),
                    'skipped_list': skipped_files,
                    'message': f"All {len(skipped_files)} files were already processed"
                }
            
            all_texts = []
            processed_count = 0
            
            for uploaded_file, file_hash in new_files:
                texts = self.document_processor.process_uploaded_file(uploaded_file)
                if texts:
                    current_time = datetime.now().isoformat()
                    file_size = len(uploaded_file.getbuffer())
                    file_type = uploaded_file.name.split('.')[-1].lower()
                    for text in texts:
                        text.metadata.update({
                            'file_hash': file_hash,
                            'source_file': uploaded_file.name,
                            'processed_date': current_time,
                            'file_size': file_size,
                            'file_type': file_type
                        })
                    all_texts.extend(texts)
                    processed_count += 1
                    logging.info(f"Processed file: {uploaded_file.name} ({len(texts)} chunks)")
            
            if all_texts:
                logging.info(f"[VectorStore] Total chunks to add: {len(all_texts)}")
                for i, chunk in enumerate(all_texts):
                    logging.info(f"[VectorStore] Chunk {i}: {chunk.page_content[:80]}... | Metadata: {chunk.metadata}")
                # Create or update vector database
                embeddings = self.embedder.get()
                if not embeddings:
                    logging.error("Embeddings not available. Cannot create vector store.")
                    return {
                        'success': False,
                        'new_files': 0,
                        'skipped_files': len(skipped_files),
                        'skipped_list': skipped_files,
                        'error': 'Embedding model failed to initialize. Please check system logs.',
                        'message': 'Cannot process documents without embedding model.'
                    }
                
                # Verify embeddings are working
                try:
                    test_embedding = embeddings.embed_query("test")
                    if not test_embedding or len(test_embedding) == 0:
                        raise ValueError("Embeddings returned empty result")
                except Exception as e:
                    logging.error(f"Embedding test failed: {e}")
                    return {
                        'success': False,
                        'new_files': 0,
                        'skipped_files': len(skipped_files),
                        'skipped_list': skipped_files,
                        'error': f'Embedding model test failed: {str(e)}',
                        'message': 'Embedding model is not working properly.'
                    }
                
                # Create vector store
                try:
                    if self.vector_store is None:
                        self.vector_store = self.vector_store_service.create_from_documents(all_texts, embeddings)
                    else:
                        self.vector_store_service.add_documents(all_texts)
                    self.vector_store_service.persist()
                except Exception as e:
                    logging.error(f"Failed to create/update vector store: {e}")
                    return {
                        'success': False,
                        'new_files': 0,
                        'skipped_files': len(skipped_files),
                        'skipped_list': skipped_files,
                        'error': f'Vector store creation failed: {str(e)}',
                        'message': 'Failed to create vector database.'
                    }
                
                # Update document list
                if isinstance(self.documents, list):
                    self.documents.extend(all_texts)
                else:
                    self.documents = list(all_texts)
                
                # Save metadata
                # The original code had self.processed_files, which is removed.
                # This logic will now always save metadata.
                # self.save_metadata()
                
                self.retriever = VectorStoreRetriever(self.vector_store, self.documents)
                
                return {
                    'success': True,
                    'new_files': processed_count,
                    'skipped_files': len(skipped_files),
                    'skipped_list': skipped_files,
                    'total_chunks': len(all_texts),
                    'message': f"Successfully processed {processed_count} new files ({len(all_texts)} chunks)"
                }
            
            return {
                'success': False,
                'new_files': 0,
                'skipped_files': len(skipped_files),
                'skipped_list': skipped_files,
                'message': "No documents could be processed"
            }
            
        except Exception as e:
            logging.error(f"Error processing documents: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Error processing documents: {str(e)}"
            }
    
    def process_text_content(self, text_content: str, source_name: str = "Sample Content"):
        """Process raw text content for demo purposes"""
        try:
            embeddings = self.embedder.get()
            if not embeddings:
                # If embeddings are not initialized, try to re-instantiate
                logging.warning("Embeddings not available, attempting to reinitialize...")
                self.embedder = EmbeddingModel()
                embeddings = self.embedder.get()
                if not embeddings:
                    raise Exception("Failed to initialize embedding model")
            
            # Test embeddings
            try:
                test_embedding = embeddings.embed_query("test")
                if not test_embedding or len(test_embedding) == 0:
                    raise ValueError("Embeddings test failed")
            except Exception as e:
                logging.error(f"Embedding test failed: {e}")
                raise Exception(f"Embedding model is not working: {e}")
            
            texts = self.document_processor.process_text_content(text_content, source_name)
            
            # Create vector store with error handling
            try:
                self.vector_store = self.vector_store_service.create_from_documents(texts, embeddings)
                self.documents = texts
                self.retriever = VectorStoreRetriever(self.vector_store, self.documents)
                logging.info(f"Successfully processed text content: {len(texts)} chunks created")
                return True
            except Exception as e:
                logging.error(f"Failed to create vector store from text: {e}")
                raise Exception(f"Vector store creation failed: {e}")
            
        except Exception as e:
            logging.error(f"Error processing text content: {str(e)}")
            raise e
    
    def _get_file_hash(self, uploaded_file) -> str:
        """Generate hash for uploaded file to avoid reprocessing"""
        file_content = uploaded_file.getbuffer()
        return hashlib.md5(file_content).hexdigest()
    
    def search_knowledge_base(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant information"""
        if not self.vector_store:
            return []
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'relevance_score': score
                })
            
            return formatted_results
            
        except Exception as e:
            logging.error(f"Error searching knowledge base: {str(e)}")
            return []
    
    def is_valid_doc(self, doc):
        return isinstance(doc, Document)

    def get_random_context(self, min_length: int = 200) -> Optional[str]:
        """Get random context from knowledge base for question generation"""
        if not self.documents or not isinstance(self.documents, list):
            return None
        valid_docs = [doc for doc in self.documents if self.is_valid_doc(doc)]
        suitable_docs = [doc for doc in valid_docs if isinstance(doc, Document) and len(doc.page_content) >= min_length]
        if not suitable_docs:
            suitable_docs = [doc for doc in valid_docs if isinstance(doc, Document)]
        if suitable_docs:
            selected_doc = random.choice(suitable_docs)
            return selected_doc.page_content
        return None
    
    def get_context_by_topic(self, topic: str, k: int = 3) -> List[str]:
        """Get context related to a specific topic"""
        if not self.vector_store:
            return []
        
        try:
            results = self.vector_store.similarity_search(topic, k=k)
            return [doc.page_content for doc in results]
        except Exception as e:
            logging.error(f"Error getting context by topic: {str(e)}")
            return []
    
    def get_all_contexts(self) -> List[Dict[str, Any]]:
        """Get all document contexts with metadata"""
        contexts = []
        valid_docs = [doc for doc in self.documents if self.is_valid_doc(doc)]
        for doc in valid_docs:
            if not isinstance(doc, Document):
                continue
            contexts.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'length': len(doc.page_content)
            })
        return contexts
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        if not self.documents or not isinstance(self.documents, list):
            return {
                'doc_count': 0,
                'chunk_count': 0,
                'total_chars': 0,
                'avg_chunk_size': 0,
                'topic_count': 0,
                'source_files': []
            }
        valid_docs = [doc for doc in self.documents if self.is_valid_doc(doc)]
        valid_docs = [doc for doc in valid_docs if isinstance(doc, Document)]
        total_chars = sum(len(doc.page_content) for doc in valid_docs)
        avg_chunk_size = total_chars / len(valid_docs) if valid_docs else 0
        source_files = set()
        for doc in valid_docs:
            if 'source_file' in doc.metadata:
                source_files.add(doc.metadata['source_file'])
            elif 'original_filename' in doc.metadata:
                source_files.add(doc.metadata['original_filename'])
            elif 'source' in doc.metadata:
                source_files.add(doc.metadata['source'])
        topic_count = min(len(source_files) * 3, len(valid_docs) // 2)
        topic_count = max(topic_count, 1) if valid_docs else 0
        return {
            'doc_count': len(source_files),
            'chunk_count': len(valid_docs),
            'total_chars': total_chars,
            'avg_chunk_size': int(avg_chunk_size),
            'topic_count': topic_count,
            'source_files': list(source_files)
        }
    
    def clear_knowledge_base(self):
        """Clear the current knowledge base"""
        self.documents = []
        # Use the vectorstore_service to clear all data from the vector store
        try:
            self.vector_store_service.clear_all_data()
            logging.info("Cleared all data from vector store using clear_all_data().")
        except Exception as e:
            logging.error(f"Error clearing all data from vector store: {e}")
        self.vector_store = None
    
    def export_knowledge_base(self) -> Dict[str, Any]:
        """Export knowledge base for backup/sharing"""
        valid_docs = [doc for doc in self.documents if self.is_valid_doc(doc) and isinstance(doc, Document)]
        return {
            'documents': [
                {
                    'content': doc.page_content,
                    'metadata': doc.metadata
                }
                for doc in valid_docs
            ],
            'stats': self.get_stats()
        }
    
    def get_sources(self) -> List[str]:
        """Get list of all source documents"""
        sources = set()
        valid_docs = [doc for doc in self.documents if self.is_valid_doc(doc) and isinstance(doc, Document)]
        for doc in valid_docs:
            if 'source_file' in doc.metadata:
                sources.add(doc.metadata['source_file'])
            elif 'original_filename' in doc.metadata:
                sources.add(doc.metadata['original_filename'])
            elif 'source' in doc.metadata:
                sources.add(doc.metadata['source'])
        return sorted(list(sources))
    
    def remove_processed_file(self, file_hash: str) -> bool:
        """Remove a processed file from the knowledge base"""
        try:
            # Remove documents from memory (this is a simplified approach)
            self.documents = [doc for doc in self.documents 
                            if self.is_valid_doc(doc) and isinstance(doc, Document) and doc.metadata.get('file_hash') != file_hash]
            logging.info(f"Removed processed file with hash: {file_hash}")
            return True
        except Exception as e:
            logging.error(f"Error removing processed file: {e}")
            return False
    
    def rebuild_vectorstore(self):
        """Rebuild the vectorstore from current documents"""
        try:
            if not self.documents or not self.embedder.get():
                return False

            # Clear existing vectorstore in-place
            self.vector_store_service.clear_all_data()

            # Recreate vectorstore
            self.vector_store = self.vector_store_service.create_from_documents(self.documents, self.embedder.get())

            logging.info("Successfully rebuilt vectorstore")
            return True

        except Exception as e:
            logging.error(f"Error rebuilding vectorstore: {e}")
            return False
    
    def is_file_already_processed(self, uploaded_file) -> bool:
        """Check if a file has already been processed"""
        file_hash = self._get_file_hash(uploaded_file)
        for doc in self.documents:
            if getattr(doc, "metadata", {}).get("file_hash") == file_hash:
                return True
        return False 