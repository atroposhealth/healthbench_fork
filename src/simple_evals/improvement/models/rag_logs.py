from enum import Enum
from pathlib import Path
from typing import Self

from pydantic import BaseModel


class RAGLog(BaseModel):
    """
    Represents the logging output from a single RAG-enabled run.
    """

    prompt_id: str
    vector_search_row_id: float
    atropos_case_id: str
    similarity_score: float
    conversation: "list[ConversationTurn]"

    @classmethod
    def from_log_dir(cls, log_dir: Path | str) -> list[Self]:
        log_dir = Path(log_dir)
        out = []
        for filepath in log_dir.glob("*.json"):
            out.append(cls.model_validate_json(filepath.read_text()))
        return out


class ConversationTurn(BaseModel):
    content: str
    role: "ConversationTurnRole"


class ConversationTurnRole(str, Enum):
    User = "user"
    Assistant = "assistant"
    System = "system"
