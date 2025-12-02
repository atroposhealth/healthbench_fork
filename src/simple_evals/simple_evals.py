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
)
from .sampler.claude_sampler import ClaudeCompletionSampler
from .sampler.groq_rag_sampler import (
    LLAMA_4_RAG_SYSTEM_MESSAGE,
    GroqRAGCompletionSampler,
)
from .sampler.groq_sampler import (
    LLAMA_4_SYSTEM_MESSAGE,
    LLAMA_ENHANCED_SYSTEM_MESSAGE,
    LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_1,
    LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_2,
    LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_3,
    LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_4,
    LLAMA_ENHANCED_SYSTEM_MESSAGE_COMPLETENESS_5,
    GroqCompletionSampler,
)
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
    if args.model:
        models_chosen = args.model.split(",")
        for model_name in models_chosen:
            if model_name not in available_models:
                raise RuntimeError(f"Error: Model '{model_name}' not found.")
        models_to_evaluate = {
            model_name: available_models[model_name] for model_name in models_chosen
        }

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


def get_available_models(output_dir: Path) -> dict[str, SamplerBase]:
    return {
        # # Reasoning Models
        "o3": ResponsesSampler(
            model="o3-2025-04-16",
            reasoning_model=True,
        ),
        "claude-opus-4.1": ClaudeCompletionSampler(
            model="claude-opus-4-1-20250805",
        ),
        # Llama models:
        "llama-3.1-8b": GroqCompletionSampler(
            model="llama-3.1-8b-instant",
            system_message=LLAMA_4_SYSTEM_MESSAGE,
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
    }


if __name__ == "__main__":
    main()
