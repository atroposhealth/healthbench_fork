import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Self

from databricks.vector_search.client import VectorSearchClient
from dot_slash import dot_slash
from pydantic import BaseModel
from tqdm import tqdm

from ..sampler.groq_rag_sampler import LLAMA_4_RAG_SYSTEM_MESSAGE

RESULTS_DIR = Path(dot_slash("../../../results/"))
EVAL_INPUTS = RESULTS_DIR / "inputs/2025-05-07-06-14-12_oss_eval.jsonl"
RAG_LOGS_DIR = (
    RESULTS_DIR
    / "66a515a50edfaa2c8f21674d4141a124b50ef286/llama-4-maverick-rag/rag_info"
)


class EvalInput(BaseModel):
    """
    Represents a single conversation from the benchmark's input set.
    """

    example_tags: list[str]
    ideal_completions_data: Any | None
    prompt: "list[ConversationTurn]"
    prompt_id: str
    rubrics: "list[RubricCriterion]"
    canary: str

    @classmethod
    def from_inputs(cls, input_filepath: Path) -> list[Self]:
        out = []
        with input_filepath.open() as file:
            for line in file.readlines():
                if line == "":
                    continue
                out.append(cls.model_validate_json(line))
        return out


class ConversationTurn(BaseModel):
    content: str
    role: "ConversationTurnRole"


class ConversationTurnRole(str, Enum):
    User = "user"
    Assistant = "assistant"
    System = "system"


class RubricCriterion(BaseModel):
    criterion: str
    points: int
    tags: list[str]


def main():
    eval_inputs = EvalInput.from_inputs(EVAL_INPUTS)

    vector_search_client = VectorSearchClient(
        workspace_url="https://dbc-7a32c3d1-0aa9.cloud.databricks.com",
        personal_access_token=os.environ["DATABRICKS_API_KEY"],
        disable_notice=True,
    )
    vector_search_index = vector_search_client.get_index(
        endpoint_name="dbdemos_vs_endpoint",
        index_name="test_uc_yen.dbdemos_rag_chatbot_julian.atropos_cases_6_vs_index",
    )

    for eval_input in tqdm(eval_inputs):
        # Open the log file
        log_file = RAG_LOGS_DIR / f"{eval_input.prompt_id}.json"
        log_data = json.loads(log_file.read_text())
        if "similarity_score" in log_data:
            continue

        # Extract the conversation text to use as input to the vector search
        conversation_turns = [LLAMA_4_RAG_SYSTEM_MESSAGE]
        for message in eval_input.prompt:
            conversation_turns.append(message.content)
        vector_search_input = "\n\n".join(conversation_turns)

        # Retrieve the top response from our vector-search index
        results = vector_search_index.similarity_search(
            columns=["id", "case_id", "content"],
            query_text=vector_search_input,
            num_results=1,
            disable_notice=True,
        )
        documents_and_scores = results["result"]["data_array"]
        # We are only asking for one result, so we don't need to sort by score
        vector_search_row_id, atropos_case_id, content, score = documents_and_scores[0]

        # Make sure the Atropos case ID we just got from Alexandria matches the
        # one we got originally
        mismatch_count = 0
        if log_data["atropos_case_id"] != atropos_case_id:
            mismatch_count += 1
            with open(dot_slash("mismatches.txt"), "a") as file:
                file.write(
                    f"Expected {atropos_case_id}, got {log_data['atropos_case_id']} for {eval_input.prompt_id}.json\n"
                )
            continue

        # Add the similarity score
        log_data["similarity_score"] = score
        # Write the log data back out
        log_file.write_text(json.dumps(log_data, indent=2))

    print(f"Total Mismatches: {mismatch_count}")


if __name__ == "__main__":
    main()
