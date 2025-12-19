"""Split test_ids.csv into chunks of 5 rows each."""

import csv
from pathlib import Path


def split_csv_into_chunks(
    input_file: Path,
    output_dir: Path,
    chunk_size: int = 5,
) -> int:
    """
    Split a CSV file into chunks of specified size.

    Args:
        input_file: Path to the input CSV file
        output_dir: Directory to write chunk files to
        chunk_size: Number of rows per chunk (default: 5)

    Returns:
        Number of chunk files created
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(input_file, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)

        chunk_num = 0
        current_chunk = []

        for row in reader:
            current_chunk.append(row)

            if len(current_chunk) == chunk_size:
                chunk_file = output_dir / f"chunk_{chunk_num:03d}.csv"
                with open(chunk_file, "w", newline="") as out_f:
                    writer = csv.writer(out_f)
                    writer.writerow(header)
                    writer.writerows(current_chunk)

                chunk_num += 1
                current_chunk = []

        # Write any remaining rows
        if current_chunk:
            chunk_file = output_dir / f"chunk_{chunk_num:03d}.csv"
            with open(chunk_file, "w", newline="") as out_f:
                writer = csv.writer(out_f)
                writer.writerow(header)
                writer.writerows(current_chunk)
            chunk_num += 1

    return chunk_num


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    input_file = script_dir / "test_ids.csv"
    output_dir = script_dir / "test_ids_chunked_5"

    num_chunks = split_csv_into_chunks(input_file, output_dir, chunk_size=5)
    print(f"Created {num_chunks} chunk files in {output_dir}")
