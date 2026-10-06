import os
from pathlib import Path

from shared.schemas import JobRequest
from shared.worker import create_worker_app

USE_FAKE_VIDEO = os.getenv("USE_FAKE_VIDEO", "true").lower() == "true"
CUDA_VISIBLE_DEVICES = os.getenv("CUDA_VISIBLE_DEVICES", "")


class BaseVideoBackend:
    """Interface backend video.

    TODO: brancher LTX-Video image-to-video réel (pipeline GPU).
    """

    def render(
        self,
        prompt: str,
        image_url: str | None,
        duration: float,
        aspect: str,
        output_path: Path,
    ) -> None:
        raise NotImplementedError


class FakeVideoBackend(BaseVideoBackend):
    """Backend léger pour CI/tests: produit un MP4 factice."""

    def render(
        self,
        prompt: str,
        image_url: str | None,
        duration: float,
        aspect: str,
        output_path: Path,
    ) -> None:
        payload = (
            f"FAKE_MP4\nprompt={prompt}\nimage_url={image_url}\nduration={duration}\naspect={aspect}\n".encode("utf-8")
        )
        output_path.write_bytes(payload)


class LTXVideoStubBackend(BaseVideoBackend):
    """Stub d'interface pour futur backend LTX-Video réel."""

    def render(
        self,
        prompt: str,
        image_url: str | None,
        duration: float,
        aspect: str,
        output_path: Path,
    ) -> None:
        # TODO(notoria): implémenter l'appel LTX-Video réel avec accélération GPU.
        # Le modèle n'est pas téléchargé dans ce scaffold pour éviter un runtime lourd.
        FakeVideoBackend().render(prompt, image_url, duration, aspect, output_path)


def _video_processor(payload: JobRequest, _inputs_dir: Path, outputs_dir: Path):
    prompt = str(payload.params.get("prompt") or payload.script).strip()
    if not prompt:
        return outputs_dir / "broll.mp4", {}, ["missing_required_param:prompt"]

    image_url = payload.params.get("image_url")
    duration = float(payload.params.get("duration", 4.0))
    aspect = str(payload.params.get("aspect", "16:9"))

    if duration <= 0:
        return outputs_dir / "broll.mp4", {}, ["invalid_param:duration_must_be_positive"]

    output_path = outputs_dir / "broll.mp4"
    backend: BaseVideoBackend = FakeVideoBackend() if USE_FAKE_VIDEO else LTXVideoStubBackend()
    backend.render(prompt=prompt, image_url=image_url, duration=duration, aspect=aspect, output_path=output_path)

    return output_path, {
        "prompt": prompt,
        "image_url": image_url,
        "duration": duration,
        "aspect": aspect,
        "video_mime": "video/mp4",
        "video_mode": "fake" if USE_FAKE_VIDEO else "ltx_stub",
        "cuda_visible_devices": CUDA_VISIBLE_DEVICES,
    }, []


app = create_worker_app(
    "video",
    version="0.5.0",
    required_params=[],
    processor=_video_processor,
)
