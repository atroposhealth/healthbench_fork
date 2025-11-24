#! /bin/bash

uv run python -m src.simple_evals.simple_evals \
    --output-dir /Users/max/Developer/repos/HealthBench/results/cbd99b81af7e1cb59d122dec8d0cb78717b8d10d/llama-4-scout-rag2 \
    --n-threads 10 \
    --eval healthbench \
    --model llama-4-scout-rag \
    && \
uv run python -m src.simple_evals.simple_evals \
    --output-dir /Users/max/Developer/repos/HealthBench/results/cbd99b81af7e1cb59d122dec8d0cb78717b8d10d/llama-4-maverick-rag2 \
    --n-threads 10 \
    --eval healthbench \
    --model llama-4-maverick-rag