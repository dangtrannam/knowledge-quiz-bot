# Provider/model configuration and magic strings for the app

PROVIDER_OPTIONS = ["OpenAI", "Azure", "Gemini", "Anthropic", "Ollama"]

PROVIDER_DEFAULTS = {
    "OpenAI": {"base_url": "", "models": ["gpt-4o-mini"]},
    "Azure": {"base_url": "https://aiportalapi.stu-platform.live/jpe", "models": ["GPT-4o-mini"]},
    "Gemini": {"base_url": "", "models": ["gemini-pro", "gemini-1.5-pro"]},
    "Anthropic": {"base_url": "", "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"]},
    "Ollama": {"base_url": "http://localhost:11434", "models": ["qwen3:0.6b", "mistral", "phi"]},
}

# Embedding model/provider options (mirroring LLM structure)
EMBEDDING_PROVIDER_OPTIONS = ["OpenAI", "Azure", "Ollama", "HuggingFace"]
EMBEDDING_PROVIDER_DEFAULTS = {
    "OpenAI": {"base_url": "", "models": ["text-embedding-3-small", "text-embedding-3-large"]},
    "Azure": {"base_url": "https://aiportalapi.stu-platform.live/jpe", "models": ["text-embedding-3-small", "text-embedding-3-large"]},
    "Ollama": {"base_url": "http://localhost:11434", "models": ["nomic-embed-text", "all-minilm", "bge-base-en-v1.5"]},
    "HuggingFace": {"base_url": "", "models": ["sentence-transformers/all-MiniLM-L6-v2", "BAAI/bge-base-en-v1.5"]},
}
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_EMBEDDING_BASE_URL = "http://localhost:11434"

DEFAULT_BASE_URL = "https://aiportalapi.stu-platform.live/jpe"
DEFAULT_MODEL = "GPT-4o-mini"
DEFAULT_MODEL_INPUT_TYPE = "predefined" 