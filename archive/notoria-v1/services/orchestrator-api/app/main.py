import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict
from urllib import error, request

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.responses import Response

from shared.schemas import JobRequest, JobResult, RegistryServiceCreate, RegistryServicePatch, RegistryServiceResponse, ServiceHealth
from shared.utils import configure_json_logger

from .db import get_db
from .models import RegistryService

app = FastAPI(title="NOTORIA Orchestrator API", version="0.6.0")
logger = configure_json_logger("orchestrator-api")

JOBS_TOTAL = Counter("notoria_jobs_total", "Total jobs created")
JOB_RETRIES_TOTAL = Counter("notoria_job_retries_total", "Total job retries")
REGISTRY_UPSERTS_TOTAL = Counter("notoria_registry_upserts_total", "Total registry inserts/updates")
ORCHESTRATION_TOTAL = Counter("notoria_orchestration_total", "Total orchestration runs", ["status"])
STEP_DURATION = Histogram("notoria_orchestration_step_duration_seconds", "Step execution duration", ["step"])

STORE: Dict[str, JobResult] = {}
MAX_RETRIES_PER_STEP = int(os.getenv("ORCHESTRATOR_MAX_RETRIES", "2"))
WORKER_TIMEOUT_SECONDS = float(os.getenv("WORKER_TIMEOUT_SECONDS", "15"))


class N8nOrderCreatedRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    avatar_id: str = Field(..., min_length=1)
    script: str = Field(..., min_length=1)
    language: str = Field(default="fr", min_length=2, max_length=10)
    format: str = Field(default="mp4", min_length=2, max_length=20)
    plan: str = Field(..., min_length=1)


class N8nOrderCreatedResponse(BaseModel):
    job_id: str
    status_url: str


@dataclass
class DispatchResult:
    ok: bool
    status_code: int
    body: dict[str, Any]
    error: str | None = None


def _build_timing_map(script_text: str) -> list[dict[str, Any]]:
    words = [w for w in script_text.split() if w.strip()]
    timing_map: list[dict[str, Any]] = []
    cursor = 0.0
    for word in words:
        duration = max(0.15, min(0.65, len(word) * 0.05))
        timing_map.append({"word": word, "start_s": round(cursor, 2), "end_s": round(cursor + duration, 2)})
        cursor += duration
    return timing_map


def _script_agent_stub(script_text: str) -> tuple[str, list[dict[str, Any]]]:
    spoken_script = script_text.strip()
    return spoken_script, _build_timing_map(spoken_script)


def _url_join(base_url: str, endpoint: str) -> str:
    return f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"


def _http_get_json(url: str, timeout: float) -> DispatchResult:
    req = request.Request(url=url, method="GET")
    try:
        with request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8")
            body = json.loads(raw) if raw else {}
            return DispatchResult(ok=200 <= resp.status < 300, status_code=resp.status, body=body)
    except error.HTTPError as exc:
        payload = exc.read().decode("utf-8") if hasattr(exc, "read") else ""
        return DispatchResult(ok=False, status_code=exc.code, body={}, error=payload or str(exc))
    except Exception as exc:  # noqa: BLE001
        return DispatchResult(ok=False, status_code=0, body={}, error=str(exc))


def _http_post_json(url: str, payload: dict[str, Any], timeout: float) -> DispatchResult:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, data=data, method="POST", headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8")
            body = json.loads(raw) if raw else {}
            return DispatchResult(ok=200 <= resp.status < 300, status_code=resp.status, body=body)
    except error.HTTPError as exc:
        payload_text = exc.read().decode("utf-8") if hasattr(exc, "read") else ""
        return DispatchResult(ok=False, status_code=exc.code, body={}, error=payload_text or str(exc))
    except Exception as exc:  # noqa: BLE001
        return DispatchResult(ok=False, status_code=0, body={}, error=str(exc))


def _service_endpoint(service: RegistryService, key: str, default_path: str) -> str:
    endpoint = default_path
    if isinstance(service.endpoints, dict):
        endpoint = str(service.endpoints.get(key) or endpoint)
    return _url_join(service.base_url, endpoint)


def _resolve_primary_service(db: Session, category: str) -> RegistryService:
    service = (
        db.query(RegistryService)
        .filter(RegistryService.category == category, RegistryService.enabled.is_(True))
        .order_by(RegistryService.type.asc(), RegistryService.id.asc())
        .first()
    )
    if not service:
        raise HTTPException(status_code=503, detail=f"no enabled service for category={category}")
    return service


def _resolve_by_name(db: Session, service_name: str) -> RegistryService | None:
    return db.query(RegistryService).filter(RegistryService.service_name == service_name, RegistryService.enabled.is_(True)).first()


