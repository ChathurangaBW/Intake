from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
import socket
import time
from dataclasses import dataclass

from intake.config import settings
from intake.db import SessionLocal
from intake.jobs import JobService
from intake.models import ToolCall
from intake.services import IntakeService

logger = logging.getLogger("intake.worker")


@dataclass
class WorkerState:
    stopping: bool = False


def default_worker_id() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"


def run_once(worker_id: str) -> bool:
    with SessionLocal() as session:
        jobs = JobService(session)
        job = jobs.claim_next(worker_id)
        if job is None:
            return False

        try:
            tool_call = session.get(ToolCall, job.tool_call_id)
            if tool_call is None:
                jobs.fail(job.id, worker_id=worker_id, error="tool call was deleted")
                return True
            if job.cancel_requested:
                jobs.cancel(job.id, actor=worker_id)
                return True

            # IntakeService retains its synchronous authorization guard. The
            # durable queue owns authorization state while a leased worker runs.
            tool_call.status = "authorized"
            tool_call.worker_id = worker_id
            session.commit()

            service = IntakeService(session)
            result = asyncio.run(service.execute_tool_call(tool_call.id))
            jobs.complete(
                job.id,
                worker_id=worker_id,
                result=result.model_dump(mode="json"),
            )
            logger.info("completed job %s for tool call %s", job.id, tool_call.id)
        except Exception as error:  # noqa: BLE001 - worker isolation boundary
            session.rollback()
            JobService(session).fail(
                job.id,
                worker_id=worker_id,
                error=f"{type(error).__name__}: {error}",
            )
            logger.exception("failed job %s", job.id)
        return True


def run_forever(worker_id: str | None = None, *, once: bool = False) -> None:
    resolved_worker_id = worker_id or default_worker_id()
    state = WorkerState()

    def stop(_signum: int, _frame: object) -> None:
        state.stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    logger.info("Intake worker started: %s", resolved_worker_id)

    while not state.stopping:
        worked = run_once(resolved_worker_id)
        if once:
            break
        if not worked:
            time.sleep(settings.worker_poll_interval_seconds)

    logger.info("Intake worker stopped: %s", resolved_worker_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Intake durable execution worker")
    parser.add_argument("--worker-id", default=None)
    parser.add_argument("--once", action="store_true", help="Claim at most one job and exit")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    run_forever(args.worker_id, once=args.once)


if __name__ == "__main__":
    main()
