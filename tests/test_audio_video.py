import struct
import wave
from pathlib import Path

import pytest

from comfyui_restoration.audio import detect_clicks, guard_loudness_command, repair_command
from comfyui_restoration.adapters.audio_models import AudioModelRequest
from comfyui_restoration.video import ensure_progressive, experimental_model_request


def test_click_detector_finds_synthetic_full_scale_jump(tmp_path: Path):
    path = tmp_path / "fixture.wav"
    values = [0] * 20 + [32767] + [0] * 20
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(1000)
        stream.writeframes(b"".join(struct.pack("<h", value) for value in values))
    events = detect_clicks(path)
    assert events and events[0]["sample"] == 20


def test_audio_guards_reject_unsafe_peak():
    with pytest.raises(ValueError):
        guard_loudness_command(Path("a"), Path("b"), true_peak=1)
    with pytest.raises(ValueError):
        repair_command(Path("a"), Path("b"), method="shell")


def test_video_lane_refuses_interlaced_and_labels_generation():
    with pytest.raises(ValueError):
        ensure_progressive({"streams": [{"codec_type": "video", "field_order": "tt"}]})
    assert experimental_model_request("model", Path("a"), Path("b"))["lane"] == "experimental_reconstruction"


def test_neural_enhancement_requires_explicit_experimental_label():
    request = AudioModelRequest("voicefixer", Path("a"), Path("b"), mode="enhance")
    with pytest.raises(ValueError):
        request.validate()
