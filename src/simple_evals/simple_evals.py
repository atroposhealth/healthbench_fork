import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from . import common
from .healthbench_eval import HealthBenchEval, PreSampled, RandomSampler
from .sampler.chat_completion_sampler import (
    OPENAI_SYSTEM_MESSAGE_API,
    ChatCompletionSampler,
    SelfHostedChatCompletionSampler,
)
from .sampler.claude_sampler import ClaudeCompletionSampler
from .sampler.fine_tuned_remote import FineTunedSamplerFactory
from .sampler.gemini_sampler import GEMINI_SYSTEM_MESSAGE, GeminiCompletionSampler
from .sampler.groq_rag_sampler import (
    LLAMA_4_RAG_SYSTEM_MESSAGE,
    GroqRAGCompletionSampler,
)
from .sampler.groq_rag_system_sampler import (
    LLAMA_4_SYSTEM_RAG_SYSTEM_MESSAGE,
    GroqRAGSystemCompletionSampler,
)
from .sampler.groq_sampler import (
    LLAMA_4_SYSTEM_MESSAGE,
    LLAMA_ENHANCED_SYSTEM_MESSAGE,
    LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_1,
    LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_2,
    LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_3,
    LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_4,
    LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_5,
    LLAMA_ENHANCED_SYSTEM_MESSAGE_CONTEXT_AWARENESS,
    TOP_100_MEDICAL_GUIDELINES,
    GroqCompletionSampler,
)
from .sampler.groq_two_pass_sampler import GroqTwoPassCompletionSampler
from .sampler.groq_upper_bound import GroqUpperBoundSampler
from .sampler.responses_sampler import ResponsesSampler, SamplerBase


