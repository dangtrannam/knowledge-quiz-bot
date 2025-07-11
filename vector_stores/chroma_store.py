import os
import logging
from typing import List, Any, Optional
from langchain_chroma import Chroma

class ChromaStoreManager:
    """
    Handles creation, loading, persistence, clearing, and rebuilding of the Chroma vector store.
    """
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.vector_store: Optional[Chroma] = None

    def create_from_documents(self, documents: List[Any], embeddings: Any) -> Chroma:
        """
        Create a new Chroma vector store from documents and embeddings.
        """
        self.vector_store = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=self.persist_directory
        )
        logging.info("Created new vector database")
        return self.vector_store

    def load_existing(self, embeddings: Any) -> Optional[Chroma]:
        """
        Load an existing Chroma vector store if available.
        """
        if os.path.exists(self.persist_directory):
            try:
                self.vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=embeddings
                )
                logging.info("Loaded existing vector database")
                return self.vector_store
            except Exception as e:
                logging.warning(f"Vector database exists but may be corrupted: {e}")
                self.vector_store = None
        return None

    def add_documents(self, documents: List[Any]):
        """
        Add new documents to the existing vector store.
        """
        if self.vector_store:
            self.vector_store.add_documents(documents)
            logging.info(f"Added {len(documents)} new chunks to existing vector database")

    def persist(self):
        """
        Persist the current vector store to disk.
        (No-op: Persistence is automatic with langchain_chroma if persist_directory is set.)
        """
        if self.vector_store:
            logging.info("Vector database is persisted automatically by langchain_chroma.")

    def clear_all_data(self):
        """
        Clear all data from the Chroma vector store without deleting the underlying files.
        """
        if self.vector_store:
            try:
                if hasattr(self.vector_store, 'delete_collection'):
                    self.vector_store.delete_collection()
                    logging.info("Cleared all data from Chroma vector_store using delete_collection().")
                elif hasattr(self.vector_store, 'delete'):
                    self.vector_store.delete(ids=None)
                    logging.info("Cleared all data from Chroma vector_store using delete(ids=None).")
                else:
                    logging.warning("No supported method to clear all data from Chroma vector_store.")
            except Exception as e:
                logging.error(f"Error clearing all data from Chroma vector_store: {e}")

    def rebuild(self, documents: List[Any], embeddings: Any) -> bool:
        """
        Rebuild the vector store from the provided documents and embeddings.
        """
        self.clear_all_data()
        self.create_from_documents(documents, embeddings)
        self.persist()
        logging.info("Successfully rebuilt vector_store")
        return True 