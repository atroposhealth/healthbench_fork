"""
Calls the Fine-tuned Llama 4 endpoint once for each chunked Test ID file in
"src/simple_evals/improvement/dpo/test_ids_chunked".
"""

import subprocess
from pathlib import Path

from dot_slash import dot_slash

# command_template = """
# uv run python -m src.simple_evals.simple_evals \
#     --output-dir /Users/max/Developer/repos/HealthBench/results/7e027c10d0470439c600d35e8fa05e73ce618ae6/llama-4-maverick-self-hosted \
#     --n-threads 1 \
#     --eval healthbench \
#     --model llama-4-maverick-lora-r4-alpha16-lr5e-6-qv_proj \
#     --fine-tuned-remote true \
#     --fine-tuned-system-message-path /Users/max/Developer/repos/HealthBench/src/simple_evals/improvement/analyzing_completeness/prompts/3.md \
#     --example-list {chunk_path}
# """

command_template = """
uv run python -m src.simple_evals.simple_evals \
    --output-dir /Users/max/Developer/repos/HealthBench/results/7e027c10d0470439c600d35e8fa05e73ce618ae6/llama-4-maverick-self-hosted \
    --n-threads 1 \
    --eval healthbench \
    --model llama-4-maverick-self-hosted-lora \
    --example-list {chunk_path}
"""


def main():
    chunked_dir = Path(dot_slash("src/simple_evals/improvement/dpo/test_ids_chunked_5"))
    chunk_files = list(chunked_dir.glob("*.csv"))
    # Make sure to process them in order so we can re-start if needed
    chunk_files.sort()
    for chunk_filepath in chunk_files:
        command = command_template.format(chunk_path=chunk_filepath)
        print(f"Running:\n{command}")
        subprocess.check_call(command, shell=True)


if __name__ == "__main__":
    main()
