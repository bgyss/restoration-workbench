import json
from pathlib import Path

from scripts.run_synthetic_benchmark import run


def test_synthetic_benchmark_writes_probe_and_identity_report(tmp_path: Path):
    report = json.loads(run(tmp_path).read_text())
    assert len(report["fixtures"]) == 3
    assert all(len(item["sha256"]) == 64 for item in report["fixtures"])
    assert all(item["probe"]["streams"] for item in report["fixtures"])
    assert all("faithful_lane_default" in item["video_guardrails"] for item in report["fixtures"])
    interlace = next(item for item in report["fixtures"] if item["name"] == "interlace_probe")
    assert interlace["video_guardrails"]["interlaced_risk"] is True
    music = next(item for item in report["fixtures"] if item["name"] == "music_speech")
    audio = next(stream for stream in music["probe"]["streams"] if stream["codec_type"] == "audio")
    assert audio["channels"] == 2
    click = next(item for item in report["fixtures"] if item["name"] == "speech_click_hiss")
    assert click["audio_metrics"]["peak"] > 0.3
    assert click["click_evaluation"]["recall"] == 1.0
    assert click["repair_evaluation"]["method"] == "adeclick"
    assert click["repair_evaluation"]["before_click_events"] >= click["repair_evaluation"]["after_click_events"]
