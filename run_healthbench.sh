#! /bin/bash

uv run python -m src.simple_evals.simple_evals \
    --output-dir /Users/max/Developer/repos/HealthBench/results/7e027c10d0470439c600d35e8fa05e73ce618ae6/gpt-5 \
    --n-threads 10 \
    --eval healthbench \
    --model gpt-5.1,gpt-5.2-pro