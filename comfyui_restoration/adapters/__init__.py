"""Optional model adapters. None are imported or downloaded by the core package."""

from .audio_models import AudioModelRequest, available_audio_adapters

__all__ = ["AudioModelRequest", "available_audio_adapters"]

