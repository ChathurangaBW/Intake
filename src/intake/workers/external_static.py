from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from sqlalchemy.orm import Session

from intake.config import settings
from intake.models import Artifact, Evidence
from intake.storage import EvidenceStore
from intake.workers.local_static import LocalStaticWorkerClient
from intake.workers.static import StaticWorkerClient, StaticWorkerRequest, StaticWorkerResult


class HybridStaticWorkerClient(StaticWorkerClient):
    """Static worker that prefers configured RE tools and falls back safely.

    The external paths use fixed argv lists with no shell interpolation. If the
    operator has not enabled external static tools, or the tool binary is not
    available, Intake falls back to the built-in metadata/string worker.
    """

    def __init__(self, session: Session, evidence_store: EvidenceStore | None = None) -> None:
        self.session = session
        self.evidence_store = evidence_store or EvidenceStore()
        self.local = LocalStaticWorkerClient(session, evidence_store=self.evidence_store)

    async def submit(self, request: StaticWorkerRequest) -> StaticWorkerResult:
        if not settings.enable_external_static_tools:
            return await self.local.submit(request)

        artifact = self.session.get(Artifact, request.artifact_id)
        if artifact is None:
            return StaticWorkerResult(
                worker_id=request.worker_id,
                tool_call_id=request.tool_call_id,
                status="not_found",
                summary=f"Artifact not found: {request.artifact_id}",
            )

        if request.worker_id == "static-rizin" and shutil.which(settings.rizin_path):
            return self._run_rizin(request, artifact)
        if request.worker_id == "static-ghidra" and shutil.which(settings.ghidra_analyze_headless_path):
            return self._run_ghidra(request, artifact)
        return await self.local.submit(request)

    def _write_sample(self, artifact: Artifact, directory: Path) -> Path:
        sample = directory / f"artifact-{artifact.id}.bin"
        sample.write_bytes(self.evidence_store.get_bytes(artifact.sha256))
        return sample

    def _run_rizin(self, request: StaticWorkerRequest, artifact: Artifact) -> StaticWorkerResult:
        with tempfile.TemporaryDirectory(prefix="intake-rizin-") as tmp:
            sample = self._write_sample(artifact, Path(tmp))
            argv = [
                settings.rizin_path,
                "-q",
                "-2",
                "-A",
                "-c",
                "ij",
                "-c",
                "aflj",
                "-c",
                "izj",
                "-c",
                "q",
                str(sample),
            ]
            return self._run_and_store(
                request=request,
                artifact=artifact,
                argv=argv,
                tool_name="rizin",
                timeout_seconds=min(request.timeout_seconds, settings.maximum_tool_runtime_seconds),
            )

    def _run_ghidra(self, request: StaticWorkerRequest, artifact: Artifact) -> StaticWorkerResult:
        with tempfile.TemporaryDirectory(prefix="intake-ghidra-") as tmp:
            root = Path(settings.ghidra_project_root)
            root.mkdir(parents=True, exist_ok=True)
            sample = self._write_sample(artifact, Path(tmp))
            project_name = f"intake-{artifact.id}"
            argv = [
                settings.ghidra_analyze_headless_path,
                str(root),
                project_name,
                "-import",
                str(sample),
                "-overwrite",
                "-analysisTimeoutPerFile",
                str(min(request.timeout_seconds, settings.maximum_tool_runtime_seconds)),
            ]
            return self._run_and_store(
                request=request,
                artifact=artifact,
                argv=argv,
                tool_name="ghidra",
                timeout_seconds=min(request.timeout_seconds, settings.maximum_tool_runtime_seconds),
            )

    def _run_and_store(
        self,
        *,
        request: StaticWorkerRequest,
        artifact: Artifact,
        argv: list[str],
        tool_name: str,
        timeout_seconds: int,
    ) -> StaticWorkerResult:
        completed = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        stdout = completed.stdout[-settings.external_tool_output_limit_bytes :]
        stderr = completed.stderr[-settings.external_tool_output_limit_bytes :]
        report = {
            "tool": tool_name,
            "artifact_id": artifact.id,
            "sha256": artifact.sha256,
            "argv": [argv[0], *argv[1:-1], "<artifact>"],
            "returncode": completed.returncode,
            "stdout_tail": stdout,
            "stderr_tail": stderr,
            "worker_boundary": "external-static-fixed-argv",
        }
        report_bytes = json.dumps(report, indent=2, sort_keys=True).encode("utf-8")
        stored = self.evidence_store.put_bytes(report_bytes, media_type="application/json")
        evidence = Evidence(
            engagement_id=artifact.engagement_id,
            tool_call_id=request.tool_call_id if request.tool_call_id != "pending" else None,
            sha256=stored.sha256,
            media_type="application/json",
            size_bytes=stored.size_bytes,
            storage_uri=stored.storage_uri,
            summary=f"{tool_name} static analysis output for artifact {artifact.id}",
            metadata_={"worker_id": request.worker_id, "profile": request.profile, "returncode": completed.returncode},
        )
        self.session.add(evidence)
        self.session.commit()
        self.session.refresh(evidence)
        status = "completed" if completed.returncode == 0 else "failed"
        return StaticWorkerResult(
            worker_id=request.worker_id,
            tool_call_id=request.tool_call_id,
            status=status,
            summary=f"{tool_name} static analysis {status} for {artifact.id}",
            evidence=[{"id": evidence.id, "sha256": evidence.sha256, "storage_uri": evidence.storage_uri}],
        )
