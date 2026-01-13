import json
import logging
from enum import Enum
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class Tag(BaseModel):
    """Represents a tag with a name and value."""

    tag: str
    value: str


class IdealCompletionsData(BaseModel):
    """Data about ideal completions for evaluation."""

    ideal_completion: str
    ideal_completions_group: str
    ideal_completions_ref_completions: list[str]


class EvalInput(BaseModel):
    """
    Represents a single conversation from the benchmark's input set.
    """

    example_tags: list[Tag]
    ideal_completions_data: IdealCompletionsData | None
    prompt: "list[ConversationTurn]"
    prompt_id: str
    rubrics: "list[RubricCriterion]"
    canary: str

    @classmethod
    def from_inputs(cls, input_filepath: Path) -> list[Self]:
        """
        Parse EvalInput records from a JSONL file.

        Args:
            input_filepath: Path to the JSONL file to parse

        Returns:
            List of successfully parsed EvalInput instances

        Note:
            Parsing errors are logged but do not stop processing.
            Successfully parsed records are still returned.
        """
        out = []
        errors = []

        with input_filepath.open() as file:
            for line_num, line in enumerate(file, start=1):
                # Skip empty lines
                if line.strip() == "":
                    continue

                try:
                    out.append(cls.model_validate_json(line))
                except json.JSONDecodeError as e:
                    error_msg = f"Line {line_num}: Invalid JSON - {e.msg}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                except ValidationError as e:
                    error_msg = f"Line {line_num}: Validation error - {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        if errors:
            logger.warning(
                f"Parsed {len(out)} records with {len(errors)} errors from {input_filepath}"
            )

        return out

    def flatten(self) -> dict:
        # Parse out the theme
        theme: str | None = None
        for tag in self.example_tags:
            if tag.tag == "theme":
                theme = tag.value
                break
        assert theme is not None
        return {
            "prompt_id": self.prompt_id,
            "theme": theme,
        }


class ConversationTurn(BaseModel):
    content: str
    role: "ConversationTurnRole"


class ConversationTurnRole(str, Enum):
    User = "user"
    Assistant = "assistant"
    System = "system"


class RubricCriterion(BaseModel):
    criterion_id: str
    criterion: str
    points: int
    tags: list[Tag]
