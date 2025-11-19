#! /bin/bash

uv run python -m src.simple_evals.simple_evals \
    --output-dir /Users/max/Developer/repos/HealthBench/results/66a515a50edfaa2c8f21674d4141a124b50ef286/llama-4-maverick-rag \
    --n-threads 10 \
    --eval healthbench \
    --model llama-4-scout-rag