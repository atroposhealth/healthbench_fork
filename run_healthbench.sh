#! /bin/bash

uv run python -m src.simple_evals.simple_evals \
    --output-dir /Users/max/Developer/repos/simple-evals/results/9eb82b46b5ef7faf6ec102a989421543e84d4228/llama-3.1-8b \
    --n-threads 10 \
    --eval healthbench \
    --model llama-3.1-8b 