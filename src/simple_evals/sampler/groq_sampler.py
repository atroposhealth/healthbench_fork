import os
import time
from pathlib import Path
from typing import Any

import groq
from dot_slash import dot_slash

from ..package_types import MessageList, SamplerBase, SamplerResponse

LLAMA_4_SYSTEM_MESSAGE = "You are a helpful assistant."

LLAMA_ENHANCED_SYSTEM_MESSAGE = Path(dot_slash("enhanced_system_prompt.md")).read_text()

COMPLETENESS_PROMPT_DIR = Path(
    dot_slash("../improvement/analyzing_completeness/prompts")
)
LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_1 = (
    COMPLETENESS_PROMPT_DIR / "1.md"
).read_text()
LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_2 = (
    COMPLETENESS_PROMPT_DIR / "2.md"
).read_text()
LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_3 = (
    COMPLETENESS_PROMPT_DIR / "3.md"
).read_text()
LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_4 = (
    COMPLETENESS_PROMPT_DIR / "4.md"
).read_text()
LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_5 = (
    COMPLETENESS_PROMPT_DIR / "5.md"
).read_text()

CONTEXT_AWARENESS_PROMPT_DIR = Path(
    dot_slash("../improvement/analyzing_context_awareness/prompts")
)
LLAMA_ENHANCED_SYSTEM_MESSAGE_CONTEXT_AWARENESS = (
    CONTEXT_AWARENESS_PROMPT_DIR / "context_awareness.md"
).read_text()

TOP_100_MEDICAL_GUIDELINES = Path(
    dot_slash("top_100_medical_guidelines.md")
).read_text()


class GroqCompletionSampler(SamplerBase):
    """
    Sample from Groq's chat completion API
    """

    def __init__(
        self,
        model: str,
        system_message: str | None = None,
        temperature: float = 0.5,
        max_tokens: int = 1024,
    ):
        api_key = os.environ["GROQ_API_KEY"]
        self.client = groq.Groq(api_key=api_key)
        self.model = model
        self.system_message = system_message
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.image_format = "url"

    def _handle_image(
        self,
        image: str,
        encoding: str = "base64",
        format: str = "png",
        fovea: int = 768,
    ):
        new_image = {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/{format};{encoding},{image}",
            },
        }
        return new_image

    def _handle_text(self, text: str):
        return {"type": "text", "text": text}

    def _pack_message(self, role: str, content: Any):
        return {"role": str(role), "content": content}

    def __call__(self, message_list: MessageList, prompt_id: str) -> SamplerResponse:
        if self.system_message:
            message_list = [
                self._pack_message("system", self.system_message)
            ] + message_list
        trial = 0
        while True:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=message_list,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("OpenAI API returned empty response; retrying")
                return SamplerResponse(
                    response_text=content,
                    response_metadata={"usage": response.usage},
                    actual_queried_message_list=message_list,
                )
            # NOTE: BadRequestError is triggered once for MMMU, please uncomment if you are reruning MMMU
            except groq.BadRequestError as e:
                print("Bad Request Error", e)
                return SamplerResponse(
                    response_text="No response (bad request).",
                    response_metadata={"usage": None},
                    actual_queried_message_list=message_list,
                )
            except Exception as e:
                exception_backoff = 2**trial  # expontial back off
                print(
                    f"Rate limit exception so wait and retry {trial} after {exception_backoff} sec",
                    e,
                )
                time.sleep(exception_backoff)
                trial += 1
            # unknown error shall throw exception
