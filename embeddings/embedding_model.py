import logging
from typing import Optional, List
from llm.litellm_provider import LiteLLMProvider

class LiteLLMEmbeddings:
    """
    LangChain-compatible embedding wrapper using LiteLLMProvider (Ollama backend).
    Implements embed_query and embed_documents for compatibility with Chroma/VectorStore.
    """
    def __init__(self, model_name: str = "ollama/nomic-embed-text", api_base: str = "http://localhost:11434", api_key: Optional[str] = None):
        self.provider = LiteLLMProvider(
            api_key=api_key,
            api_base=api_base,
            model=model_name
        )
        self.model_name = model_name
        self.api_base = api_base

    def embed_query(self, text: str) -> List[float]:
        # LiteLLMProvider.embed expects a list of strings
        try:
            result = self.provider.embed([text])
            if result and isinstance(result, list) and len(result) > 0:
                return result[0]
            else:
                raise ValueError("No embedding returned from LiteLLMProvider")
        except Exception as e:
            logging.error(f"LiteLLMEmbeddings.embed_query failed: {e}")
            return []

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            return self.provider.embed(texts)
        except Exception as e:
            logging.error(f"LiteLLMEmbeddings.embed_documents failed: {e}")
            return [[] for _ in texts]

class EmbeddingModel:
    """
    Handles initialization and access to the LiteLLM embedding model for document embeddings.
    """
    def __init__(self, model_name: str = "ollama/nomic-embed-text", api_base: str = "http://localhost:11434", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_base = api_base
        self.api_key = api_key
        self.embeddings = None
        self._initialize_embeddings()

    def _initialize_embeddings(self):
        max_retries = 3
        retry_delay = 2
        for attempt in range(max_retries):
            try:
                if not self.embeddings:
                    logging.info(f"Initializing LiteLLM embeddings: {self.model_name} via {self.api_base} (attempt {attempt + 1}/{max_retries})")
                    self.embeddings = LiteLLMEmbeddings(
                        model_name=self.model_name,
                        api_base=self.api_base,
                        api_key=self.api_key
                    )
                    # Test the embeddings with a simple query
                    test_embedding = self.embeddings.embed_query("test")
                    if test_embedding and len(test_embedding) > 0:
                        logging.info("LiteLLMEmbeddings initialized and tested successfully")
                        return
                    else:
                        raise ValueError("Embedding test failed - returned empty or invalid embedding")
            except Exception as e:
                logging.error(f"Failed to initialize LiteLLM embeddings (attempt {attempt + 1}/{max_retries}): {e}")
                self.embeddings = None
                import time
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logging.error(f"All {max_retries} attempts failed. Embeddings unavailable.")

    def get(self) -> Optional[LiteLLMEmbeddings]:
        if self.embeddings is None:
            logging.warning("Embeddings not initialized. Attempting re-initialization...")
            self._initialize_embeddings()
        return self.embeddings

    def is_ready(self) -> bool:
        return self.embeddings is not None

    def reset(self):
        self.embeddings = None
        self._initialize_embeddings() 