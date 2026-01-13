import os
import time
from pathlib import Path
from typing import Any

import groq
from dot_slash import dot_slash

from ..package_types import MessageList, SamplerBase, SamplerResponse
from .benchmark_inputs import EvalInput

LLAMA_4_SYSTEM_RAG_SYSTEM_MESSAGE = (
    "You are a helpful assistant whose job is to answer medical questions. "
)


class GroqUpperBoundSampler(SamplerBase):
    """
    Sample from Groq's chat completion API, including the rubric criteria for
    the benchmark input in the system prompt. We are using this to get a sense
    of upper-bound performance on the benchmark.
    """

    def __init__(
        self,
        model: str,
        results_dir: Path,  # Specifies where to write the RAG logs.
        system_message: str | None = None,
        temperature: float = 0.5,
        max_tokens: int = 1024,
    ):
        self.client = groq.Groq(api_key=os.environ["GROQ_API_KEY"])
        self.model = model
        self.results_dir = results_dir
        self.system_message = system_message
        self.temperature = temperature
        self.max_tokens = max_tokens
        evaluation_inputs = EvalInput.from_inputs(
            Path(dot_slash("benchmark_inputs_reformatted.jsonl"))
        )
        self.evaluation_inputs_by_prompt_id = {
            i.prompt_id: i for i in evaluation_inputs
        }

    def _pack_message(self, role: str, content: Any):
        return

    def __call__(self, message_list: MessageList, prompt_id: str) -> SamplerResponse:
        # Extract the conversation text to use as input to the vector search
        conversation_turns = []
        for message in message_list:
            conversation_turns.append(message["content"])

        eval_inputs_for_prompt = self.evaluation_inputs_by_prompt_id[prompt_id]
        criteria_string = ""
        for criterion in eval_inputs_for_prompt.rubrics:
            criteria_string += (
                f"Criterion: {criterion.criterion}\n"
                + f"Points possible: {criterion.points}\n\n"
            )

        # Build the system message with study content included
        base_system_message = self.system_message or ""
        system_message_with_study = f"""{base_system_message}

Your response to the user's question will be graded using the following rubric. Each rubric 
criterion is associated with a score that will be awarded if the criterion is met. Note that 
rubric criteria with negative scores indicate undesirable aspects of the response. For example, 
a criterion that looks like

Criterion: Calls the user by the wrong name.
Points possible: -5

indicates that calling the user by the wrong name is undesirable, as it will result in a 
five point deduction from the score.

Here are the rubric criteria:

<begin_rubric_criteria>

{criteria_string}

<end_rubric_criteria>
""".strip()

        # Prepend the system message (with study content) to the message_list
        message_list = [
            {"role": "system", "content": system_message_with_study}
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
