from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from intake.config import settings


@dataclass(frozen=True)
class StoredObject:
    sha256: str
    size_bytes: int
    storage_uri: str
    key: str


@dataclass(frozen=True)
class IntegrityResult:
    expected_sha256: str
    actual_sha256: str
    expected_size_bytes: int | None
    actual_size_bytes: int
    digest_matches: bool
    size_matches: bool

    @property
    def valid(self) -> bool:
        return self.digest_matches and self.size_matches


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
            config=Config(signature_version="s3v4", connect_timeout=3, read_timeout=10),
            use_ssl=settings.object_store_secure,
        )

    def ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return
        except ClientError as error:
            code = str(error.response.get("Error", {}).get("Code", ""))
            if code not in {"404", "NoSuchBucket", "NotFound"}:
                raise
        self.client.create_bucket(Bucket=self.bucket)

    def check(self) -> None:
        self.ensure_bucket()
        self.client.head_bucket(Bucket=self.bucket)

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

    def verify(self, digest: str, expected_size_bytes: int | None = None) -> IntegrityResult:
        data = self.get_bytes(digest)
        actual_digest = sha256_bytes(data)
        actual_size = len(data)
        return IntegrityResult(
            expected_sha256=digest,
            actual_sha256=actual_digest,
            expected_size_bytes=expected_size_bytes,
            actual_size_bytes=actual_size,
            digest_matches=actual_digest == digest,
            size_matches=expected_size_bytes is None or actual_size == expected_size_bytes,
        )
