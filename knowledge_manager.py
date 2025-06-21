import os
import tempfile
import hashlib
from typing import List, Dict, Any, Optional
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from chromadb.config import Settings
import random
import logging

class KnowledgeManager:
    def __init__(self):
        self.documents = []
        self.vectorstore = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.embeddings = None
        self.processed_files = set()
        
    def process_documents(self, uploaded_files):
        """Process uploaded documents and build vector database"""
        try:
            # Initialize embeddings if not already done
            if not self.embeddings:
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
            
            all_texts = []
            
            for uploaded_file in uploaded_files:
                # Check if file was already processed
                file_hash = self._get_file_hash(uploaded_file)
                if file_hash in self.processed_files:
                    continue
                
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getbuffer())
                    tmp_file_path = tmp_file.name
                
                try:
                    # Load document based on file type
                    documents = self._load_document(tmp_file_path, uploaded_file.name)
                    
                    if documents:
                        # Split documents into chunks
                        texts = self.text_splitter.split_documents(documents)
                        
                        # Add metadata
                        for text in texts:
                            text.metadata['source_file'] = uploaded_file.name
                            text.metadata['file_hash'] = file_hash
                        
                        all_texts.extend(texts)
                        self.processed_files.add(file_hash)
                        
                finally:
                    # Clean up temporary file
                    os.unlink(tmp_file_path)
            
            if all_texts:
                # Create or update vector database
                if self.vectorstore is None:
                    self.vectorstore = Chroma.from_documents(
                        documents=all_texts,
                        embedding=self.embeddings,
                        persist_directory="./chroma_db"
                    )
                else:
                    # Add new documents to existing vectorstore
                    self.vectorstore.add_documents(all_texts)
                
                # Persist the database
                self.vectorstore.persist()
                
                # Update document list
                self.documents.extend(all_texts)
                
                return True
            
        except Exception as e:
            logging.error(f"Error processing documents: {str(e)}")
            raise e
        
        return False
    
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