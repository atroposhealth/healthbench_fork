#! /bin/bash

uv run python -m src.simple_evals.simple_evals \
    --output-dir /Users/max/Developer/repos/HealthBench/results/7e027c10d0470439c600d35e8fa05e73ce618ae6/llama-3.1-8b-self-hosted-2500 \
    --n-threads 1 \
    --eval healthbench \
    --model llama-3.1-8b-lr5e6-epoch2-alpha32 \
    --fine-tuned-remote true \
    --fine-tuned-system-message "You are a helpful assistant." \
    --example-list /Users/max/Developer/repos/HealthBench/src/simple_evals/improvement/dpo/test_ids.csv