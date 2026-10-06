import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

import boto3
from botocore.client import BaseClient
from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from shared.schemas import JobRequest, JobResult, ServiceHealth
from shared.utils import configure_json_logger

MINIO_BUCKET = os.getenv("MINIO_BUCKET", "notoria")
MINIO_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
PRESIGNED_EXPIRATION = int(os.getenv("PRESIGNED_EXPIRATION", "3600"))

WorkerProcessor = Callable[[JobRequest, Path, Path], tuple[Path, dict[str, Any], list[str]] | tuple[Path, dict[str, Any], dict[str, Any], list[str]]]


def _s3_client() -> BaseClient:
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        region_name=S3_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def _normalize_input_key(raw_uri: str) -> str:
    if raw_uri.startswith("s3://"):
        prefix = f"s3://{MINIO_BUCKET}/"
        return raw_uri.replace(prefix, "", 1) if raw_uri.startswith(prefix) else raw_uri.split("/", 3)[-1]
    return raw_uri.lstrip("/")


def _default_processor(payload: JobRequest, _inputs_dir: Path, outputs_dir: Path) -> tuple[Path, dict[str, Any], list[str]]:
    local_output = outputs_dir / "output.json"
    local_output.write_text(
        json.dumps(
            {
                "job_id": payload.job_id,
                "script": payload.script,
                "language": payload.language,
                "format": payload.format,
            }
        )
    )
    return local_output, {}, []


def create_worker_app(
    worker_name: str,
    version: str = "0.1.0",
    *,
    required_params: list[str] | None = None,
    processor: WorkerProcessor | None = None,
) -> FastAPI:
    app = FastAPI(title=f"NOTORIA Worker {worker_name}", version=version)
    logger = configure_json_logger(f"worker-{worker_name}")

    metric_worker_name = worker_name.replace("-", "_")
    runs_total = Counter(f"notoria_worker_{metric_worker_name}_runs_total", f"Total runs for worker {worker_name}")
    run_duration_seconds = Histogram(
        f"notoria_worker_{metric_worker_name}_run_duration_seconds", f"Run duration for worker {worker_name}"
    )

    required_params = required_params or []
    processor = processor or _default_processor
    status_store: dict[str, JobResult] = {}

    @app.get("/health", response_model=ServiceHealth)
    def health() -> ServiceHealth:
        return ServiceHealth(service_name=f"worker-{worker_name}", ok=True, gpu={"available": False}, version=version)

    @app.post("/generate", response_model=JobResult)
    def generate(payload: JobRequest) -> JobResult:
        started = time.perf_counter()
        client = _s3_client()
        workdir = Path(tempfile.mkdtemp(prefix=f"notoria-{worker_name}-{payload.job_id[:8]}-"))
        inputs_dir = workdir / "inputs"
        outputs_dir = workdir / "outputs"
        inputs_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)

        input_uris = payload.params.get("input_uris", []) if isinstance(payload.params, dict) else []
        downloaded_files: list[str] = []
        errors: list[str] = []

        for key in required_params:
            if key not in payload.params:
                errors.append(f"missing_required_param:{key}")

        for idx, raw_uri in enumerate(input_uris):
            try:
                object_key = _normalize_input_key(str(raw_uri))
                local_target = inputs_dir / f"input_{idx}_{Path(object_key).name}"
                client.download_file(MINIO_BUCKET, object_key, str(local_target))
                downloaded_files.append(str(local_target))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"download_failed:{raw_uri}:{exc}")

        extra_outputs: dict[str, Any] = {}
        extra_metrics: dict[str, Any] = {}
        if not errors:
            try:
                result_tuple = processor(payload, inputs_dir, outputs_dir)
                if len(result_tuple) == 3:
                    local_output, extra_outputs, processor_errors = result_tuple
                else:
                    local_output, extra_outputs, extra_metrics, processor_errors = result_tuple
                errors.extend(processor_errors)
            except Exception as exc:  # noqa: BLE001
                local_output = outputs_dir / "output.error.txt"
                local_output.write_text(f"processor_failed:{exc}")
                errors.append(f"processor_failed:{exc}")
        else:
            local_output = outputs_dir / "output.error.txt"
            local_output.write_text("missing required params or download failure")

        output_key = f"jobs/{payload.job_id}/{worker_name}/{local_output.name}"
        presigned_url = ""
        try:
            client.upload_file(str(local_output), MINIO_BUCKET, output_key)
            presigned_url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": MINIO_BUCKET, "Key": output_key},
                ExpiresIn=PRESIGNED_EXPIRATION,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"upload_or_presign_failed:{exc}")

        elapsed = time.perf_counter() - started
        runs_total.inc()
        run_duration_seconds.observe(elapsed)

        result = JobResult(
            job_id=payload.job_id,
            status="accepted" if not errors else "failed",
            outputs={
                "worker": worker_name,
                "bucket": MINIO_BUCKET,
                "object_key": output_key,
                "presigned_url": presigned_url,
                **extra_outputs,
            },
            metrics={
                "duration_ms": round(elapsed * 1000, 2),
                "downloaded_inputs": len(downloaded_files),
                **extra_metrics,
            },
            errors=errors,
        )
        status_store[payload.job_id] = result

        logger.info(
            json.dumps(
                {
                    "event": "worker_generate_completed",
                    "worker": worker_name,
                    "job_id": payload.job_id,
                    "duration_ms": round(elapsed * 1000, 2),
                    "errors_count": len(errors),
                }
            )
        )
        return result

    @app.post("/status", response_model=JobResult)
    def status(payload: JobRequest) -> JobResult:
        result = status_store.get(payload.job_id)
        if result:
            return result
        return JobResult(job_id=payload.job_id, status="queued", outputs={}, metrics={}, errors=[])

    @app.get("/metrics")
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app
