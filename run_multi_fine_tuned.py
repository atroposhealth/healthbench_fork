import subprocess


def main():
    models_to_run = [
        "llama-3.1-8b-base",
        "llama-3.1-8b-lr5e5",
        "llama-3.1-8b-lr5e6",
        "llama-3.1-8b-lr5e5-epoch2",
        "llama-3.1-8b-lr5e6-epoch2",
        "llama-3.1-8b-lr5e5-alpha32",
        "llama-3.1-8b-lr5e6-alpha32",
        "llama-3.1-8b-lr5e5-epoch2-alpha32",
        "llama-3.1-8b-lr5e6-epoch2-alpha32",
    ]
    command_template = r"""
uv run python -m src.simple_evals.simple_evals \
    --output-dir /Users/max/Developer/repos/HealthBench/results/7e027c10d0470439c600d35e8fa05e73ce618ae6/llama-3.1-8b-self-hosted \
    --n-threads 1 \
    --eval healthbench \
    --model {} \
    --fine-tuned-remote true \
    --fine-tuned-system-message "You are a helpful assistant." \
    --example-list /Users/max/Developer/repos/HealthBench/src/simple_evals/improvement/dpo/sampled_test_ids_100.csv
"""
    for healthbench_model_name in models_to_run:
        command = command_template.format(healthbench_model_name)
        print(f"Running:\n{command}")
        subprocess.check_call(command, shell=True)


if __name__ == "__main__":
    main()
