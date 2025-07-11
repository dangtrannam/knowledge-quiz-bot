import os
import tempfile
import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import random
import logging
from services.metadata_manager import MetadataManager
from services.document_processor import DocumentProcessor
from services.vectorstore_service import VectorStoreService
from embeddings.embedding_model import EmbeddingModel
from retrievers.vector_retriever import VectorStoreRetriever

class KnowledgeManager:
    """
    Orchestrates document ingestion, embedding, vector storage, and retrieval using modular components.
    """
    def __init__(self, persist_directory: str = "./chroma_db", metadata_file: str = "./processed_files.json"):
        self.persist_directory = persist_directory
        self.metadata_file = metadata_file
        self.metadata_manager = MetadataManager(metadata_file)
        self.document_processor = DocumentProcessor()
        self.vectorstore_service = VectorStoreService(persist_directory)
        self.embedder = EmbeddingModel()
        self.documents = []
        self.processed_files = self.metadata_manager.load_metadata()
        self.is_preloaded = False
        self.vectorstore = None
        self.retriever = None
        self._preload_existing_documents()
    
    def _save_metadata(self):
        self.metadata_manager.save_metadata(self.processed_files)
    
    def _preload_existing_documents(self):
        """Preload existing vector database if available"""
        try:
            embeddings = self.embedder.get()
            if not embeddings:
                logging.warning("Embeddings not available during preload. Vector store will not be loaded.")
                return
            
            # Test embeddings before using them
            try:
                test_embedding = embeddings.embed_query("test")
                if not test_embedding or len(test_embedding) == 0:
                    logging.warning("Embedding test failed during preload. Skipping vector store loading.")
                    return
            except Exception as e:
                logging.warning(f"Embedding test failed during preload: {e}. Skipping vector store loading.")
                return
            
            self.vectorstore = self.vectorstore_service.load_existing(embeddings)
            if self.vectorstore:
                self.is_preloaded = True
                self.retriever = VectorStoreRetriever(self.vectorstore)
                logging.info("Preloaded vectorstore and retriever.")
            else:
                logging.info("No existing vector store found to preload.")
        except Exception as e:
            logging.error(f"Error during preload: {e}")
            self.is_preloaded = False
    
    def process_documents(self, uploaded_files) -> Dict[str, Any]:
        """Process uploaded documents and build vector database"""
        try:
            new_files = []
            skipped_files = []
            
            for uploaded_file in uploaded_files:
                # Check if file was already processed
                file_hash = self._get_file_hash(uploaded_file)
                file_name = uploaded_file.name
                
                if file_hash in self.processed_files:
                    skipped_files.append(file_name)
                    logging.info(f"Skipping already processed file: {file_name}")
                    continue
                
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
                    for text in texts:
                        text.metadata.update({
                            'file_hash': file_hash
                        })
                    all_texts.extend(texts)
                    self.processed_files[file_hash] = {
                        'filename': uploaded_file.name,
                        'processed_date': current_time,
                        'file_size': len(uploaded_file.getbuffer()),
                        'chunk_count': len(texts),
                        'file_type': uploaded_file.name.split('.')[-1].lower()
                    }
                    processed_count += 1
                    logging.info(f"Processed file: {uploaded_file.name} ({len(texts)} chunks)")
            
            if all_texts:
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
                    if self.vectorstore is None:
                        self.vectorstore = self.vectorstore_service.create_from_documents(all_texts, embeddings)
                    else:
                        self.vectorstore_service.add_documents(all_texts)
                    self.vectorstore_service.persist()
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
                self.documents.extend(all_texts)
                
                # Save metadata
                self._save_metadata()
                
                self.retriever = VectorStoreRetriever(self.vectorstore, self.documents)
                
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
                self.vectorstore = self.vectorstore_service.create_from_documents(texts, embeddings)
                self.documents = texts
                self.retriever = VectorStoreRetriever(self.vectorstore, self.documents)
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
        if not self.vectorstore:
            return []
        
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
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
    
    def get_random_context(self, min_length: int = 200) -> Optional[str]:
        """Get random context from knowledge base for question generation"""
        if not self.documents:
            return None
        
        # Filter documents by minimum length
        suitable_docs = [doc for doc in self.documents if len(doc.page_content) >= min_length]
        
        if not suitable_docs:
            suitable_docs = self.documents  # Fallback to any document
        
        if suitable_docs:
            selected_doc = random.choice(suitable_docs)
            return selected_doc.page_content
        
        return None
    
    def get_context_by_topic(self, topic: str, k: int = 3) -> List[str]:
        """Get context related to a specific topic"""
        if not self.vectorstore:
            return []
        
        try:
            results = self.vectorstore.similarity_search(topic, k=k)
            return [doc.page_content for doc in results]
        except Exception as e:
            logging.error(f"Error getting context by topic: {str(e)}")
            return []
    
    def get_all_contexts(self) -> List[Dict[str, Any]]:
        """Get all document contexts with metadata"""
        contexts = []
        for doc in self.documents:
            contexts.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'length': len(doc.page_content)
            })
        return contexts
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        if not self.documents:
            return {
                'doc_count': 0,
                'chunk_count': 0,
                'total_chars': 0,
                'avg_chunk_size': 0,
                'topic_count': 0,
                'source_files': []
            }
        
        # Calculate statistics
        total_chars = sum(len(doc.page_content) for doc in self.documents)
        avg_chunk_size = total_chars / len(self.documents) if self.documents else 0
        
        # Get unique source files
        source_files = set()
        for doc in self.documents:
            if 'source_file' in doc.metadata:
                source_files.add(doc.metadata['source_file'])
            elif 'original_filename' in doc.metadata:
                source_files.add(doc.metadata['original_filename'])
            elif 'source' in doc.metadata:
                source_files.add(doc.metadata['source'])
        
        # Estimate topic count (this is a simple heuristic)
        topic_count = min(len(source_files) * 3, len(self.documents) // 2)
        topic_count = max(topic_count, 1) if self.documents else 0
        
        return {
            'doc_count': len(source_files),
            'chunk_count': len(self.documents),
            'total_chars': total_chars,
            'avg_chunk_size': int(avg_chunk_size),
            'topic_count': topic_count,
            'source_files': list(source_files)
        }
    
    def clear_knowledge_base(self):
        """Clear the current knowledge base"""
        self.documents = []
        self.processed_files = {}
        # Properly dereference the vectorstore before deleting files
        if self.vectorstore is not None:
            try:
                del self.vectorstore
            except Exception as e:
                logging.warning(f"Error deleting vectorstore: {e}")
        self.vectorstore = None
        import shutil, gc, time, os
        # Run garbage collection to release file handles
        gc.collect()
        time.sleep(0.2)  # Give the OS a moment to release the lock
        if os.path.exists("./chroma_db"):
            try:
                shutil.rmtree("./chroma_db")
            except Exception as e:
                logging.error(f"Error deleting chroma_db directory: {e}")
                raise
    
    def export_knowledge_base(self) -> Dict[str, Any]:
        """Export knowledge base for backup/sharing"""
        return {
            'documents': [
                {
                    'content': doc.page_content,
                    'metadata': doc.metadata
                }
                for doc in self.documents
            ],
            'stats': self.get_stats()
        }
    
    def get_sources(self) -> List[str]:
        """Get list of all source documents"""
        sources = set()
        for doc in self.documents:
            if 'source_file' in doc.metadata:
                sources.add(doc.metadata['source_file'])
            elif 'original_filename' in doc.metadata:
                sources.add(doc.metadata['original_filename'])
            elif 'source' in doc.metadata:
                sources.add(doc.metadata['source'])
        
        return sorted(list(sources))
    
    def get_processed_files_details(self) -> List[Dict[str, Any]]:
        """Get detailed information about all processed files"""
        files_info = []
        for file_hash, metadata in self.processed_files.items():
            files_info.append({
                'file_hash': file_hash,
                'filename': metadata.get('filename', 'Unknown'),
                'processed_date': metadata.get('processed_date', 'Unknown'),
                'file_size': metadata.get('file_size', 0),
                'file_size_mb': round(metadata.get('file_size', 0) / (1024 * 1024), 2),
                'chunk_count': metadata.get('chunk_count', 0),
                'file_type': metadata.get('file_type', 'unknown')
            })
        
        # Sort by processed date (most recent first)
        files_info.sort(key=lambda x: x['processed_date'], reverse=True)
        return files_info
    
    def remove_processed_file(self, file_hash: str) -> bool:
        """Remove a processed file from the knowledge base"""
        try:
            if file_hash not in self.processed_files:
                return False
            
            # Remove from processed files metadata
            filename = self.processed_files[file_hash].get('filename', 'Unknown')
            del self.processed_files[file_hash]
            
            # Remove documents from memory (this is a simplified approach)
            # In a full implementation, you'd need to rebuild the vectorstore
            self.documents = [doc for doc in self.documents 
                            if doc.metadata.get('file_hash') != file_hash]
            
            # Save updated metadata
            self._save_metadata()
            
            logging.info(f"Removed processed file: {filename}")
            return True
            
        except Exception as e:
            logging.error(f"Error removing processed file: {e}")
            return False
    
    def rebuild_vectorstore(self):
        """Rebuild the vectorstore from current documents"""
        try:
            if not self.documents or not self.embedder.get():
                return False
            
            # Clear existing vectorstore
            if os.path.exists(self.persist_directory):
                import shutil
                shutil.rmtree(self.persist_directory)
            
            # Recreate vectorstore
            self.vectorstore = self.vectorstore_service.create_from_documents(self.documents, self.embedder.get())
            
            logging.info("Successfully rebuilt vectorstore")
            return True
            
        except Exception as e:
            logging.error(f"Error rebuilding vectorstore: {e}")
            return False
    
    def is_file_already_processed(self, uploaded_file) -> bool:
        """Check if a file has already been processed"""
        file_hash = self._get_file_hash(uploaded_file)
        return file_hash in self.processed_files 