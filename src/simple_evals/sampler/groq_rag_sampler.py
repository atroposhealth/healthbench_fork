import json
import os
import time
from pathlib import Path
from typing import Any

import groq
from databricks.vector_search.client import VectorSearchClient

from ..package_types import MessageList, SamplerBase, SamplerResponse

LLAMA_4_SYSTEM_MESSAGE = (
    "You are a helpful assistant whose job is to answer medical questions. "
    + "Users may include results from research studies as part of their "
    + "question. If the results are relevant, take them into account when "
    + "formulating your answer. Otherwise, disregard them."
)


class GroqRAGCompletionSampler(SamplerBase):
    """
    Sample from Groq's chat completion API, including relevant content from the
    Atropos content library.
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
        self.image_format = "url"
        vector_search_client = VectorSearchClient(
            workspace_url="https://dbc-7a32c3d1-0aa9.cloud.databricks.com",
            personal_access_token=os.environ["DATABRICKS_API_KEY"],
        )
        self.vector_search_index = vector_search_client.get_index(
            endpoint_name="dbdemos_vs_endpoint",
            index_name="test_uc_yen.dbdemos_rag_chatbot_julian.atropos_cases_6_vs_index",
        )

    def _pack_message(self, role: str, content: Any):
        return {"role": str(role), "content": content}

    def __call__(self, message_list: MessageList, prompt_id: str) -> SamplerResponse:
        # Prepend the system message to the message_list
        if self.system_message:
            message_list = [
                self._pack_message("system", self.system_message)
            ] + message_list
        trial = 0

        # Extract the conversation text to use as input to the vector search
        conversation_turns = []
        for message in message_list:
            conversation_turns.append(message["content"])
        vector_search_input = "\n\n".join(conversation_turns)

        # Retrieve the top response from our vector-search index
        results = self.vector_search_index.similarity_search(
            columns=["id", "case_id", "content"],
            query_text=vector_search_input,
            num_results=1,
        )
        documents_and_scores = results["result"]["data_array"]
        # Extract the match with the highest score
        documents_and_scores.sort(lambda d_and_s: d_and_s[1], reversed=True)
        vector_search_row_id, atropos_case_id, content, _ = documents_and_scores[0]

        # Add the Atropos content to the final message (which is always a user
        # message)
        final_message = message_list[-1]
        final_message["content"] = f"""
Here are the findings of a recent research study, in case the information is helpful:

{content}
"""
        # Write a log to the results directory indicating which case was used
        # for this prompt, along with what the conversation looked like, since
        # it's hard to get that data out of the HealthBench results.
        self._log_rag_info(
            prompt_id, message_list, vector_search_row_id, atropos_case_id
        )

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

    def _log_rag_info(
        self,
        prompt_id: str,
        messages: MessageList,
        vector_search_row_id: str,
        atropos_case_id: str,
    ):
        """
        Logs which atropos case was used in each conversation for later analysis.
        """
        log_dir = self.results_dir / "rag_info"
        if not log_dir.is_dir():
            log_dir.mkdir(parents=True)
        log_info = {
            "prompt_id": prompt_id,
            "vector_search_row_id": vector_search_row_id,
            "atropos_case_id": atropos_case_id,
            "conversation": messages,
        }
        log_file = log_dir / f"{prompt_id}.json"
        log_file.write_text(json.dumps(log_info, indent=2))
        raise NotImplementedError()
