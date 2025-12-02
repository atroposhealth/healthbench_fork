#! /bin/bash

uv run python -m src.simple_evals.simple_evals \
    --output-dir /Users/max/Developer/repos/HealthBench/results/a67ca8f9edea993fbb2551094c41777651cea1ec/enhanced_prompt_3 \
    --n-threads 10 \
    --eval healthbench \
    --model llama-4-scout-enhanced-prompt-completeness-3,llama-3.3-70b-enhanced-prompt-completeness-3,llama-3.1-8b-enhanced-prompt-completeness-3