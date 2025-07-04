import os
import logging
from typing import List, Any, Optional
# from langchain_community.vectorstores import Chroma  # Deprecated in LangChain 0.2.9
from langchain_chroma import Chroma  # Updated import as per deprecation warning
import shutil

class ChromaStoreManager:
    """
    Handles creation, loading, persistence, clearing, and rebuilding of the Chroma vector store.
    """
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.vectorstore: Optional[Chroma] = None

    def create_from_documents(self, documents: List[Any], embeddings: Any) -> Chroma:
        """
        Create a new Chroma vector store from documents and embeddings.
        """
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=self.persist_directory
        )
        logging.info("Created new vector database")
        return self.vectorstore

    def load_existing(self, embeddings: Any) -> Optional[Chroma]:
        """
        Load an existing Chroma vector store if available.
        """
        if os.path.exists(self.persist_directory):
            try:
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=embeddings
                )
                logging.info("Loaded existing vector database")
                return self.vectorstore
            except Exception as e:
                logging.warning(f"Vector database exists but may be corrupted: {e}")
                self.vectorstore = None
        return None

    def add_documents(self, documents: List[Any]):
        """
        Add new documents to the existing vector store.
        """
        if self.vectorstore:
            self.vectorstore.add_documents(documents)
            logging.info(f"Added {len(documents)} new chunks to existing vector database")

    def persist(self):
        """
        Persist the current vector store to disk.
        (No-op: Persistence is automatic with langchain_chroma if persist_directory is set.)
        """
        if self.vectorstore:
            logging.info("Vector database is persisted automatically by langchain_chroma.")

    def clear(self):
        """
        Clear the persisted vector store from disk.
        """
        if os.path.exists(self.persist_directory):
            shutil.rmtree(self.persist_directory)
            logging.info("Cleared persisted vector database")
        self.vectorstore = None

    def rebuild(self, documents: List[Any], embeddings: Any) -> bool:
        """
        Rebuild the vector store from the provided documents and embeddings.
        """
        self.clear()
        self.create_from_documents(documents, embeddings)
        self.persist()
        logging.info("Successfully rebuilt vectorstore")
        return True 