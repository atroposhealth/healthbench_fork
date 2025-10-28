# Results
Results are stored in S3. Use the `result_manager.py` script to list/download/upload them.

To list existing results run

```sh
uv run result_manager.py list
```

Then to download an existing set of results run

```sh
uv run result_manager.py download <some_object_name> .
```