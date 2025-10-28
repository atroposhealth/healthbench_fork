import json
from pathlib import Path

from dot_slash import dot_slash

# FILEPATH = Path(
#     dot_slash("maverick/healthbench_llama-4-maverick_20251023_212754_allresults.json")
# )
# MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"

FILEPATH = Path(
    dot_slash("scout/healthbench_llama-4-scout_20251023_153707_allresults.json")
)
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

groq_pricing_per_million_tokens_input = {
    "meta-llama/llama-4-maverick-17b-128e-instruct": 0.2,
    "meta-llama/llama-4-scout-17b-16e-instruct": 0.11,
}

groq_pricing_per_million_tokens_output = {
    "meta-llama/llama-4-maverick-17b-128e-instruct": 0.6,
    "meta-llama/llama-4-scout-17b-16e-instruct": 0.34,
}


def main():
    input_cost_per_million = groq_pricing_per_million_tokens_input[MODEL]
    output_cost_per_million = groq_pricing_per_million_tokens_output[MODEL]
    full_results = json.loads(FILEPATH.read_text())
    metadata = full_results["metadata"]
    grand_total_input_tokens = 0
    grand_total_output_tokens = 0
    for example_metadata in metadata["example_level_metadata"]:
        grand_total_input_tokens += example_metadata["usage"]["prompt_tokens"]
        grand_total_output_tokens += example_metadata["usage"]["completion_tokens"]
    grand_total_tokens = grand_total_input_tokens + grand_total_output_tokens
    input_millions = grand_total_input_tokens / 1e6
    output_millions = grand_total_output_tokens / 1e6
    input_cost = input_millions * input_cost_per_million
    output_cost = output_millions * output_cost_per_million
    total_cost = input_cost + output_cost
    print(
        f"Model: {MODEL}\nCost: ${total_cost:.2f}\nTotal Tokens: {grand_total_tokens:,} "
        + f"({grand_total_input_tokens:,} input, {grand_total_output_tokens:,} output)"
    )


if __name__ == "__main__":
    main()
