import os
import time

import groq

from .. import common
from ..package_types import MessageList, SamplerBase, SamplerResponse

LLAMA_4_SYSTEM_MESSAGE = "You are a helpful assistant."


class GroqCompletionSampler(SamplerBase):
    def __init__(
        self,
        model: str,
        system_message: str | None = None,
        temperature: float = 0.0,  # default in Anthropic example
        max_tokens: int = 4096,
    ):
        api_key = os.environ["GROQ_API_KEY"]
        self.client = groq.Groq(api_key=api_key)
        self.model = model
        self.system_message = system_message
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.image_format = "base64"

    def _handle_image(
        self,
        image: str,
        encoding: str = "base64",
        format: str = "png",
        fovea: int = 768,
    ):
        new_image = {
            "type": "image",
            "source": {
                "type": encoding,
                "media_type": f"image/{format}",
                "data": image,
            },
        }
        return new_image

    def _handle_text(self, text):
        return {"type": "text", "text": text}

    def _pack_message(self, role, content):
        return {"role": str(role), "content": content}

    def __call__(self, message_list: MessageList, prompt_id: str) -> SamplerResponse:
        trial = 0
        while True:
            try:
                if not common.has_only_user_assistant_messages(message_list):
                    raise ValueError(
                        f"Claude sampler only supports user and assistant messages, got {message_list}"
                    )
                if self.system_message:
                    response_message = self.client.chat.completions.create(
                        model=self.model,
                        messages=message_list,
                        # system=self.system_message,
                        # max_tokens=self.max_tokens,
                        # temperature=self.temperature,
                    )
                    claude_input_messages: MessageList = [
                        {"role": "system", "content": self.system_message}
                    ] + message_list
                else:
                    response_message = self.client.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        messages=message_list,
                    )
                    claude_input_messages = message_list
                response_text = response_message.content[0].text
                return SamplerResponse(
                    response_text=response_text,
                    response_metadata={},
                    actual_queried_message_list=claude_input_messages,
                )
            except anthropic.RateLimitError as e:
                exception_backoff = 2**trial  # expontial back off
                print(
                    f"Rate limit exception so wait and retry {trial} after {exception_backoff} sec",
                    e,
                )
                time.sleep(exception_backoff)
                trial += 1
            # unknown error shall throw exception