def _dispatch_with_routing(db: Session, category: str, payload: dict[str, Any], step_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    primary_service = _resolve_primary_service(db, category)
    attempts: list[dict[str, Any]] = []

    for retry in range(MAX_RETRIES_PER_STEP + 1):
        service = primary_service
        if retry > 0 and primary_service.fallback_service:
            fallback = _resolve_by_name(db, primary_service.fallback_service)
            if fallback:
                service = fallback

        health_url = _service_endpoint(service, "health", "/health")
        generate_url = _service_endpoint(service, "generate", "/generate")

        health = _http_get_json(health_url, WORKER_TIMEOUT_SECONDS)
        if not health.ok:
            attempts.append({"retry": retry, "service": service.service_name, "phase": "health", "status_code": health.status_code, "error": health.error})
            continue

        resp = _http_post_json(generate_url, payload, WORKER_TIMEOUT_SECONDS)
        if resp.ok:
            return resp.body, {"service": service.service_name, "retry": retry, "attempts": attempts}

        attempts.append({"retry": retry, "service": service.service_name, "phase": "dispatch", "status_code": resp.status_code, "error": resp.error})
        if resp.status_code < 500 and resp.status_code != 0 and retry >= MAX_RETRIES_PER_STEP:
            break

    raise HTTPException(status_code=503, detail={"step": step_name, "attempts": attempts})


def _s3_uri_from_outputs(outputs: dict[str, Any]) -> str:
    bucket = outputs.get("bucket")
    object_key = outputs.get("object_key")
    return f"s3://{bucket}/{object_key}" if bucket and object_key else ""


def _run_pipeline(job: JobRequest, db: Session) -> JobResult:
    metrics: dict[str, Any] = {"script_chars": len(job.script), "retries_per_step": MAX_RETRIES_PER_STEP}
    outputs: dict[str, Any] = {}
    errors: list[str] = []

    try:
        t0 = time.perf_counter()
        spoken_script, timing_map = _script_agent_stub(job.script)
        outputs["script_agent"] = {"spoken_script": spoken_script, "timing_map": timing_map}
        STEP_DURATION.labels(step="script_agent").observe(time.perf_counter() - t0)

        common_payload = {
            "job_id": job.job_id,
            "avatar_id": job.avatar_id,
            "script": spoken_script,
            "language": job.language,
            "format": job.format,
            "params": dict(job.params),
        }

        t0 = time.perf_counter()
        tts_payload = {**common_payload, "params": {**common_payload["params"], "voice_id": job.params.get("voice_id", "default")}}
        tts_body, tts_route = _dispatch_with_routing(db, "tts", tts_payload, "tts")
        outputs["tts"] = tts_body.get("outputs", {})
        metrics["tts"] = {**tts_body.get("metrics", {}), **tts_route}
        voice_uri = _s3_uri_from_outputs(outputs["tts"])
        STEP_DURATION.labels(step="tts").observe(time.perf_counter() - t0)

        t0 = time.perf_counter()
        video_payload = {
            **common_payload,
            "params": {
                **common_payload["params"],
                "prompt": common_payload["params"].get("prompt", spoken_script),
                "duration": common_payload["params"].get("duration", 4.0),
                "aspect": common_payload["params"].get("aspect", "16:9"),
                "image_url": common_payload["params"].get("image_url"),
            },
        }
        video_body, video_route = _dispatch_with_routing(db, "video", video_payload, "video")
        outputs["video"] = video_body.get("outputs", {})
        metrics["video"] = {**video_body.get("metrics", {}), **video_route}
        avatar_base_uri = _s3_uri_from_outputs(outputs["video"])
        STEP_DURATION.labels(step="video").observe(time.perf_counter() - t0)

        t0 = time.perf_counter()
        lipsync_payload = {
            **common_payload,
            "params": {**common_payload["params"], "avatar_base_uri": avatar_base_uri, "voice_uri": voice_uri},
        }
        lipsync_body, lipsync_route = _dispatch_with_routing(db, "lipsync", lipsync_payload, "lipsync")
        outputs["lipsync"] = lipsync_body.get("outputs", {})
        metrics["lipsync"] = {**lipsync_body.get("metrics", {}), **lipsync_route}
        lipsync_uri = _s3_uri_from_outputs(outputs["lipsync"])
        STEP_DURATION.labels(step="lipsync").observe(time.perf_counter() - t0)

        t0 = time.perf_counter()
        enhance_payload = {
            **common_payload,
            "params": {
                **common_payload["params"],
                "video_uri": lipsync_uri,
                "enable_upscale": common_payload["params"].get("enable_upscale", True),
                "enable_face_restore": common_payload["params"].get("enable_face_restore", False),
            },
        }
        enhance_body, enhance_route = _dispatch_with_routing(db, "enhance", enhance_payload, "enhance")
        outputs["enhance"] = enhance_body.get("outputs", {})
        metrics["enhance"] = {**enhance_body.get("metrics", {}), **enhance_route}
        enhanced_uri = _s3_uri_from_outputs(outputs["enhance"])
        STEP_DURATION.labels(step="enhance").observe(time.perf_counter() - t0)

        t0 = time.perf_counter()
        qa_payload = {
            **common_payload,
            "params": {
                **common_payload["params"],
                "final_cut_uri": enhanced_uri,
                "av_drift_ms": metrics["lipsync"].get("av_drift_ms", 0),
                "lipsync_score": metrics["lipsync"].get("lipsync_score", 1.0),
            },
        }
        qa_body, qa_route = _dispatch_with_routing(db, "qa", qa_payload, "qa")
        outputs["qa"] = qa_body.get("outputs", {})
        metrics["qa"] = {**qa_body.get("metrics", {}), **qa_route}
        STEP_DURATION.labels(step="qa").observe(time.perf_counter() - t0)

        if not bool(outputs["qa"].get("qa_passed", False)):
            errors.extend(qa_body.get("errors", []))
            return JobResult(job_id=job.job_id, status="failed", outputs=outputs, metrics=metrics, errors=errors)

        outputs["delivery"] = {
            "final_assets_urls": {
                "voice_wav": outputs.get("tts", {}).get("presigned_url"),
                "avatar_base_mp4": outputs.get("video", {}).get("presigned_url"),
                "avatar_lipsynced_mp4": outputs.get("lipsync", {}).get("presigned_url"),
                "enhanced_mp4": outputs.get("enhance", {}).get("presigned_url"),
                "qa_report": outputs.get("qa", {}).get("presigned_url"),
            }
        }
        return JobResult(job_id=job.job_id, status="completed", outputs=outputs, metrics=metrics, errors=[])

    except HTTPException as exc:
        return JobResult(job_id=job.job_id, status="failed", outputs=outputs, metrics=metrics, errors=[str(exc.detail)])


@app.post("/v1/jobs", response_model=JobResult, status_code=202)
def create_job(payload: JobRequest, db: Session = Depends(get_db)) -> JobResult:
    if payload.job_id in STORE:
        raise HTTPException(status_code=409, detail="job_id already exists")
    JOBS_TOTAL.inc()
    logger.info(f"job_created job_id={payload.job_id} avatar_id={payload.avatar_id}")
    result = _run_pipeline(payload, db)
    STORE[payload.job_id] = result
    ORCHESTRATION_TOTAL.labels(status=result.status).inc()
    return result


@app.get("/v1/jobs/{job_id}", response_model=JobResult)
def get_job(job_id: str) -> JobResult:
    job = STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.post("/v1/jobs/{job_id}/retry", response_model=JobResult)
def retry_job(job_id: str, db: Session = Depends(get_db)) -> JobResult:
    job = STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    updated = JobRequest(job_id=job_id, avatar_id="retry", script="retry", language="fr", format="mp4", params={})
    result = _run_pipeline(updated, db)
    STORE[job_id] = result
    JOB_RETRIES_TOTAL.inc()
    logger.info(f"job_retried job_id={job_id}")
    return result


@app.post("/webhooks/n8n/order_created", response_model=N8nOrderCreatedResponse)
def n8n_order_created(payload: N8nOrderCreatedRequest, db: Session = Depends(get_db)) -> N8nOrderCreatedResponse:
    request_payload = JobRequest(
        avatar_id=payload.avatar_id,
        script=payload.script,
        language=payload.language,
        format=payload.format,
        params={"plan": payload.plan, "customer_id": payload.customer_id},
    )
    result = create_job(request_payload, db)
    return N8nOrderCreatedResponse(job_id=result.job_id, status_url=f"/v1/jobs/{result.job_id}")


@app.get("/registry/services", response_model=list[RegistryServiceResponse])
def list_registry_services(db: Session = Depends(get_db)) -> list[RegistryService]:
    return db.query(RegistryService).order_by(RegistryService.id.asc()).all()


@app.post("/registry/services", response_model=RegistryServiceResponse, status_code=201)
def create_registry_service(payload: RegistryServiceCreate, db: Session = Depends(get_db)) -> RegistryService:
    service = RegistryService(**payload.model_dump())
    db.add(service)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="service_name already exists") from exc
    db.refresh(service)
    REGISTRY_UPSERTS_TOTAL.inc()
    logger.info(f"registry_service_created id={service.id} service_name={service.service_name}")
    return service


@app.patch("/registry/services/{service_id}", response_model=RegistryServiceResponse)
def patch_registry_service(service_id: int, payload: RegistryServicePatch, db: Session = Depends(get_db)) -> RegistryService:
    service = db.get(RegistryService, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="registry service not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(service, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="service_name already exists") from exc

    db.refresh(service)
    REGISTRY_UPSERTS_TOTAL.inc()
    logger.info(f"registry_service_updated id={service.id} service_name={service.service_name}")
    return service


@app.get("/healthz", response_model=ServiceHealth)
def healthz() -> ServiceHealth:
    return ServiceHealth(service_name="orchestrator-api", ok=True, gpu={}, version="0.6.0")


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
