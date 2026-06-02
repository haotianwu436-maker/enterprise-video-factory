"""Command line entry point for the local runtime foundation."""

from __future__ import annotations

import argparse
import json

import uvicorn

from video_factory_runtime.domain import ActorContext
from video_factory_runtime.seed import (
    DEFAULT_TENANT_ID,
    DEFAULT_USER_ID,
    create_default_service,
    sample_create_job_request,
)


def main(argv: list[str] | None = None) -> int:
    """Start the local API server or print a sample accepted job."""
    parser = argparse.ArgumentParser(description="Run the enterprise video factory runtime foundation.")
    parser.add_argument("--host", default="127.0.0.1", help="Host for the FastAPI server.")
    parser.add_argument("--port", default=8000, type=int, help="Port for the FastAPI server.")
    parser.add_argument(
        "--sample-job",
        action="store_true",
        help="Create a sample job in-process and print the accepted response.",
    )
    args = parser.parse_args(argv)

    if args.sample_job:
        service = create_default_service()
        job = service.create_job(
            sample_create_job_request(),
            ActorContext(tenant_id=DEFAULT_TENANT_ID, user_id=DEFAULT_USER_ID, role="creator"),
        )
        print(json.dumps(job.to_api(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    uvicorn.run(
        "video_factory_runtime.api:create_app",
        factory=True,
        host=args.host,
        port=args.port,
    )
    return 0