def main():
    parser = argparse.ArgumentParser(
        description="Run sampling and evaluations using different samplers and evaluations."
    )
    parser.add_argument(
        "--list-models", action="store_true", help="List available models"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Select a model by name. Also accepts a comma-separated list of models.",
    )
    parser.add_argument(
        "--eval",
        type=str,
        help="Select an eval by name. Also accepts a comma-separated list of evals.",
    )
    parser.add_argument(
        "--n-repeats",
        type=int,
        default=1,
        help="Number of repeats to run. Only supported for certain evals.",
    )
    parser.add_argument(
        "--n-threads",
        type=int,
        default=120,
        help="Number of threads to run. Only supported for HealthBench and HealthBenchMeta.",
    )
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument(
        "--examples", type=int, help="Number of examples to use (overrides default)"
    )
    parser.add_argument(
        "--example-list",
        type=Path,
        help="Specific examples to use (takes priority over --examples).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Directory to write the output results.",
        default="/tmp",
    )
    # If this argument is passed and model is "fine-tuned-remote" then the model
    # name will be pulled from the endpoint
    parser.add_argument(
        "--fine-tuned-remote",
        type=bool,
        default=False,
        help="Use the fine-tuned-remote sampler.",
    )
    parser.add_argument(
        "--fine-tuned-system-message",
        type=str,
        help="The system message to use for the fine-tuned model call.",
    )
    parser.add_argument(
        "--fine-tuned-system-message-path",
        type=str,
        help="The path to the system message to use for the fine-tuned model call.",
    )

    args = parser.parse_args()
    print(f"Running with args {args}")

    # Ensure the output directory exists
    output_dir = Path(args.output_dir)
    if not output_dir.is_dir():
        output_dir.mkdir(parents=True)

    available_models = get_available_models(output_dir)
    if args.list_models:
        print("Available models:")
        for model_name in available_models.keys():
            print(f" - {model_name}")
        return

    # Get the models that the user requested
    models_to_evaluate: dict[str, SamplerBase] = {}
    if args.model:
        if args.fine_tuned_remote:
            system_message = ""
            if args.fine_tuned_system_message is not None:
                system_message = args.fine_tuned_system_message
            if args.fine_tuned_system_message_path is not None:
                system_message = Path(args.fine_tuned_system_message_path).read_text()
            print(f"Using system message: {system_message}")
            factory = available_models["fine-tuned-remote"]
            assert isinstance(factory, FineTunedSamplerFactory)
            sampler = factory.get_sampler(
                model_name=args.model,
                system_message=system_message,
            )
            models_to_evaluate = {args.model: sampler}
        else:
            models_chosen = args.model.split(",")
            for model_name in models_chosen:
                if model_name not in available_models:
                    raise RuntimeError(f"Error: Model '{model_name}' not found.")
            for model_name in models_chosen:
                sampler = available_models[model_name]
                assert isinstance(sampler, SamplerBase)
                models_to_evaluate[model_name] = sampler

    # Only use 10 examples if debug mode is on
    n_examples: int | None = args.examples
    if args.debug:
        n_examples = 10
        # If debug mode is on, don't use the provided list of samples
        args.examples_list = None
    example_sampler = get_example_sampler(n_examples, args.example_list)

    grading_sampler = ChatCompletionSampler(
        model="gpt-4.1-2025-04-14",
        system_message=OPENAI_SYSTEM_MESSAGE_API,
        max_tokens=2048,
        # api_key_env_var_name="SINGLE_HEALTHBENCH_RUN",
    )

    # Get the evals that the user requested
    evals_to_run: dict[str, HealthBenchEval] = {}
    if args.eval:
        requested_evals = args.eval.split(",")
        for requested_eval_name in requested_evals:
            try:
                evals_to_run[requested_eval_name] = get_evaluation(
                    requested_eval_name,
                    grading_sampler=grading_sampler,
                    example_sampler=example_sampler,
                    n_repeats=args.n_repeats,
                    n_threads=args.n_threads,
                )
            except Exception as e:
                raise RuntimeError(
                    f"Error: eval '{requested_eval_name}' not found."
                ) from e
    else:
        evals_to_run = {
            eval_name: get_evaluation(
                eval_name,
                grading_sampler=grading_sampler,
                example_sampler=example_sampler,
                n_repeats=args.n_repeats,
                n_threads=args.n_threads,
            )
            for eval_name in [
                "healthbench",
                # "healthbench_hard",
                # "healthbench_consensus",
                # "healthbench_meta",
            ]
        }

    print(evals_to_run)
    debug_suffix = "_DEBUG" if args.debug else ""
    print(debug_suffix)
    mergekey2resultpath = {}
    print(f"Running the following evals: {list(evals_to_run.keys())}")
    print(f"Running evals for the following models: {list(models_to_evaluate.keys())}")

    now = datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M%S")
    for model_name, sampler in models_to_evaluate.items():
        for eval_name, eval_obj in evals_to_run.items():
            result = eval_obj(sampler)
            # ^^^ how to use a sampler
            file_stem = f"{eval_name}_{model_name}"
            # file stem should also include the year, month, day, and time in hours and minutes
            file_stem += f"_{date_str}"
            report_filename = f"{output_dir}/{file_stem}{debug_suffix}.html"
            print(f"Writing report to {report_filename}")
            with open(report_filename, "w") as fh:
                fh.write(common.make_report(result))
            assert result.metrics is not None
            metrics = result.metrics | {"score": result.score}
            # Sort metrics by key
            metrics = dict(sorted(metrics.items()))
            print(metrics)
            result_filename = f"{output_dir}/{file_stem}{debug_suffix}.json"
            with open(result_filename, "w") as f:
                f.write(json.dumps(metrics, indent=2))
            print(f"Writing results to {result_filename}")

            full_result_filename = (
                f"{output_dir}/{file_stem}{debug_suffix}_allresults.json"
            )
            with open(full_result_filename, "w") as f:
                result_dict = {
                    "score": result.score,
                    "metrics": result.metrics,
                    "htmls": result.htmls,
                    "convos": result.convos,
                    "metadata": result.metadata,
                }
                f.write(json.dumps(result_dict, indent=2))
                print(f"Writing all results to {full_result_filename}")

            mergekey2resultpath[f"{file_stem}"] = result_filename
    merge_metrics = []
    for eval_model_name, result_filename in mergekey2resultpath.items():
        try:
            result = json.load(open(result_filename, "r+"))
        except Exception as e:
            print(e, result_filename)
            continue
        result = result.get("f1_score", result.get("score", None))
        eval_name = eval_model_name[: eval_model_name.find("_")]
        model_name = eval_model_name[eval_model_name.find("_") + 1 :]
        merge_metrics.append(
            {"eval_name": eval_name, "model_name": model_name, "metric": result}
        )
    merge_metrics_df = pd.DataFrame(merge_metrics).pivot(
        index=["model_name"], columns="eval_name"
    )
    print("\nAll results: ")
    print(merge_metrics_df.to_markdown())
    return merge_metrics


