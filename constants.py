# Provider/model configuration and magic strings for the app

PROVIDER_OPTIONS = ["OpenAI", "Gemini", "Anthropic", "Ollama"]

PROVIDER_DEFAULTS = {
    # "OpenAI": {"base_url": "https://aiportalapi.stu-platform.live/jpe", "models": ["GPT-4o-mini"]},
    "OpenAI": {"base_url": "", "models": ["gpt-4o-mini"]},
    "Gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta", "models": ["gemini-pro", "gemini-1.5-pro"]},
    "Anthropic": {"base_url": "https://api.anthropic.com/v1", "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"]},
    "Ollama": {"base_url": "http://localhost:11434", "models": ["llama2", "mistral", "phi"]},
}

DEFAULT_BASE_URL = "https://aiportalapi.stu-platform.live/jpe"
DEFAULT_MODEL = "GPT-4o-mini"
DEFAULT_MODEL_INPUT_TYPE = "predefined" 