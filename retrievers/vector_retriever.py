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

    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the vector store for relevant information using similarity search with scores.
        """
        if not self.vector_store:
            return []
        try:
            logging.info(f"Searching knowledge base with query: {query}")
            results = self.vector_store.similarity_search_with_score(query, k=k)
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

    def get_random_context(self, min_length: int = 200) -> Optional[str]:
        """
        Get a random context from the documents for question generation.
        """
        if not self.documents:
            return None
        suitable_docs = [doc for doc in self.documents if len(doc.page_content) >= min_length]
        if not suitable_docs:
            suitable_docs = self.documents  # Fallback to any document
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