#! /bin/bash

uv run python -m src.simple_evals.simple_evals \
    --output-dir /Users/max/Developer/Meta/HealthBench/results/e7a6a63532eaacc9e13568cbd286b95034032147/llama-4-maverick-top-100-reworded-criteria \
    --n-threads 5 \
    --eval healthbench \
    --model llama-4-maverick-top-100-reworded-criteria \
    --examples 2000