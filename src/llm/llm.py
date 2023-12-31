from abc import abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypedDict


class LLMOptions(TypedDict, total=False):
    llm_params: Dict[str, Any]
    model: str


class LanguageModel(Protocol):
    def __init__(self, **opts: LLMOptions): ...

    @abstractmethod
    def chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    def get_response_sync(self, prompt: str) -> Optional[str]: ...
