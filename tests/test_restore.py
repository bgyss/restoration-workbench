from pathlib import Path

import pytest

from scripts.restore import quote, safe_workdir, validate_source, video_filter


def test_quote_handles_spaces_and_single_quotes():
    assert quote("The Garden (Wiseman, 2005).mkv") == "'The Garden (Wiseman, 2005).mkv'"
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
