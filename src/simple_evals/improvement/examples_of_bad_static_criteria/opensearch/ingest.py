import json
import warnings
from pathlib import Path

import requests
from dot_slash import dot_slash
from tqdm import tqdm

DATA_DIR = Path(dot_slash("to_ingest"))


def ingest_data():
    with warnings.catch_warnings():
        for filepath in tqdm(list(DATA_DIR.glob("*.json"))):
            doc_id = filepath.stem
            url = f"http://127.0.0.1:9200/criteria/_doc/{doc_id}"
            doc = json.loads(filepath.read_text())
            doc["id"] = doc_id
            response = requests.put(
                url,
                json=doc,
            )
            response.raise_for_status()


if __name__ == "__main__":
    ingest_data()
