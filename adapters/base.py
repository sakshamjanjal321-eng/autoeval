from abc import ABC, abstractmethod
from typing import Optional
from autoeval.loader import LLMResponse

class BaseAdapter(ABC):
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.kwargs = kwargs

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Sends a request to the LLM and returns the unified LLMResponse."""
        pass
