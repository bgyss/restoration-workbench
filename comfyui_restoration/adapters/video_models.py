"""Replaceable video backend contract; implementations live outside the base package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VideoModelRequest:
    backend: str
    source: Path
    destination: Path
    model_hash: str
    scale: int = 1
    temporal_window: int = 5
    strength: float = 0.1
    seed: int = 0
    device: str = "auto"
    lane: str = "experimental_reconstruction"
    tile_size: int | None = None
    tile_overlap: int = 0
    offload: bool = False

    def validate(self) -> None:
        if not self.backend.strip() or not self.model_hash.strip():
            raise ValueError("video backend and model hash are required")
        if self.scale < 1 or self.temporal_window < 1 or not 0 <= self.strength <= 1:
            raise ValueError("invalid video model parameters")
        if self.tile_size is not None and self.tile_size < 16:
            raise ValueError("tile size is too small")
        if self.tile_overlap < 0 or (self.tile_size is not None and self.tile_overlap >= self.tile_size):
            raise ValueError("invalid tile overlap")
        if self.lane != "experimental_reconstruction":
            raise ValueError("model adapters must remain in the experimental lane")


def request_manifest(request: VideoModelRequest) -> dict:
    request.validate()
    return {"backend": request.backend, "model_hash": request.model_hash, "source": str(request.source), "destination": str(request.destination), "scale": request.scale, "temporal_window": request.temporal_window, "strength": request.strength, "seed": request.seed, "device": request.device, "lane": request.lane, "tile_size": request.tile_size, "tile_overlap": request.tile_overlap, "offload": request.offload}
