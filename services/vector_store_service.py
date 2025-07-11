from vector_stores.chroma_store import ChromaStoreManager

class VectorStoreService:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.manager = ChromaStoreManager(persist_directory)
        self.vector_store = None

    def create_from_documents(self, texts, embeddings):
        self.vector_store = self.manager.create_from_documents(texts, embeddings)
        return self.vector_store

    def add_documents(self, texts):
        self.manager.add_documents(texts)

    def load_existing(self, embeddings):
        self.vector_store = self.manager.load_existing(embeddings)
        return self.vector_store

    def persist(self):
        self.manager.persist()

    def clear_all_data(self):
        self.manager.clear_all_data() 