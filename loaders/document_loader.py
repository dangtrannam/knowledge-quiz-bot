from typing import List, Any
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging

class DocumentLoader:
    """
    Handles loading documents from files and splitting them into chunks for processing.
    """
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def load_document(self, file_path: str, original_filename: str) -> List[Any]:
        """
        Load a document based on its file extension.
        Returns a list of langchain Document objects.
        """
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

    def split_documents(self, documents: List[Any]) -> List[Any]:
        """
        Split a list of langchain Document objects into chunks using the configured splitter.
        """
        return self.text_splitter.split_documents(documents) 