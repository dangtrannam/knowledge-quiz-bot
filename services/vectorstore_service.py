from vectorstores.chroma_store import ChromaStoreManager

class VectorStoreService:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.manager = ChromaStoreManager(persist_directory)
        self.vectorstore = None

    def create_from_documents(self, texts, embeddings):
        self.vectorstore = self.manager.create_from_documents(texts, embeddings)
        return self.vectorstore

    def add_documents(self, texts):
        self.manager.add_documents(texts)

    def load_existing(self, embeddings):
        self.vectorstore = self.manager.load_existing(embeddings)
        return self.vectorstore

    def persist(self):
        self.manager.persist() 