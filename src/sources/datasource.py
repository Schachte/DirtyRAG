from typing import Any, Dict, Protocol, TypedDict

from llm.llm import LanguageModel
from playwright_helper import PlaywrightHelper


class DatasourceOptions(TypedDict, total=False):
    llm: LanguageModel
    source_params: Dict[str, Any]
    playwright: PlaywrightHelper


class Datasource(Protocol):
    def __init__(self, **opts: DatasourceOptions): ...

    async def pull_content(
        self,
    ) -> str | Dict[str, Any]: ...

    def name(self) -> str: ...

    def get_prompts(self, prompt_helpers: Dict[str, Any]) -> Dict[str, str]: ...
