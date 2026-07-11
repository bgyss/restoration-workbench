import struct
import wave
from pathlib import Path

from comfyui_restoration.candidates import audio_candidate_matrix, record_candidate
from comfyui_restoration.metrics import pcm_metrics


def test_candidate_matrix_keeps_untouched_baseline_and_experimental_labels():
    matrix = audio_candidate_matrix()
    assert matrix[0]["id"] == "untouched"
    assert all(item["lane"] == "experimental_reconstruction" for item in matrix if "voicefixer" in item["id"] or "resemble" in item["id"])
    assert record_candidate(matrix[0], metrics={"peak": 0.1}, rejection_reason="not selected")["rejection_reason"] == "not selected"


def test_pcm_metrics_are_sample_accurate(tmp_path: Path):
    path = tmp_path / "x.wav"
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(48_000)
        stream.writeframes(b"".join(struct.pack("<h", value) for value in (0, 32767, -32768, 0)))
    result = pcm_metrics(path)
    assert result["sample_count"] == 4
    assert result["clipping_samples"] == 2
