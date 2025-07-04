from langchain_huggingface import HuggingFaceEmbeddings
import logging
from typing import Optional
import torch
import time

class EmbeddingModel:
    """
    Handles initialization and access to the HuggingFace embedding model for document embeddings.
    """
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "auto"):
        # Better device detection and fallback
        if device == "auto":
            if torch.cuda.is_available():
                try:
                    # Test CUDA availability
                    torch.cuda.init()
                    device = "cuda"
                    logging.info("CUDA detected and initialized, using GPU")
                except Exception as e:
                    logging.warning(f"CUDA available but failed to initialize: {e}. Falling back to CPU")
                    device = "cpu"
            else:
                device = "cpu"
                logging.info("CUDA not available, using CPU")
        
        self.model_name = model_name
        self.device = device
        self.embeddings = None
        self._initialize_embeddings()

    def _initialize_embeddings(self):
        """
        Initialize the HuggingFaceEmbeddings model with robust error handling.
        """
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                if not self.embeddings:
                    logging.info(f"Initializing HuggingFace embeddings: {self.model_name} on {self.device} (attempt {attempt + 1}/{max_retries})")
                    
                    # Enhanced model configuration with better device handling
                    model_kwargs = {
                        'device': self.device,
                        'trust_remote_code': True  # Allow custom model code
                    }
                    
                    # Add device_map for better GPU handling
                    if self.device == "cuda":
                        model_kwargs['device_map'] = 'auto'
                    
                    encode_kwargs = {
                        'normalize_embeddings': True,
                        'batch_size': 32  # Reasonable batch size
                    }
                    
                    self.embeddings = HuggingFaceEmbeddings(
                        model_name=self.model_name,
                        model_kwargs=model_kwargs,
                        encode_kwargs=encode_kwargs
                    )
                    
                    # Test the embeddings with a simple query
                    test_embedding = self.embeddings.embed_query("test")
                    if test_embedding and len(test_embedding) > 0:
                        logging.info("Embeddings initialized and tested successfully")
                        return
                    else:
                        raise ValueError("Embedding test failed - returned empty or invalid embedding")
                        
            except Exception as e:
                logging.error(f"Failed to initialize embeddings (attempt {attempt + 1}/{max_retries}): {e}")
                self.embeddings = None
                
                # Try fallback strategies
                if attempt < max_retries - 1:
                    if "meta tensor" in str(e).lower() or "device" in str(e).lower():
                        # Device-related error - try CPU fallback
                        if self.device != "cpu":
                            logging.warning("Device error detected, falling back to CPU")
                            self.device = "cpu"
                        else:
                            # Try different model as last resort
                            logging.warning("Trying alternative embedding model")
                            self.model_name = "sentence-transformers/all-mpnet-base-v2"
                    
                    time.sleep(retry_delay)
                else:
                    logging.error(f"All {max_retries} attempts failed. Embeddings unavailable.")

    def get(self) -> Optional[HuggingFaceEmbeddings]:
        """
        Get the initialized HuggingFaceEmbeddings instance.
        """
        if self.embeddings is None:
            logging.warning("Embeddings not initialized. Attempting re-initialization...")
            self._initialize_embeddings()
        return self.embeddings
    
    def is_ready(self) -> bool:
        """
        Check if embeddings are ready to use.
        """
        return self.embeddings is not None
    
    def reset(self):
        """
        Reset and reinitialize embeddings.
        """
        self.embeddings = None
        self._initialize_embeddings() 