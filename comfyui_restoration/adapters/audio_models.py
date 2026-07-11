"""Narrow subprocess contracts for optional speech models."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioModelRequest:
    adapter: str
    source: Path
    destination: Path
    mode: str = "denoise"
    attenuation_db: float = 6.0
    device: str = "auto"
    experimental_reconstruction: bool = False

    def validate(self) -> None:
        if self.adapter not in {"deepfilternet", "voicefixer", "resemble_enhance", "demucs"}:
            raise ValueError("unsupported optional audio adapter")
        if self.attenuation_db < 0 or self.attenuation_db > 30:
            raise ValueError("attenuation must be between 0 and 30 dB")
        if self.adapter in {"voicefixer", "resemble_enhance"} and not self.experimental_reconstruction and self.mode == "enhance":
            raise ValueError("enhancement mode must be explicitly labeled experimental_reconstruction")


def available_audio_adapters() -> dict[str, bool]:
    return {"deepfilternet": shutil.which("deep-filter") is not None, "voicefixer": False, "resemble_enhance": False, "demucs": shutil.which("demucs") is not None}


def command(request: AudioModelRequest) -> list[str]:
    request.validate()
    if request.adapter == "deepfilternet":
        return ["deep-filter", "--atten-lim-db", str(request.attenuation_db), "--output-dir", str(request.destination.parent), str(request.source)]
    if request.adapter == "demucs":
        return ["demucs", "--out", str(request.destination.parent), str(request.source)]
    # These models intentionally require a separately installed runner; never infer or execute it.
    raise RuntimeError(f"{request.adapter} adapter requires an explicitly configured subprocess environment")

