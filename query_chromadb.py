import sys
from langchain_chroma import Chroma
from embeddings.embedding_model import EmbeddingModel

PERSIST_DIR = "./chroma_db"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python query_chromadb.py 'your query here'")
        sys.exit(1)
    query = sys.argv[1]

    # Load embedding model (should match the one used to build the DB)
    embedder = EmbeddingModel().get()
    if not embedder:
        print("Failed to load embedding model.")
        sys.exit(1)

    # Load Chroma vector store (use embedding_function for compatibility)
    vector_store = Chroma(persist_directory=PERSIST_DIR, embedding_function=embedder) # type: ignore

    # Query
    results = vector_store.similarity_search_with_score(
        query, 
        k=5, 
        filter={"file_type": "pdf"}
    )
    print(f"Top 5 results for query: '{query}'\n")
    for i, (doc, score) in enumerate(results):
        print(f"Result {i+1} (Score: {score:.4f}):")
        print(f"Content: {doc.page_content[:200]}...")
        print(f"Metadata: {doc.metadata}")
        print("-"*60) 