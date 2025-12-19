#! /bin/bash

uv run python -m src.simple_evals.simple_evals \
    --output-dir /Users/max/Developer/repos/HealthBench/results/7e027c10d0470439c600d35e8fa05e73ce618ae6/llama-4-maverick-self-hosted \
    --n-threads 1 \
    --eval healthbench \
    --model llama-4-maverick-lora-r4-alpha16-lr5e-6-qv_proj \
    --fine-tuned-remote true \
    --fine-tuned-system-message-path /Users/max/Developer/repos/HealthBench/src/simple_evals/improvement/analyzing_completeness/prompts/3.md \
    --example-list /Users/max/Developer/repos/HealthBench/src/simple_evals/improvement/dpo/test_ids.csv
    # --examples 10


