"""Process JSON files through OpenAI to check for rubric contradictions."""

import json
import os
from pathlib import Path

from openai import OpenAI


def load_processed_files(output_path: Path) -> set[str]:
    """Load the set of already-processed source files from the output file."""
    if not output_path.exists():
        return set()

    processed = set()
    with open(output_path) as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                processed.add(record.get("source_file", ""))
    return processed


def append_result(output_path: Path, result: dict) -> None:
    """Append a single result to the JSONLines output file."""
    with open(output_path, "a") as f:
        f.write(json.dumps(result) + "\n")


def load_prompt_template(prompt_path: Path) -> str:
    """Load the prompt template from a markdown file."""
    return prompt_path.read_text()


def load_json_files(directory: Path) -> list[dict]:
    """Load all JSON files from a directory."""
    json_files = []
    for json_path in directory.glob("*.json"):
        with open(json_path) as f:
            data = json.load(f)
            data["_source_file"] = json_path.name
            json_files.append(data)
    return json_files


def filter_accuracy_axis(records: list[dict]) -> list[dict]:
    """Filter records to only those with axis='accuracy'."""
    return [r for r in records if r.get("axis") == "accuracy"]


def populate_prompt(template: str, criterion: str, study_result: str) -> str:
    """Populate the prompt template with criterion and study result."""
    prompt = template.replace("{{criterion}}", criterion)
    prompt = prompt.replace("{{study_result}}", study_result)
    return prompt


def process_with_openai(prompt: str, client: OpenAI) -> str:
    """Send prompt to OpenAI and return the response."""
    response = client.chat.completions.create(
        model="o3-mini", messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content
    return content if content is not None else ""


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    client = OpenAI(api_key=api_key)

    script_dir = Path(__file__).parent
    prompt_template = load_prompt_template(script_dir / "prompt.md")
    to_ingest_dir = script_dir.parent / "opensearch/to_ingest"
    output_path = script_dir / "results.jsonl"

    all_records = load_json_files(to_ingest_dir)
    accuracy_records = filter_accuracy_axis(all_records)

    # Load already-processed files
    processed_files = load_processed_files(output_path)
    print(f"Found {len(processed_files)} already-processed records")

    # Filter out already-processed records
    records_to_process = [
        r for r in accuracy_records if r.get("_source_file") not in processed_files
    ]

    print(f"Found {len(accuracy_records)} total records with axis='accuracy'")
    print(f"Processing {len(records_to_process)} new records")

    if not records_to_process:
        print("No new records to process")
        return

    for i, record in enumerate(records_to_process, 1):
        criterion = record.get("criteria", "")
        study_result = record.get("atropos_summary", "")
        source_file = record.get("_source_file", "unknown")

        prompt = populate_prompt(prompt_template, criterion, study_result)

        print(f"[{i}/{len(records_to_process)}] Processing {source_file}...")

        try:
            response = process_with_openai(prompt, client)
            result = {
                "source_file": source_file,
                "criterion": criterion,
                "study_result": study_result,
                "response": response,
            }
            append_result(output_path, result)
            print(f"  Response: {response[:100]}...")
        except Exception as e:
            print(f"  Error: {e}")
            result = {
                "source_file": source_file,
                "criterion": criterion,
                "study_result": study_result,
                "error": str(e),
            }
            append_result(output_path, result)

    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
