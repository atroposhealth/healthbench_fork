import time
from typing import Any

import requests
from pydantic import BaseModel

from ..package_types import MessageList, SamplerBase, SamplerResponse


class FineTunedModelDetails(BaseModel):
    """
    Returned by a GET request to the model endpoint.
    """

    name: str


class FineTunedModelCompletionRequest(BaseModel):
    # A list of messages
    prompt: list[dict]


class FineTunedModelOutputSuccess(BaseModel):
    completion: str
    input_tokens: int
    output_tokens: int


class FineTunedModelFailure(BaseModel):
    error: str


class FineTunedModelOutput(BaseModel):
    result: FineTunedModelOutputSuccess | FineTunedModelFailure


class FineTunedSamplerFactory:
    """
    We use a factory here because of the way HealthBench registers models.
    Normally we need to know the model's name at code-authoring time, but we are
    trying to build a model-agnostic interface here that knows how to get a
    prediction from any model available at an endpoint that we control that
    conforms to a particular protocol. Specifically, it will return a
    `FineTunedModelDetails` object when it receives a GET request, and it will
    return a `FineTunedModelOutput` when it receives a POST request containing a
    `FineTunedModelCompletionRequest`.
    """

    def get_sampler(
        self, model_name: str, system_message: str | None = None
    ) -> "FineTunedRemoteSampler":
        return FineTunedRemoteSampler(
            model=model_name,
            system_message=system_message,
        )


class FineTunedRemoteSampler(SamplerBase):
    """
    Sample from a remote endpoint.
    """

    def __init__(
        self,
        model: str,
        system_message: str | None = None,
    ):
        self.model = model
        self.system_message = system_message
        self.endpoint = f"http://localhost:5000/blather/{model}"
        # self.endpoint = "http://localhost:5000/generate"

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
                request_body = FineTunedModelCompletionRequest(prompt=message_list)
                response = requests.post(self.endpoint, json=request_body.model_dump())
                response.raise_for_status()
                model_response = FineTunedModelOutput.model_validate_json(response.text)
                match model_response.result:
                    case FineTunedModelOutputSuccess(
                        completion=completion,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    ):
                        return SamplerResponse(
                            response_text=completion,
                            response_metadata={
                                "usage": {
                                    "input_tokens": input_tokens,
                                    "output_tokens": output_tokens,
                                }
                            },
                            actual_queried_message_list=message_list,
                        )
                    case FineTunedModelFailure(error=error):
                        raise ValueError(f"Error from endpoint:\n{error}")
            except Exception as e:
                exception_backoff = 2**trial  # exponential back off
                print(
                    f"Rate limit exception so wait and retry {trial} after {exception_backoff} sec",
                    e,
                )
                time.sleep(exception_backoff)
                trial += 1
            # unknown error shall throw exception
