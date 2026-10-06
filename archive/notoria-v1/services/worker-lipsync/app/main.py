import os
from pathlib import Path

from shared.schemas import JobRequest
from shared.worker import create_worker_app

USE_FAKE_LIPSYNC = os.getenv("USE_FAKE_LIPSYNC", "true").lower() == "true"


class BaseLipsyncBackend:
    """Interface backend lipsync.

    TODO: brancher Wav2Lip réel (pipeline GPU) sans téléchargement lourd dans ce scaffold.
    """

    def lipsync(self, avatar_base_uri: str, voice_uri: str, output_path: Path) -> None:
        raise NotImplementedError


class FakeLipsyncBackend(BaseLipsyncBackend):
    """Backend léger pour CI/tests: produit un MP4 factice lipsync."""

    def lipsync(self, avatar_base_uri: str, voice_uri: str, output_path: Path) -> None:
        payload = f"FAKE_LIPSYNC_MP4\navatar_base={avatar_base_uri}\nvoice={voice_uri}\n".encode("utf-8")
        output_path.write_bytes(payload)


class Wav2LipStubBackend(BaseLipsyncBackend):
    """Stub d'interface pour futur backend Wav2Lip réel."""

    def lipsync(self, avatar_base_uri: str, voice_uri: str, output_path: Path) -> None:
        # TODO(notoria): implémenter l'appel réel Wav2Lip (GPU worker dédié).
        FakeLipsyncBackend().lipsync(avatar_base_uri, voice_uri, output_path)


def _lipsync_processor(payload: JobRequest, _inputs_dir: Path, outputs_dir: Path):
    avatar_base_uri = str(payload.params.get("avatar_base_uri", "")).strip()
    voice_uri = str(payload.params.get("voice_uri", "")).strip()

    if not avatar_base_uri:
        return outputs_dir / "avatar_lipsynced.mp4", {}, {}, ["missing_required_param:avatar_base_uri"]
    if not voice_uri:
        return outputs_dir / "avatar_lipsynced.mp4", {}, {}, ["missing_required_param:voice_uri"]

    output_path = outputs_dir / "avatar_lipsynced.mp4"
    backend: BaseLipsyncBackend = FakeLipsyncBackend() if USE_FAKE_LIPSYNC else Wav2LipStubBackend()
    backend.lipsync(avatar_base_uri=avatar_base_uri, voice_uri=voice_uri, output_path=output_path)

    # Placeholder metrics until real model scoring is connected.
    lipsync_score = 0.93 if USE_FAKE_LIPSYNC else 0.90
    av_drift_ms = 18.0 if USE_FAKE_LIPSYNC else 25.0

    return (
        output_path,
        {
            "avatar_base_uri": avatar_base_uri,
            "voice_uri": voice_uri,
            "video_mime": "video/mp4",
            "lipsync_mode": "fake" if USE_FAKE_LIPSYNC else "wav2lip_stub",
        },
        {
            "lipsync_score": lipsync_score,
            "av_drift_ms": av_drift_ms,
        },
        [],
    )


app = create_worker_app(
    "lipsync",
    version="0.5.0",
    required_params=["avatar_base_uri", "voice_uri"],
    processor=_lipsync_processor,
)
