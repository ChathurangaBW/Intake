from __future__ import annotations

from ipaddress import ip_address, ip_network
from urllib.parse import urlparse

from pydantic import BaseModel, Field


class ScopeManifest(BaseModel):
    engagement_id: str
    domains: list[str] = Field(default_factory=list)
    cidrs: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    allowed_operations: list[str] = Field(default_factory=list)
    approval_required: list[str] = Field(default_factory=list)
    denied_operations: list[str] = Field(default_factory=list)


def normalize_host(value: str) -> str:
    parsed = urlparse(value if "://" in value else f"scheme://{value}")
    return (parsed.hostname or value).lower().rstrip(".")


class ScopeValidator:
    def __init__(self, manifest: ScopeManifest) -> None:
        self.manifest = manifest

    def operation_allowed(self, operation: str) -> bool:
        if operation in self.manifest.denied_operations:
            return False
        if not self.manifest.allowed_operations:
            return True
        return operation in self.manifest.allowed_operations

    def requires_approval(self, operation: str) -> bool:
        return operation in self.manifest.approval_required

    def target_allowed(self, value: str) -> bool:
        host = normalize_host(value)
        if host in {domain.lower().rstrip(".") for domain in self.manifest.domains}:
            return True

        for domain in self.manifest.domains:
            suffix = "." + domain.lower().rstrip(".")
            if host.endswith(suffix):
                return True

        try:
            ip = ip_address(host)
        except ValueError:
            return False

        return any(ip in ip_network(cidr, strict=False) for cidr in self.manifest.cidrs)

    def artifact_allowed(self, artifact_id_or_sha256: str) -> bool:
        return artifact_id_or_sha256 in self.manifest.artifacts
