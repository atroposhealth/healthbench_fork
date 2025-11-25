import json
import os
from dataclasses import dataclass
from pathlib import Path

from databricks import sql

from .models.benchmark_inputs import EvalInput
from .models.results import AllResults, ExampleLevelMetadata
from .paths import EVAL_INPUTS


class EvalInputReader:
    def __init__(self, path_to_inputs: Path | None = None):
        if path_to_inputs is None:
            path_to_inputs = EVAL_INPUTS
        self.inputs = EvalInput.from_inputs(path_to_inputs)
        self.inputs_by_prompt_id = {i.prompt_id: i for i in self.inputs}

    def get_by_prompt_id(self, prompt_id: str) -> EvalInput | None:
        return self.inputs_by_prompt_id.get(prompt_id)


@dataclass
class AlexandriaDocument:
    case_id: str
    content: str


def get_alexandria_document_by_case_id(case_id: str) -> AlexandriaDocument | None:
    with sql.connect(
        server_hostname="dbc-7a32c3d1-0aa9.cloud.databricks.com",
        http_path="sql/protocolv1/o/1725462443952779/1121-234632-dbrcjc42",
        access_token=os.environ["DATABRICKS_API_KEY"],
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM test_uc_yen.dbdemos_rag_chatbot_julian.atropos_cases_6 WHERE case_id = %s",
                [case_id],  # type: ignore
            )
            results = cursor.fetchall()
            if len(results) == 0:
                return None
            return AlexandriaDocument(
                case_id=case_id,
                content=results[0].content,
            )


class RagLogReader:
    def __init__(self, rag_log_dir: Path):
        assert rag_log_dir.is_dir()
        self.rag_log_dir = rag_log_dir

    def get_case_id_for_prompt_id(self, prompt_id: str) -> str:
        log_path = self.rag_log_dir / f"{prompt_id}.json"
        log_info = json.loads(log_path.read_text())
        return log_info["atropos_case_id"]


class ExampleLevelMetadataReader:
    """
    Returns example-level metadata objects by prompt_id.
    """

    def __init__(self, result_file: Path):
        all_results = AllResults.from_file(result_file)
        self.metadata_by_prompt_id = {
            m.prompt_id: m for m in all_results.metadata.example_level_metadata
        }

    def by_prompt_id(self, prompt_id: str) -> ExampleLevelMetadata:
        return self.metadata_by_prompt_id[prompt_id]
