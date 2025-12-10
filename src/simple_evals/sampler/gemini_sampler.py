import os
import time
from typing import Any

from google import genai

from ..package_types import Message, MessageList, SamplerBase, SamplerResponse

GEMINI_SYSTEM_MESSAGE = "You are a helpful assistant."


class GeminiCompletionSampler(SamplerBase):
    """
    Sample from Gemini's chat completion API
    """

    def __init__(
        self,
        model: str,
        system_message: str | None = None,
    ):
        api_key = os.environ["GEMINI_API_KEY"]
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.system_message = system_message

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

    def _openai_message_to_gemini_message(self, message: Message) -> dict:
        # Map OpenAI roles to Gemini roles
        role = "model" if message["role"] == "assistant" else message["role"]

        # Gemini expects parts to be objects with 'text' field, not raw strings
        return {"role": role, "parts": [{"text": message["content"]}]}

    def __call__(self, message_list: MessageList, prompt_id: str) -> SamplerResponse:
        # Convert OpenAI messages to Gemini format
        gemini_messages = list(
            map(self._openai_message_to_gemini_message, message_list)
        )

        # Create config with system instruction
        config = None
        if self.system_message:
            config = {"system_instruction": {"parts": [{"text": self.system_message}]}}
            # Add the system message to the list of messages that gets logged, too
            message_list = [
                self._pack_message("system", self.system_message)
            ] + message_list

        trial = 0
        while True:
            try:
                chat_with_history = self.client.chats.create(
                    model=self.model,
                    history=gemini_messages[:-1],  # type: ignore
                    config=config,
                )
                user_message = gemini_messages[-1]["parts"][0]["text"]
                response = chat_with_history.send_message(user_message)
                content = response.text
                if content is None:
                    raise ValueError("Gemini API returned empty response; retrying")
                usage: dict = {}
                if response.usage_metadata is not None:
                    usage = response.usage_metadata.model_dump()
                return SamplerResponse(
                    response_text=content,
                    response_metadata={"usage": usage},
                    actual_queried_message_list=message_list,
                )
            except Exception as e:
                exception_backoff = min(2**trial, 600)  # expontial back off
                print(
                    f"Rate limit exception so wait and retry {trial} after {exception_backoff} sec",
                    e,
                )
                time.sleep(exception_backoff)
                trial += 1
            # unknown error shall throw exception
