import os
import struct
import wave
from pathlib import Path

from shared.schemas import JobRequest
from shared.worker import create_worker_app

USE_FAKE_TTS = os.getenv("USE_FAKE_TTS", "true").lower() == "true"


class BaseTTSBackend:
    """Interface TTS backend.

    TODO: implémenter un backend XTTS réel (chargement modèle + inférence GPU)
    dans une classe dédiée qui respecte cette interface.
    """

    def synthesize(self, script: str, voice_id: str, output_path: Path) -> None:
        raise NotImplementedError


class FakeTTSBackend(BaseTTSBackend):
    """Backend léger pour CI/tests: produit un WAV de silence."""

    def synthesize(self, script: str, voice_id: str, output_path: Path) -> None:
        sample_rate = 16000
        duration_seconds = max(1, min(10, len(script) // 40 + 1))
        total_frames = sample_rate * duration_seconds

        with wave.open(str(output_path), "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            silence_frame = struct.pack("<h", 0)
            wav_file.writeframes(silence_frame * total_frames)


class XTTSStubBackend(BaseTTSBackend):
    """Stub d'interface pour futur backend XTTS réel."""

    def synthesize(self, script: str, voice_id: str, output_path: Path) -> None:
        # TODO(notoria): remplacer par l'appel réel XTTS quand le runtime GPU sera branché.
        # Cette implémentation évite de télécharger un modèle lourd pour le moment.
        FakeTTSBackend().synthesize(script=script, voice_id=voice_id, output_path=output_path)


def _tts_processor(payload: JobRequest, _inputs_dir: Path, outputs_dir: Path):
    voice_id = str(payload.params.get("voice_id", "")).strip()
    if not voice_id:
        return outputs_dir / "voice.wav", {}, ["missing_required_param:voice_id"]

    output_path = outputs_dir / "voice.wav"
    backend: BaseTTSBackend = FakeTTSBackend() if USE_FAKE_TTS else XTTSStubBackend()
    backend.synthesize(script=payload.script, voice_id=voice_id, output_path=output_path)

    return output_path, {"voice_id": voice_id, "audio_mime": "audio/wav", "tts_mode": "fake" if USE_FAKE_TTS else "xtts_stub"}, []


app = create_worker_app(
    "tts",
    version="0.5.0",
    required_params=["voice_id"],
    processor=_tts_processor,
)
