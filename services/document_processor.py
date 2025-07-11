import tempfile
from datetime import datetime
from loaders.document_loader import DocumentLoader

class DocumentProcessor:
    def __init__(self):
        self.loader = DocumentLoader()

    def process_uploaded_file(self, uploaded_file):
        file_extension = uploaded_file.name.split('.')[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_file_path = tmp_file.name
        try:
            documents = self.loader.load_document(tmp_file_path, uploaded_file.name)
            if documents:
                texts = self.loader.split_documents(documents)
                current_time = datetime.now().isoformat()
                for text in texts:
                    text.metadata.update({
                        'source_file': uploaded_file.name,
                        'processed_date': current_time,
                        'file_size': len(uploaded_file.getbuffer())
                    })
                return texts
            return []
        finally:
            import os
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def process_text_content(self, text_content: str, source_name: str = "Sample Content"):
        from langchain.schema import Document
        document = Document(page_content=text_content, metadata={"source": source_name})
        texts = self.loader.split_documents([document])
        return texts 