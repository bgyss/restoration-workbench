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
    chunk_seconds: float = 30.0
    overlap_seconds: float = 2.0
    bypass: bool = False
    master_rate: int = 48_000
    model_rate: int = 48_000

    def validate(self) -> None:
        if self.adapter not in {"deepfilternet", "voicefixer", "resemble_enhance", "demucs"}:
            raise ValueError("unsupported optional audio adapter")
        if self.attenuation_db < 0 or self.attenuation_db > 30:
            raise ValueError("attenuation must be between 0 and 30 dB")
        if self.chunk_seconds <= 0 or self.overlap_seconds < 0 or self.overlap_seconds >= self.chunk_seconds:
            raise ValueError("overlap must be non-negative and shorter than the chunk")
        if self.device not in {"auto", "cpu", "cuda", "mps"}:
            raise ValueError("unsupported device")
        if self.master_rate <= 0 or self.model_rate <= 0:
            raise ValueError("sample rates must be positive")
        if self.adapter not in {"voicefixer", "resemble_enhance"} and self.model_rate != self.master_rate:
            raise ValueError("non-resampling adapters must use the master sample rate")
        if self.adapter in {"voicefixer", "resemble_enhance"} and not self.experimental_reconstruction and self.mode == "enhance":
            raise ValueError("enhancement mode must be explicitly labeled experimental_reconstruction")


def available_audio_adapters() -> dict[str, bool]:
    return {"deepfilternet": shutil.which("deep-filter") is not None, "voicefixer": shutil.which("voicefixer-runner") is not None, "resemble_enhance": shutil.which("resemble-enhance") is not None, "demucs": shutil.which("demucs") is not None}


def round_trip_sample_count(sample_count: int, source_rate: int, target_rate: int) -> int:
    if sample_count < 0 or source_rate <= 0 or target_rate <= 0:
        raise ValueError("invalid sample-count/rate values")
    forward = (sample_count * target_rate + source_rate // 2) // source_rate
    return (forward * source_rate + target_rate // 2) // target_rate


def command(request: AudioModelRequest) -> list[str]:
    request.validate()
    if request.bypass:
        return ["bypass", str(request.source), str(request.destination)]
    if request.adapter == "deepfilternet":
        return ["deep-filter", "--atten-lim-db", str(request.attenuation_db), "--output-dir", str(request.destination.parent), str(request.source)]
    if request.adapter == "demucs":
        return ["demucs", "--out", str(request.destination.parent), str(request.source)]
    runner = {"voicefixer": "voicefixer-runner", "resemble_enhance": "resemble-enhance"}[request.adapter]
    if shutil.which(runner) is None:
        raise RuntimeError(f"{request.adapter} runner is unavailable: install the reviewed adapter separately")
    arguments = [runner, "--input", str(request.source), "--output", str(request.destination), "--mode", request.mode, "--device", request.device, "--chunk-seconds", str(request.chunk_seconds), "--overlap-seconds", str(request.overlap_seconds)]
    if request.adapter in {"voicefixer", "resemble_enhance"}:
        arguments.extend(["--model-rate", str(request.model_rate), "--master-rate", str(request.master_rate)])
    return arguments
