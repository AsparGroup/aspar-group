import os
from pathlib import Path

from shared.schemas import JobRequest
from shared.worker import create_worker_app

USE_FAKE_ENHANCE = os.getenv("USE_FAKE_ENHANCE", "true").lower() == "true"


class BaseEnhanceBackend:
    """Interface backend enhance.

    TODO: brancher Real-ESRGAN/GFPGAN réels (pipeline GPU) sans runtime lourd ici.
    """

    def enhance(
        self,
        video_uri: str,
        enable_upscale: bool,
        enable_face_restore: bool,
        output_path: Path,
    ) -> None:
        raise NotImplementedError


class FakeEnhanceBackend(BaseEnhanceBackend):
    """Backend CI/tests: génère un MP4 factice enrichi de métadonnées."""

    def enhance(
        self,
        video_uri: str,
        enable_upscale: bool,
        enable_face_restore: bool,
        output_path: Path,
    ) -> None:
        payload = (
            f"FAKE_ENHANCED_MP4\nvideo_uri={video_uri}\n"
            f"enable_upscale={enable_upscale}\nenable_face_restore={enable_face_restore}\n"
        ).encode("utf-8")
        output_path.write_bytes(payload)


class EnhanceStubBackend(BaseEnhanceBackend):
    """Stub pour futur backend réel (Real-ESRGAN + GFPGAN)."""

    def enhance(
        self,
        video_uri: str,
        enable_upscale: bool,
        enable_face_restore: bool,
        output_path: Path,
    ) -> None:
        # TODO(notoria): implémenter l'enhance réel avec étapes optionnelles:
        # 1) upscale (Real-ESRGAN), 2) face restore (GFPGAN).
        FakeEnhanceBackend().enhance(video_uri, enable_upscale, enable_face_restore, output_path)


def _enhance_processor(payload: JobRequest, _inputs_dir: Path, outputs_dir: Path):
    video_uri = str(payload.params.get("video_uri", "")).strip()
    if not video_uri:
        return outputs_dir / "enhanced.mp4", {}, {}, ["missing_required_param:video_uri"]

    enable_upscale = bool(payload.params.get("enable_upscale", True))
    enable_face_restore = bool(payload.params.get("enable_face_restore", False))

    output_path = outputs_dir / "enhanced.mp4"
    backend: BaseEnhanceBackend = FakeEnhanceBackend() if USE_FAKE_ENHANCE else EnhanceStubBackend()
    backend.enhance(
        video_uri=video_uri,
        enable_upscale=enable_upscale,
        enable_face_restore=enable_face_restore,
        output_path=output_path,
    )

    return (
        output_path,
        {
            "video_uri": video_uri,
            "video_mime": "video/mp4",
            "enhance_mode": "fake" if USE_FAKE_ENHANCE else "enhance_stub",
        },
        {
            "enable_upscale": enable_upscale,
            "enable_face_restore": enable_face_restore,
        },
        [],
    )


app = create_worker_app(
    "enhance",
    version="0.5.0",
    required_params=["video_uri"],
    processor=_enhance_processor,
)
