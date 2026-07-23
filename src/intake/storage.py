from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import boto3
from botocore.client import Config

from intake.config import settings


@dataclass(frozen=True)
class StoredObject:
    sha256: str
    size_bytes: int
    storage_uri: str
    key: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def evidence_key(digest: str) -> str:
    return f"sha256/{digest[:2]}/{digest}"


class EvidenceStore:
    """Content-addressed object storage for tool outputs and artifacts."""

    def __init__(self) -> None:
        self.bucket = settings.object_store_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.object_store_endpoint,
            aws_access_key_id=settings.object_store_access_key,
            aws_secret_access_key=settings.object_store_secret_key,
            region_name=settings.object_store_region,
            config=Config(signature_version="s3v4"),
            use_ssl=settings.object_store_secure,
        )

    def ensure_bucket(self) -> None:
        buckets = self.client.list_buckets().get("Buckets", [])
        if not any(bucket.get("Name") == self.bucket for bucket in buckets):
            self.client.create_bucket(Bucket=self.bucket)

    def put_bytes(self, data: bytes, media_type: str = "application/octet-stream") -> StoredObject:
        digest = sha256_bytes(data)
        key = evidence_key(digest)
        self.ensure_bucket()
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=media_type,
            Metadata={"sha256": digest},
        )
        return StoredObject(
            sha256=digest,
            size_bytes=len(data),
            key=key,
            storage_uri=f"s3://{self.bucket}/{key}",
        )

    def put_file(self, path: str | Path, media_type: str = "application/octet-stream") -> StoredObject:
        return self.put_bytes(Path(path).read_bytes(), media_type=media_type)

    def get_bytes(self, digest: str) -> bytes:
        key = evidence_key(digest)
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()
