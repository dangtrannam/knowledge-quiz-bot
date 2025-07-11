from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

class LLMBase(ABC):
    """
    Abstract base class for LLM providers.
    """
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        pass

    @abstractmethod
    def completion(self, prompt: str, model: str, **kwargs) -> str:
        pass

    @abstractmethod
    def embed(self, texts: List[str], model: str, **kwargs) -> List[List[float]]:
        pass

    @abstractmethod
    def tts(self, text: str, voice: Optional[str] = None, **kwargs) -> Any:
        pass

    @abstractmethod
    def stt(self, audio: Any, **kwargs) -> str:
        pass 