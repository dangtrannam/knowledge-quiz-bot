import logging
import random
from typing import List, Dict, Any, Optional

class VectorStoreRetriever:
    """
    Handles retrieval operations from a vector store, including similarity search and topic-based context retrieval.
    """
    def __init__(self, vector_store, documents: Optional[List[Any]] = None):
        self.vector_store = vector_store
        self.documents = documents or []

    def similarity_search(self, query: str, k: int = 5, selected_documents: Optional[list] = None) -> List[Dict[str, Any]]:
        """
        Search the vector store for relevant information using similarity search with scores.
        Optionally filter by selected_documents (list of file_hash values).
        """
        if not self.vector_store:
            return []
        try:
            logging.info(f"Searching knowledge base with query: {query}")
            filter_dict = None
            if selected_documents and 'all' not in selected_documents:
                # Chroma supports $in for filtering multiple values
                filter_dict = {"file_hash": {"$in": selected_documents}}
            results = self.vector_store.similarity_search_with_score(query, k=k, filter=filter_dict)
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'relevance_score': score
                })
            logging.info(f"Formatted results: {formatted_results}")
            return formatted_results
        except Exception as e:
            logging.error(f"Error searching knowledge base: {str(e)}")
            return []

    def get_random_context(self, min_length: int = 200, selected_documents: Optional[list] = None) -> Optional[str]:
        """
        Get a random context from the documents for question generation.
        If selected_documents is provided, only use those documents.
        """
        docs = self.documents
        if selected_documents and 'all' not in selected_documents:
            filtered_docs = []
            for doc in docs:
                meta = getattr(doc, 'metadata', {})
                file_id = meta.get('file_hash') or meta.get('source_file') or meta.get('original_filename') or 'Unknown'
                if file_id in selected_documents:
                    filtered_docs.append(doc)
            docs = filtered_docs
        if not docs:
            return None
        suitable_docs = [doc for doc in docs if len(doc.page_content) >= min_length]
        if not suitable_docs:
            suitable_docs = docs  # Fallback to any document
        if suitable_docs:
            selected_doc = random.choice(suitable_docs)
            return selected_doc.page_content
        return None

    def get_context_by_topic(self, topic: str, k: int = 3) -> List[str]:
        """
        Get context related to a specific topic using similarity search.
        """
        if not self.vector_store:
            return []
        try:
            logging.info(f"Getting context by topic: {topic}")
            results = self.vector_store.similarity_search(topic, k=k)
            return [doc.page_content for doc in results]
        except Exception as e:
            logging.error(f"Error getting context by topic: {str(e)}")
            return []

    def get_all_chunks(self, selected_documents: Optional[list] = None) -> List[Dict[str, Any]]:
        """
        Fetch all chunks/documents from the vector store, optionally filtered by selected_documents (file_hash).
        """
        if not self.vector_store:
            return []
        try:
            where = None
            if selected_documents and 'all' not in selected_documents:
                where = {"file_hash": {"$in": selected_documents}}
            # Chroma get() returns a dict with 'documents' and 'metadatas'
            result = self.vector_store.get(where=where, include=["documents", "metadatas"])
            chunks = []
            if result and 'documents' in result and 'metadatas' in result:
                for content, meta in zip(result['documents'], result['metadatas']):
                    chunks.append({
                        'content': content,
                        'metadata': meta
                    })
            return chunks
        except Exception as e:
            logging.error(f"Error fetching all chunks: {str(e)}")
            return [] 