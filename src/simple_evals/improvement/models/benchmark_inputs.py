from enum import Enum
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel


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

    def flatten(self) -> dict:
        # Parse out the theme
        theme: str | None = None
        for tag in self.example_tags:
            parts = tag.split(":")
            if parts[0] == "theme":
                theme = parts[1]
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
    criterion: str
    points: int
    tags: list[str]
