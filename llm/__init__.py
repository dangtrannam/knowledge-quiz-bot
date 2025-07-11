# llm/__init__.py
"""
LLM abstraction module. Provides unified interface for chat, completion, embedding, TTS, STT, etc.
Supports multiple providers (OpenAI, Gemini, Anthropic, Ollama, etc.) via LiteLLM backend.
"""

from .base import LLMBase
from .litellm_provider import LiteLLMProvider

# You can add more providers here as needed

__all__ = ["LLMBase", "LiteLLMProvider"] 