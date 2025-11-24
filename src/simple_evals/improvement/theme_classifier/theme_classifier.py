from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Literal, Type, TypeVar

import polars as pl
from dot_slash import dot_slash
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel
from tqdm import tqdm

from ..models.benchmark_inputs import ConversationTurn, ConversationTurnRole, EvalInput
from ..paths import EVAL_INPUTS


def main():
    train_test = pl.read_csv(dot_slash("../train_test.csv"))
    models = get_candidate_models()
    prediction_manager = LLMClassificationManager(llm_output_dir=Path(dot_slash(".")))
    prompt_ids = get_prompt_ids(train_test)
    for eval_input in tqdm(eval_inputs(prompt_ids)):
        for model in tqdm(models, leave=False):
            model_name: str
            try:
                model_name: str = model.model_name  # type: ignore
            except AttributeError:
                model_name = model.model  # type: ignore
            if prediction_manager.has_theme_prediction(
                eval_input.prompt_id, model=model_name
            ):
                continue
            conversation = format_conversation_for_theme_prediction(eval_input.prompt)
            chain = get_chain(model)
            # chain = but_actually_with_types(chain, ChainInput, ExpectedClassifierOutput)
            result: ExpectedClassifierOutput = chain.invoke(
                {"conversation": conversation}
            )
            prediction_manager.new_theme_prediction(
                LLMThemePrediction(
                    prompt_id=eval_input.prompt_id,
                    model_id=model_name,
                    theme=result.theme,
                )
            )


T = TypeVar("T")
Q = TypeVar("Q")


def but_actually_with_types(
    chain: Runnable, input_type: Type[T], output_type: Type[Q]
) -> Runnable[T, Q]:
    return chain


class ChainInput(BaseModel):
    conversation: str


def get_chain(model: Runnable) -> Runnable:
    return (
        PromptTemplate.from_file(dot_slash("prompt.md"))
        | model
        | PydanticOutputParser(pydantic_object=ExpectedClassifierOutput)
    )


def get_prompt_ids(train_test: pl.DataFrame) -> list[str]:
    random_seed = 2846
    sampled = train_test.filter(pl.col("train_test") == "train").sample(
        10, seed=random_seed
    )
    return sampled["prompt_id"].to_list()


def eval_inputs(prompt_ids: list[str]) -> list[EvalInput]:
    all_inputs = EvalInput.from_inputs(EVAL_INPUTS)
    return [i for i in all_inputs if i.prompt_id in prompt_ids]


def format_conversation_for_theme_prediction(
    conversation: list[ConversationTurn],
) -> str:
    formatted_conversation = ""
    for turn in conversation:
        match turn.role:
            case ConversationTurnRole.System:
                continue
            case ConversationTurnRole.User:
                formatted_conversation += f"Patient: {turn.content}\n"
            case ConversationTurnRole.Assistant:
                formatted_conversation += f"Doctor: {turn.content}\n"
    assert formatted_conversation != ""
    return formatted_conversation


def get_candidate_models() -> list[Runnable]:
    return [
        init_chat_model("google_genai:gemini-3-pro-preview"),
        init_chat_model("google_genai:gemini-2.5-flash"),
        init_chat_model("o3-2025-04-16", model_provider="openai"),
        init_chat_model(
            "meta-llama/llama-4-scout-17b-16e-instruct", model_provider="groq"
        ),
        init_chat_model(
            "meta-llama/llama-4-maverick-17b-128e-instruct", model_provider="groq"
        ),
    ]


class Theme(str, Enum):
    EmergencyReferrals = "Emergency Referrals"
    ContextSeeking = "Context Seeking"
    GlobalHealth = "Global Health"
    HealthDataTasks = "Health Data Tasks"
    ExpertiseTailoredCommunication = "Expertise-tailored Communication"
    RespondingUnderUncertainty = "Responding Under Uncertainty"
    ResponseDepth = "Response Depth"


class ExpectedClassifierOutput(BaseModel):
    explanation_or_reasoning: str
    theme: Theme


@dataclass
class LLMThemePrediction:
    prompt_id: str
    model_id: str
    theme: Theme | Literal["InvalidLLMOutput"]

    def flatten(self) -> dict:
        theme: str
        match self.theme:
            case Theme() as t:
                theme = t.value
            case _:
                theme = self.theme
        return {
            "prompt_id": self.prompt_id,
            "model_id": self.model_id,
            "theme": theme,
        }


class LLMClassificationManager:
    def __init__(self, llm_output_dir: Path):
        assert llm_output_dir.is_dir()
        # Data are stored at the diagnosis level, so the primary key is a
        # combination of case_id, round, model, diagnosis_index
        self.predicted_themes_path = llm_output_dir / "predicted_themes.csv"
        if self.predicted_themes_path.is_file():
            self.predicted_themes = pl.read_csv(self.predicted_themes_path)
        else:
            self.predicted_themes = pl.DataFrame()

    def new_theme_prediction(self, theme_prediction: LLMThemePrediction) -> None:
        self.predicted_themes = pl.concat(
            [self.predicted_themes, pl.DataFrame(theme_prediction.flatten())]
        )
        self.predicted_themes.write_csv(self.predicted_themes_path)

    def has_theme_prediction(self, prompt_id: str, model: str) -> bool:
        if len(self.predicted_themes) == 0:
            return False
        return (
            self.predicted_themes.filter(
                (pl.col("prompt_id") == prompt_id) & (pl.col("model_id") == model)
            ).shape[0]
            > 0
        )


if __name__ == "__main__":
    main()


# communication        -> Expertise-tailored communication ???
# complex_responses    -> Response depth ???
# context_seeking      -> Context seeking
# emergency_referrals  -> Emergency referrals
# global_health        -> Global health
# health_data_tasks    -> Health data tasks
# hedging              -> Responding under uncertainty ???
