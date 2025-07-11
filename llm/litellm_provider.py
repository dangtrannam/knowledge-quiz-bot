from .base import LLMBase
from typing import Any, List, Dict, Optional
import litellm
import asyncio
import logging

class LiteLLMProvider(LLMBase):
    """
    LLM provider using LiteLLM for unified access to OpenAI, Gemini, Anthropic, Ollama, etc.
    """
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None, model: str = "openai/gpt-4o-mini"):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        logging.info(f"LiteLLMProvider initialized with model: {self.model}")
        logging.info(f"LiteLLMProvider initialized with api_base: {self.api_base}")

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        response = litellm.completion(
            model=self.model,
            messages=messages,
            api_key=self.api_key,
            api_base=self.api_base,
            stream=False,
            **kwargs
        )
        if asyncio.iscoroutine(response):
            response = asyncio.run(response)
        if isinstance(response, dict):
            data = response  # type: ignore
        elif hasattr(response, 'json') and callable(response.json): # type: ignore
            data = response.json()  # type: ignore[attr-defined]
        else:
            raise TypeError(f"Unexpected response type: {type(response)}")
        return data['choices'][0]['message']['content']  # type: ignore

    def completion(self, prompt: str, **kwargs) -> str:
        response = litellm.completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            api_key=self.api_key,
            api_base=self.api_base,
            stream=False,
            **kwargs
        )
        if asyncio.iscoroutine(response):
            response = asyncio.run(response)
        if isinstance(response, dict):
            data = response  # type: ignore
        elif hasattr(response, 'json') and callable(response.json): # type: ignore
            data = response.json()  # type: ignore[attr-defined]
        else:
            raise TypeError(f"Unexpected response type: {type(response)}")
        return data['choices'][0]['message']['content']  # type: ignore

    def embed(self, texts: List[str], **kwargs) -> List[List[float]]:
        response = litellm.embedding(
            model=self.model,
            input=texts,
            api_key=self.api_key,
            api_base=self.api_base,
            **kwargs
        )
        if asyncio.iscoroutine(response):
            response = asyncio.run(response)
        if isinstance(response, dict):
            data = response  # type: ignore
        elif hasattr(response, 'json') and callable(response.json):
            data = response.json()  # type: ignore[attr-defined]
        else:
            raise TypeError(f"Unexpected response type: {type(response)}")
        return [item['embedding'] for item in data['data']]  # type: ignore

    def tts(self, text: str, voice: Optional[str] = None, **kwargs) -> Any:
        # Placeholder: implement if LiteLLM supports TTS for your providers
        raise NotImplementedError("TTS not implemented in LiteLLMProvider yet.")

    def stt(self, audio: Any, **kwargs) -> str:
        # Placeholder: implement if LiteLLM supports STT for your providers
        raise NotImplementedError("STT not implemented in LiteLLMProvider yet.") 