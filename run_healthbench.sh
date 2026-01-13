#! /bin/bash

uv run python -m src.simple_evals.simple_evals \
    --output-dir /Users/max/Developer/repos/HealthBench/results/395ab7de3513b9bc22272bd90f66dc1ce99aa411/llama-4-maverick-new-vsi \
    --n-threads 10 \
    --eval healthbench \
    --model llama-4-maverick-rag-2