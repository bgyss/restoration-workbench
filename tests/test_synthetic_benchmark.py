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
