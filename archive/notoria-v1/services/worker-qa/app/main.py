import json
import os
from pathlib import Path

from shared.schemas import JobRequest
from shared.worker import create_worker_app

USE_FAKE_QA = os.getenv("USE_FAKE_QA", "true").lower() == "true"


class BaseQABackend:
    """Interface QA backend.

    TODO: brancher analyse vidéo réelle (freeze-frame, blink-rate, etc.)
    avec un moteur dédié.
    """

    def analyze(self, final_cut_uri: str, output_path: Path, report: dict) -> None:
        raise NotImplementedError


class FakeQABackend(BaseQABackend):
    """Backend QA léger pour CI/tests."""

    def analyze(self, final_cut_uri: str, output_path: Path, report: dict) -> None:
        report["analysis_mode"] = "fake"
        report["analyzed_uri"] = final_cut_uri
        output_path.write_text(json.dumps(report, indent=2))


class QAStubBackend(BaseQABackend):
    """Stub pour futur backend QA réel."""

    def analyze(self, final_cut_uri: str, output_path: Path, report: dict) -> None:
        # TODO(notoria): implémenter la détection réelle freeze/blink/sync.
        FakeQABackend().analyze(final_cut_uri, output_path, report)


def _recommended_step_to_retry(report: dict) -> str:
    if report["freeze_frame_detected"]:
        return "video"
    if report["av_drift_ms"] > 50 or report["lipsync_score"] < report["lipsync_threshold"]:
        return "lipsync"
    return "tts"


def _qa_processor(payload: JobRequest, _inputs_dir: Path, outputs_dir: Path):
    final_cut_uri = str(payload.params.get("final_cut_uri", "")).strip()
    if not final_cut_uri:
        return outputs_dir / "qa_report.json", {}, {}, ["missing_required_param:final_cut_uri"]

    av_drift_ms = float(payload.params.get("av_drift_ms", 0.0))
    lipsync_score = float(payload.params.get("lipsync_score", 1.0))
    lipsync_threshold = float(payload.params.get("lipsync_threshold", 0.85))
    freeze_frame_detected = bool(payload.params.get("freeze_frame_detected", False))
    blink_rate = float(payload.params.get("blink_rate", 16.0))

    blink_rate_min = float(payload.params.get("blink_rate_min", 8.0))
    blink_rate_max = float(payload.params.get("blink_rate_max", 30.0))

    rules = {
        "av_drift_ms_lte_50": av_drift_ms <= 50,
        "lipsync_score_gte_threshold": lipsync_score >= lipsync_threshold,
        "freeze_frame_detected_false": freeze_frame_detected is False,
        "blink_rate_in_range": blink_rate_min <= blink_rate <= blink_rate_max,
    }

    qa_passed = all(rules.values())
    report = {
        "job_id": payload.job_id,
        "qa_passed": qa_passed,
        "av_drift_ms": av_drift_ms,
        "lipsync_score": lipsync_score,
        "lipsync_threshold": lipsync_threshold,
        "freeze_frame_detected": freeze_frame_detected,
        "blink_rate": blink_rate,
        "blink_rate_range": [blink_rate_min, blink_rate_max],
        "rules": rules,
    }

    output_path = outputs_dir / "qa_report.json"
    backend: BaseQABackend = FakeQABackend() if USE_FAKE_QA else QAStubBackend()
    backend.analyze(final_cut_uri=final_cut_uri, output_path=output_path, report=report)

    errors: list[str] = []
    recommended_step_to_retry = None
    if not qa_passed:
        failed_rules = [name for name, ok in rules.items() if not ok]
        errors = [f"qa_rule_failed:{rule}" for rule in failed_rules]
        recommended_step_to_retry = _recommended_step_to_retry(report)

    return (
        output_path,
        {
            "final_cut_uri": final_cut_uri,
            "qa_passed": qa_passed,
            "recommended_step_to_retry": recommended_step_to_retry,
            "report_mime": "application/json",
            "qa_mode": "fake" if USE_FAKE_QA else "qa_stub",
        },
        {
            "av_drift_ms": av_drift_ms,
            "lipsync_score": lipsync_score,
            "freeze_frame_detected": freeze_frame_detected,
            "blink_rate": blink_rate,
        },
        errors,
    )


app = create_worker_app(
    "qa",
    version="0.5.0",
    required_params=["final_cut_uri"],
    processor=_qa_processor,
)
