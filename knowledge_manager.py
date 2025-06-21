import os
import tempfile
import hashlib
import json
import pickle
from typing import List, Dict, Any, Optional
from datetime import datetime
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from chromadb.config import Settings
import random
import logging

class KnowledgeManager:
    def __init__(self, persist_directory: str = "./chroma_db", metadata_file: str = "./processed_files.json"):
        self.documents = []
        self.vectorstore = None
        self.persist_directory = persist_directory
        self.metadata_file = metadata_file
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.embeddings = None
        self.processed_files = {}  # Changed to dict to store metadata
        self.is_preloaded = False
        
        # Initialize embeddings early
        self._initialize_embeddings()
        
        # Load existing metadata and preload if available
        self._load_metadata()
        self._preload_existing_documents()
    
    def _initialize_embeddings(self):
        """Initialize embeddings model early"""
        try:
            if not self.embeddings:
                logging.info("Initializing HuggingFace embeddings...")
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
                logging.info("Embeddings initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize embeddings: {e}")
    
    def _load_metadata(self):
        """Load metadata about processed files"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.processed_files = json.load(f)
                logging.info(f"Loaded metadata for {len(self.processed_files)} processed files")
            else:
                self.processed_files = {}
                logging.info("No existing metadata found, starting fresh")
        except Exception as e:
            logging.error(f"Error loading metadata: {e}")
            self.processed_files = {}
    
    def _save_metadata(self):
        """Save metadata about processed files"""
        try:
            os.makedirs(os.path.dirname(self.metadata_file) if os.path.dirname(self.metadata_file) else '.', exist_ok=True)
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_files, f, indent=2, ensure_ascii=False)
            logging.info(f"Saved metadata for {len(self.processed_files)} processed files")
        except Exception as e:
            logging.error(f"Error saving metadata: {e}")
    
    def _preload_existing_documents(self):
        """Preload existing vector database if available"""
        try:
            if os.path.exists(self.persist_directory) and self.embeddings:
                logging.info("Attempting to preload existing vector database...")
                
                # Try to load existing vectorstore
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                
                # Check if vectorstore has documents
                try:
                    # Try to get a sample to verify the vectorstore works
                    sample_results = self.vectorstore.similarity_search("test", k=1)
                    if sample_results:
                        logging.info(f"Successfully preloaded vector database with documents")
                        self.is_preloaded = True
                        
                        # Reconstruct documents list from metadata
                        self._reconstruct_documents_from_metadata()
                    else:
                        logging.info("Vector database exists but appears empty")
                except Exception as e:
                    logging.warning(f"Vector database exists but may be corrupted: {e}")
                    self.vectorstore = None
                    
        except Exception as e:
            logging.error(f"Error preloading documents: {e}")
            self.vectorstore = None
            self.is_preloaded = False
    
    def _reconstruct_documents_from_metadata(self):
        """Reconstruct documents list from saved metadata"""
        try:
            # This is a simplified reconstruction - in a full implementation,
            # you might want to save document content separately
            self.documents = []
            
            # For now, we'll rely on the vectorstore for content
            # and use metadata for file tracking
            logging.info(f"Reconstructed knowledge base from {len(self.processed_files)} processed files")
            
        except Exception as e:
            logging.error(f"Error reconstructing documents: {e}")
    
    def get_preload_status(self) -> Dict[str, Any]:
        """Get information about preloaded content"""
        return {
            'is_preloaded': self.is_preloaded,
            'processed_files_count': len(self.processed_files),
            'processed_files': list(self.processed_files.keys()) if self.processed_files else [],
            'vectorstore_available': self.vectorstore is not None,
            'embeddings_ready': self.embeddings is not None
        }

    def process_documents(self, uploaded_files):
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
                # Save uploaded file temporarily
                file_extension = uploaded_file.name.split('.')[-1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
                    tmp_file.write(uploaded_file.getbuffer())
                    tmp_file_path = tmp_file.name
                
                try:
                    # Load document based on file type
                    documents = self._load_document(tmp_file_path, uploaded_file.name)
                    
                    if documents:
                        # Split documents into chunks
                        texts = self.text_splitter.split_documents(documents)
                        
                        # Add enhanced metadata
                        current_time = datetime.now().isoformat()
                        for text in texts:
                            text.metadata.update({
                                'source_file': uploaded_file.name,
                                'file_hash': file_hash,
                                'processed_date': current_time,
                                'chunk_index': len(all_texts) + texts.index(text),
                                'file_size': len(uploaded_file.getbuffer())
                            })
                        
                        all_texts.extend(texts)
                        
                        # Update processed files metadata
                        self.processed_files[file_hash] = {
                            'filename': uploaded_file.name,
                            'processed_date': current_time,
                            'file_size': len(uploaded_file.getbuffer()),
                            'chunk_count': len(texts),
                            'file_type': file_extension.lower()
                        }
                        
                        processed_count += 1
                        logging.info(f"Processed file: {uploaded_file.name} ({len(texts)} chunks)")
                        
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
            
            if all_texts:
                # Create or update vector database
                if self.vectorstore is None:
                    self.vectorstore = Chroma.from_documents(
                        documents=all_texts,
                        embedding=self.embeddings,
                        persist_directory=self.persist_directory
                    )
                    logging.info("Created new vector database")
                else:
                    # Add new documents to existing vectorstore
                    self.vectorstore.add_documents(all_texts)
                    logging.info(f"Added {len(all_texts)} new chunks to existing vector database")
                
                # Persist the database
                self.vectorstore.persist()
                
                # Update document list
                self.documents.extend(all_texts)
                
                # Save metadata
                self._save_metadata()
                
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
            if not self.embeddings:
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
            
            # Create document-like object
            from langchain.schema import Document
            document = Document(page_content=text_content, metadata={"source": source_name})
            
            # Split into chunks
            texts = self.text_splitter.split_documents([document])
            
            # Create vector database
            self.vectorstore = Chroma.from_documents(
                documents=texts,
                embedding=self.embeddings,
                persist_directory="./chroma_db"
            )
            
            self.documents = texts
            return True
            
        except Exception as e:
            logging.error(f"Error processing text content: {str(e)}")
            raise e
    
    def _load_document(self, file_path: str, original_filename: str):
        """Load document based on file extension"""
        file_extension = original_filename.split('.')[-1].lower()
        
        try:
            if file_extension == 'pdf':
                loader = PyPDFLoader(file_path)
            elif file_extension == 'txt':
                loader = TextLoader(file_path, encoding='utf-8')
            elif file_extension in ['docx', 'doc']:
                loader = Docx2txtLoader(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            documents = loader.load()
            
            # Add source metadata
            for doc in documents:
                doc.metadata['original_filename'] = original_filename
                doc.metadata['file_type'] = file_extension
            
            return documents
            
        except Exception as e:
            logging.error(f"Error loading document {original_filename}: {str(e)}")
            return []
    
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
        self.vectorstore = None
        self.processed_files = set()
        
        # Clear persisted database
        import shutil
        if os.path.exists("./chroma_db"):
            shutil.rmtree("./chroma_db")
    
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
            if not self.documents or not self.embeddings:
                return False
            
            # Clear existing vectorstore
            if os.path.exists(self.persist_directory):
                import shutil
                shutil.rmtree(self.persist_directory)
            
            # Recreate vectorstore
            self.vectorstore = Chroma.from_documents(
                documents=self.documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            self.vectorstore.persist()
            logging.info("Successfully rebuilt vectorstore")
            return True
            
        except Exception as e:
            logging.error(f"Error rebuilding vectorstore: {e}")
            return False
    
    def is_file_already_processed(self, uploaded_file) -> bool:
        """Check if a file has already been processed"""
        file_hash = self._get_file_hash(uploaded_file)
        return file_hash in self.processed_files 