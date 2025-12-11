#! /bin/bash

uv run python -m src.simple_evals.simple_evals \
    --output-dir /Users/max/Developer/repos/HealthBench/results/c6363d5c993ebf26e223714ba2210cb59372214d/two_pass \
    --n-threads 10 \
    --eval healthbench \
    --model llama-4-maverick-two-pass