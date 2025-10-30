#! /bin/bash

uv run python -m src.simple_evals.simple_evals \
    --output-dir /Users/max/Developer/repos/simple-evals/results/9252fc34f9bc391262e8b71138ee3b86e7d0ad7a/llama-3.1-8b \
    --n-threads 10 \
    --eval healthbench \
    --model llama-3.1-8b \
    --examples 3