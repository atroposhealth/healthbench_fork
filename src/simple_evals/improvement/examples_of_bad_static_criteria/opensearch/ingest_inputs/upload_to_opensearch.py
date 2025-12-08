#!/usr/bin/env python3
"""
Written by Claude.

Standalone script to upload JSONL data to OpenSearch.

This script reads JSON lines from a file and uploads them as documents
to an OpenSearch server running at http://localhost:9200.
Each document's ID is set to the 'prompt_id' field from the JSON object.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

import requests

# Configuration
OPENSEARCH_URL = "http://localhost:9200"
INDEX_NAME = "inputs"
INPUT_FILE = (
    Path(__file__).parent.parent.parent.parent.parent.parent.parent
    / "results"
    / "inputs"
    / "2025-05-07-06-14-12_oss_eval.jsonl"
)


def read_jsonl_file(file_path: Path) -> list[Dict[str, Any]]:
    """Read JSONL file and return list of JSON objects."""
    documents = []

    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    print(f"Reading data from: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                doc = json.loads(line)
                documents.append(doc)
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line {line_num}: {e}")
                continue

    print(f"Successfully read {len(documents)} documents")
    return documents


def upload_documents_bulk(
    documents: list[Dict[str, Any]], batch_size: int = 1000
) -> None:
    """Upload documents to OpenSearch using the bulk API in batches."""

    total_docs = len(documents)
    print(
        f"Uploading {total_docs} documents to index '{INDEX_NAME}' in batches of {batch_size}..."
    )

    total_uploaded = 0
    total_failed = 0

    # Process documents in batches
    for batch_start in range(0, total_docs, batch_size):
        batch_end = min(batch_start + batch_size, total_docs)
        batch = documents[batch_start:batch_end]
        batch_num = (batch_start // batch_size) + 1
        total_batches = (total_docs + batch_size - 1) // batch_size

        print(
            f"  Processing batch {batch_num}/{total_batches} ({len(batch)} documents)..."
        )

        # Build the bulk request body for this batch
        # Format: { "index": { "_id": "doc_id" } }\n{ document }\n
        bulk_data = []
        for doc in batch:
            if "prompt_id" not in doc:
                print("Warning: Document missing 'prompt_id' field, skipping")
                continue

            # Action metadata
            action = {"index": {"_id": doc["prompt_id"]}}
            bulk_data.append(json.dumps(action))
            bulk_data.append(json.dumps(doc))

        # Join with newlines and add trailing newline
        bulk_body = "\n".join(bulk_data) + "\n"

        # Send bulk request
        url = f"{OPENSEARCH_URL}/{INDEX_NAME}/_bulk"
        headers = {"Content-Type": "application/x-ndjson"}

        try:
            response = requests.post(url, data=bulk_body, headers=headers)
            response.raise_for_status()

            result = response.json()

            # Check for errors in the bulk response
            if result.get("errors"):
                failed_count = sum(
                    1 for item in result["items"] if "error" in item.get("index", {})
                )
                total_failed += failed_count
                print(f"    Batch completed with {failed_count} errors")

                # Show first few errors
                for item in result["items"][:3]:
                    if "error" in item.get("index", {}):
                        error_info = item["index"]["error"]
                        print(
                            f"      - Error: {error_info.get('type')}: {error_info.get('reason')}"
                        )
            else:
                batch_uploaded = len(result["items"])
                total_uploaded += batch_uploaded
                print(f"    Successfully uploaded {batch_uploaded} documents")

        except requests.exceptions.RequestException as e:
            print(f"Error uploading batch {batch_num}: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response: {e.response.text}")
            raise

    print("\nUpload summary:")
    print(f"  Total documents processed: {total_docs}")
    print(f"  Successfully uploaded: {total_uploaded}")
    if total_failed > 0:
        print(f"  Failed: {total_failed}")


def verify_upload() -> None:
    """Verify the upload by checking document count."""
    url = f"{OPENSEARCH_URL}/{INDEX_NAME}/_count"

    try:
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        count = result.get("count", 0)
        print(f"Total documents in index '{INDEX_NAME}': {count}")
    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not verify document count: {e}")


def main():
    """Main function to orchestrate the upload process."""
    print("=" * 60)
    print("OpenSearch Document Upload Script")
    print("=" * 60)

    try:
        # Verify OpenSearch is accessible
        print("\nConnecting to OpenSearch...")
        response = requests.get(OPENSEARCH_URL)
        response.raise_for_status()
        info = response.json()
        print(f"Connected to OpenSearch cluster: {info.get('cluster_name', 'unknown')}")
        print(f"Version: {info.get('version', {}).get('number', 'unknown')}")

        # Read documents from file
        print()
        documents = read_jsonl_file(INPUT_FILE)

        if not documents:
            print("No documents to upload. Exiting.")
            return

        # Upload documents
        print()
        upload_documents_bulk(documents)

        # Verify upload
        print()
        verify_upload()

        print("\n" + "=" * 60)
        print("Upload completed successfully!")
        print("=" * 60)

    except FileNotFoundError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"\nHTTP Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
