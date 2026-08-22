#!/usr/bin/env python3
"""Publish community plugin + catalog indexes to Cloudflare R2 (SBAI-7665).

Uploads the two live indexes (pointers, not binaries):

  community/plugins/_index.json
  community/catalog/_index.json

Indexes are mutable — each publish overwrites the previous copy. This job
must never run on pull_request (secrets stay isolated to merge + cron).

Pattern reused from studiobrain-templates/scripts/publish_to_r2.py.

Requires: pip install boto3
Requires env: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
Optional env: R2_BUCKET (default: sb-content)
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys


PLUGIN_INDEX = pathlib.Path("plugins/index.json")
CATALOG_INDEX = pathlib.Path("catalog/index.json")

R2_KEYS = (
    (PLUGIN_INDEX, "community/plugins/_index.json"),
    (CATALOG_INDEX, "community/catalog/_index.json"),
)


def _err(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def _info(msg: str) -> None:
    print(msg)


def make_client(account_id: str, access_key: str, secret_key: str):
    import boto3  # type: ignore

    # boto3 1.36+ defaults to CRC32 request checksums. R2 answers AccessDenied.
    os.environ.setdefault("AWS_REQUEST_CHECKSUM_CALCULATION", "when_required")
    os.environ.setdefault("AWS_RESPONSE_CHECKSUM_VALIDATION", "when_required")

    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
    )


def publish(bucket: str, account_id: str, access_key: str, secret_key: str) -> int:
    missing_files = [str(path) for path, _ in R2_KEYS if not path.exists()]
    if missing_files:
        _err(f"missing index file(s): {', '.join(missing_files)}")
        return 1

    client = make_client(account_id, access_key, secret_key)
    for local_path, key in R2_KEYS:
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=local_path.read_bytes(),
            ContentType="application/json",
            CacheControl="public, max-age=60",
        )
        _info(f"  published (overwrite): {key} <- {local_path}")

    _info("Done: community plugin and catalog indexes uploaded to R2.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", default=os.environ.get("R2_BUCKET", "sb-content"))
    args = parser.parse_args(argv)

    account_id = os.environ.get("R2_ACCOUNT_ID")
    access_key = os.environ.get("R2_ACCESS_KEY_ID")
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
    missing = [
        name
        for name, val in (
            ("R2_ACCOUNT_ID", account_id),
            ("R2_ACCESS_KEY_ID", access_key),
            ("R2_SECRET_ACCESS_KEY", secret_key),
        )
        if not val
    ]
    if missing:
        _err(f"missing required env var(s): {', '.join(missing)}")
        return 1

    return publish(args.bucket, account_id, access_key, secret_key)


if __name__ == "__main__":
    sys.exit(main())
