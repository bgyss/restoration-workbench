from pathlib import Path

from scripts.benchmark_deepfilter import benchmark


def test_optional_deepfilter_benchmark_records_unavailable_without_failing(monkeypatch, tmp_path: Path):
    source = tmp_path / "input.wav"
    source.write_bytes(b"synthetic-placeholder")
    monkeypatch.setattr("scripts.benchmark_deepfilter.shutil.which", lambda _: None)
    result = benchmark(source, tmp_path / "outputs", tmp_path / "record.json")
    assert result["status"] == "unavailable"
    assert result["source_sha256"]
