import os
from typing import List, Optional

from openai import OpenAI

from .llm import LanguageModel, LLMOptions


class OpenAILanguageModel(LanguageModel):
    def __init__(self, **opts: LLMOptions):
        super().__init__(**opts)
        self.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        self.model = opts.get("model", "gpt-3.5-turbo")

    def chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        return super().chunk_text(text, chunk_size)

    def get_response_sync(self, prompt: str) -> Optional[str]:
        """Calls the OpenAI API with the provided prompt and returns the response."""
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
            )

            return chat_completion.choices[0].message.content  # type: ignore[no-any-return]
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
        return None