def get_example_sampler(
    n_examples: int | None, pre_sampled_list: Path | None
) -> RandomSampler | PreSampled | None:
    if n_examples is None and pre_sampled_list is None:
        return None
    if pre_sampled_list is not None:
        prompt_ids = []
        with pre_sampled_list.open() as file:
            for line in file.readlines():
                line = line.strip()
                if line == "":
                    continue
                prompt_ids.append(line)
        print("Using pre-sampled examples.")
        return PreSampled(prompt_ids)
    assert n_examples is not None
    print("Using randomly sampled examples.")
    return RandomSampler(n_examples)


def get_evaluation(
    eval_name: str,
    grading_sampler: ChatCompletionSampler,
    example_sampler: RandomSampler | PreSampled | None,
    n_repeats: int = 1,
    n_threads: int = 1,
):
    # Set num_examples = None to reproduce full evals
    match eval_name:
        case "healthbench":
            return HealthBenchEval(
                grader_model=grading_sampler,
                sampler=example_sampler,
                n_repeats=n_repeats,
                n_threads=n_threads,
                subset_name=None,
            )
        case "healthbench_hard":
            return HealthBenchEval(
                grader_model=grading_sampler,
                sampler=example_sampler,
                n_repeats=n_repeats,
                n_threads=n_threads,
                subset_name="hard",
            )
        case "healthbench_consensus":
            return HealthBenchEval(
                grader_model=grading_sampler,
                sampler=example_sampler,
                n_repeats=n_repeats,
                n_threads=n_threads,
                subset_name="consensus",
            )
        case _:
            raise Exception(f"Unrecognized eval type: {eval_name}")


