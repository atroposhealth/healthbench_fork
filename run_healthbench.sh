#! /bin/bash

uv run python -m src.simple_evals.simple_evals \
    --output-dir /Users/max/Developer/Meta/HealthBench/results/f10bb3e1b89e1f6e599556d776e9fcae3ff05226/llama-4-maverick-scratch \
    --n-threads 5 \
    --eval healthbench \
    --model llama-4-maverick-top-100-guidelines \
    --examples 1000