import tarfile
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import boto3
import typer
from rich import print
from rich.table import Table

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client, S3ServiceResource

BUCKET = "atropos-meta-benchmarking"
AWS_PROFILE = "dev-administrator"
KEY_PREFIX = "healthbench"

app = typer.Typer()


@app.command()
def upsert(path: Path):
    """
    Add the directory at PATH to S3 (after archiving and compressing it). Will
    overwrite an existing object with the same name if one already exists.
    """
    if not path.is_dir():
        raise FileNotFoundError(f"Supplied path is not a directory: {path}")
    with tempfile.TemporaryDirectory() as working_dir_name:
        working_dir = Path(working_dir_name)
        archive_name = f"{path.name}.tar.gz"
        archive_path = working_dir / archive_name
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(path)
        s3_key = f"{KEY_PREFIX}/{archive_name}"
        print(f"Uploading s3://{BUCKET}/{s3_key}")
        session = boto3.Session(profile_name=AWS_PROFILE)
        s3: S3ServiceResource = session.resource("s3")
        bucket = s3.Bucket(BUCKET)
        bucket.upload_file(str(archive_path), Key=s3_key)


@app.command()
def list():
    """
    Lists all of the objects available underneath the healthbench/ prefix.
    """
    session = boto3.Session(profile_name=AWS_PROFILE)
    s3_client: S3Client = session.client("s3")
    response = s3_client.list_objects_v2(Bucket=BUCKET, Prefix=KEY_PREFIX)
    table = Table(title="Objects")
    table.add_column("Name")
    table.add_column("Last Modified")
    table.add_column("Size")
    assert "Contents" in response
    for object in response["Contents"]:
        assert "Key" in object
        assert "LastModified" in object
        assert "Size" in object
        name = object["Key"]
        last_modified = object["LastModified"]
        size = object["Size"]
        table.add_row(name, last_modified.isoformat(), _get_size_dscription(size))
    print(table)


def _get_size_dscription(n_bytes: int) -> str:
    """
    Returns a string describing the number of bytes, e.g. "24 MB", or "2 KB".
    """
    if n_bytes > 1e12:
        n_terabytes = round(n_bytes / 1e12)
        return f"{n_terabytes} TB"
    elif n_bytes > 1e9:
        n_gigabytes = round(n_bytes / 1e9)
        return f"{n_gigabytes} GB"
    elif n_bytes > 1e6:
        n_megabytes = round(n_bytes / 1e6)
        return f"{n_megabytes} MB"
    elif n_bytes > 1e3:
        n_kilobytes = round(n_bytes / 1e3)
        return f"{n_kilobytes} KB"
    else:
        return f"{n_bytes} B"


@app.command()
def download(object_name: str, output_dir: Path):
    """
    Downloads the object specified by OBJECT_NAME (can include or omit '.tar.gz') to
    the OUTPUT_DIR.
    """
    if not output_dir.is_dir():
        output_dir.mkdir(parents=True)
    session = boto3.Session(profile_name=AWS_PROFILE)
    s3: S3ServiceResource = session.resource("s3")
    bucket = s3.Bucket(BUCKET)
    # Remove any path prefixes, if any, and make sure the name ends in
    # ".tar.gz".
    object_name = object_name.split("/")[-1].rstrip(".tar.gz") + ".tar.gz"
    key = f"{KEY_PREFIX}/{object_name}"
    with tempfile.TemporaryDirectory() as working_dir_name:
        working_dir = Path(working_dir_name)
        download_path = working_dir / object_name
        bucket.download_file(key, str(download_path))
        with tarfile.open(download_path, "r:gz") as tar:
            tar.extractall(output_dir)
    print(f"Successfully extracted {object_name} to {output_dir}.")


if __name__ == "__main__":
    app()