def get_available_models(
    output_dir: Path,
) -> dict[str, SamplerBase | FineTunedSamplerFactory]:
    return {
        # Reasoning Models
        "o3": ResponsesSampler(
            model="o3-2025-04-16",
            reasoning_model=True,
        ),
        "gpt-5.1": ChatCompletionSampler(
            model="gpt-5.1-2025-11-13",
            system_message=OPENAI_SYSTEM_MESSAGE_API,
            max_tokens=2048,
        ),
        "gpt-5.2-pro": ChatCompletionSampler(
            model="gpt-5.2-pro-2025-12-11",
            system_message=OPENAI_SYSTEM_MESSAGE_API,
            max_tokens=2048,
        ),
        "claude-opus-4.1": ClaudeCompletionSampler(
            model="claude-opus-4-1-20250805",
        ),
        # Gemini
        "gemini-3": GeminiCompletionSampler(
            model="gemini-3-pro-preview",
            system_message=GEMINI_SYSTEM_MESSAGE,
        ),
        # Llama models:
        "llama-3.1-8b": GroqCompletionSampler(
            model="llama-3.1-8b-instant",
            system_message=LLAMA_4_SYSTEM_MESSAGE,
        ),
        "llama-3.1-8b-temp-0": GroqCompletionSampler(
            model="llama-3.1-8b-instant",
            system_message=LLAMA_4_SYSTEM_MESSAGE,
            temperature=0.0,
        ),
        "llama-3.1-8b-enhanced-prompt-completeness-3": GroqCompletionSampler(
            model="llama-3.1-8b-instant",
            system_message=LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_3,
        ),
        "llama-3.3-70b": GroqCompletionSampler(
            model="llama-3.3-70b-versatile",
            system_message=LLAMA_4_SYSTEM_MESSAGE,
        ),
        "llama-3.3-70b-enhanced-prompt-completeness-3": GroqCompletionSampler(
            model="llama-3.3-70b-versatile",
            system_message=LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_3,
        ),
        "llama-4-scout": GroqCompletionSampler(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            system_message=LLAMA_4_SYSTEM_MESSAGE,
        ),
        "llama-4-maverick": GroqCompletionSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            system_message=LLAMA_4_SYSTEM_MESSAGE,
        ),
        "llama-4-scout-rag": GroqRAGCompletionSampler(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            system_message=LLAMA_4_RAG_SYSTEM_MESSAGE,
            results_dir=output_dir,
        ),
        "llama-4-maverick-rag": GroqRAGCompletionSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            system_message=LLAMA_4_RAG_SYSTEM_MESSAGE,
            results_dir=output_dir,
        ),
        "llama-4-scout-enhanced-prompt": GroqCompletionSampler(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            system_message=LLAMA_ENHANCED_SYSTEM_MESSAGE,
        ),
        "llama-4-scout-enhanced-prompt-completeness-3": GroqCompletionSampler(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            system_message=LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_3,
        ),
        "llama-4-maverick-enhanced-prompt": GroqCompletionSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            system_message=LLAMA_ENHANCED_SYSTEM_MESSAGE,
        ),
        "llama-4-maverick-enhanced-prompt-completeness-1": GroqCompletionSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            system_message=LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_1,
        ),
        "llama-4-maverick-enhanced-prompt-completeness-2": GroqCompletionSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            system_message=LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_2,
        ),
        "llama-4-maverick-enhanced-prompt-completeness-3": GroqCompletionSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            system_message=LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_3,
        ),
        "llama-4-maverick-enhanced-prompt-completeness-4": GroqCompletionSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            system_message=LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_4,
        ),
        "llama-4-maverick-enhanced-prompt-completeness-5": GroqCompletionSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            system_message=LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_5,
        ),
        "llama-4-maverick-enhanced-prompt-context-awareness": GroqCompletionSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            system_message=LLAMA_ENHANCED_SYSTEM_MESSAGE_CONTEXT_AWARENESS,
        ),
        # Different Temperatures
        "llama-4-maverick-temp0": GroqCompletionSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            system_message=LLAMA_4_SYSTEM_MESSAGE,
            temperature=0.0,
        ),
        "llama-4-maverick-temp25": GroqCompletionSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            system_message=LLAMA_4_SYSTEM_MESSAGE,
            temperature=0.25,
        ),
        "llama-4-maverick-temp75": GroqCompletionSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            system_message=LLAMA_4_SYSTEM_MESSAGE,
            temperature=0.75,
        ),
        "llama-4-maverick-temp1": GroqCompletionSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            system_message=LLAMA_4_SYSTEM_MESSAGE,
            temperature=1,
        ),
        # Two-pass
        "llama-4-maverick-two-pass": GroqTwoPassCompletionSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
        ),
        # Fine-tuned model caller
        "fine-tuned-remote": FineTunedSamplerFactory(),
        "llama-4-maverick-self-hosted-lora": SelfHostedChatCompletionSampler(
            model="llama-4-fine-tune-lora",
            system_message=LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_3,
            base_url="http://127.0.0.1:5000",
        ),
        # RAG with new VSI
        "llama-4-maverick-rag-2": GroqRAGSystemCompletionSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            system_message=LLAMA_4_SYSTEM_RAG_SYSTEM_MESSAGE,
            results_dir=output_dir,
        ),
        "llama-4-maverick-upper-bound": GroqUpperBoundSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            system_message=LLAMA_4_SYSTEM_RAG_SYSTEM_MESSAGE,
            results_dir=output_dir,
        ),
        # Neil's rubrics and prompts - added Thursday, Jan. 15
        "llama-4-maverick-top-100-guidelines": GroqCompletionSampler(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            system_message=TOP_100_MEDICAL_GUIDELINES,
        ),
    }


if __name__ == "__main__":
    main()
