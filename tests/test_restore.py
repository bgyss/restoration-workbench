from pathlib import Path

import pytest

from scripts.restore import (
    baseline_times,
    combing_times,
    projected_hours,
    quote,
    read_integrated_loudness,
    safe_workdir,
    sample_ssim,
    validate_source,
    video_filter,
)


def test_quote_handles_spaces_and_single_quotes():
    assert quote("input.mkv") == "'input.mkv'"
    assert quote("a'b") == "'a'\\''b'"


def test_filter_is_conservative_ffmpeg_fallback():
    assert video_filter() == "pp7=qp=2:mode=medium,hqdn3d=3:2:6:4"


def test_validate_source_rejects_wrong_dimensions():
    data = {
        "streams": [
            {"codec_type": "video", "width": 1920, "height": 1080, "field_order": "progressive", "r_frame_rate": "25/1"},
            {"codec_type": "audio", "sample_rate": "48000", "channels": 2},
        ]
    }
    with pytest.raises(SystemExit, match="720x544"):
        validate_source(data)


def test_reference_times_stay_inside_shorter_capture():
    assert max(baseline_times(100)) < 100
    assert max(combing_times(100)) < 100
    assert len(combing_times(1000)) == 12


def test_projected_hours_converts_seconds_to_hours():
    assert projected_hours(16.3, 11907.765, 60) == pytest.approx(0.8985, rel=0.01)


def test_metric_readers(tmp_path: Path):
    loudness = tmp_path / "loudness.txt"
    loudness.write_text("Integrated loudness:\n  I:         -20.7 LUFS\n")
    review = tmp_path / "review"
    review.mkdir()
    (review / "ssim-A.log").write_text("n:1 All:0.970000\nn:2 All:0.990000\n")
    assert read_integrated_loudness(loudness) == "-20.7 LUFS"
    assert sample_ssim(tmp_path) == {"A": 0.98}


def test_safe_workdir_rejects_source_directory(tmp_path: Path):
    source = tmp_path / "source.mkv"
    source.touch()
    with pytest.raises(SystemExit, match="source's directory"):
        safe_workdir(source, tmp_path)


def test_safe_workdir_creates_expected_layout(tmp_path: Path):
    source = tmp_path / "source.mkv"
    source.touch()
    workdir = tmp_path / "work"
    safe_workdir(source, workdir)
    assert {p.name for p in workdir.iterdir()} == {"baseline", "samples", "review", "output"}
