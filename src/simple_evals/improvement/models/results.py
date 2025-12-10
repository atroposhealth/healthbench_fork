from enum import Enum
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel


class AllResults(BaseModel):
    score: float
    metrics: dict[str, float | int]
    htmls: list[str]
    convos: "list[list[ConversationTurn]]"
    metadata: "Metadata"

    @classmethod
    def from_file(cls, file: Path | str) -> Self:
        file = Path(file)
        return cls.model_validate_json(file.read_text())


class ConversationTurn(BaseModel):
    content: str
    role: "ConversationTurnRole"


class ConversationTurnRole(str, Enum):
    User = "user"
    Assistant = "assistant"
    System = "system"


class Metadata(BaseModel):
    example_level_metadata: list["ExampleLevelMetadata"]


class ExampleLevelMetadata(BaseModel):
    score: float
    usage: dict[str, Any]
    rubric_items: "list[RubricItem]"
    prompt: list[ConversationTurn]
    completion: list[ConversationTurn]
    prompt_id: str
    completion_id: str


class RubricItem(BaseModel):
    criterion: str
    points: int
    tags: list[str]
    criteria_met: bool
    explanation: str
