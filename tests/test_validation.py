from comfyui_restoration.validation import evaluate_qc, parse_qc_log, run_qc, validate_invariants


def _probe(duration="10"):
    return {"format": {"duration": duration}, "streams": [{"codec_type": "video", "width": 720, "height": 544, "r_frame_rate": "25/1"}, {"codec_type": "audio", "sample_rate": "48000", "channels": 2}]}


def test_validation_accepts_preserved_timeline():
    assert validate_invariants(_probe(), _probe())["valid"] is True


def test_validation_rejects_geometry_and_audio_changes():
    output = _probe()
    output["streams"][0]["width"] = 1280
    output["streams"][1]["channels"] = 1
    result = validate_invariants(_probe(), output)
    assert result["valid"] is False
    assert "video width changed" in result["failures"]
    assert "audio channels changed" in result["failures"]


def test_validation_rejects_chapter_loss():
    source = _probe()
    source["chapters"] = [{"id": 1}]
    output = _probe()
    result = validate_invariants(source, output)
    assert result["valid"] is False
    assert "chapter count changed" in result["failures"]


def test_validation_rejects_decode_qc_failures():
    result = validate_invariants(_probe(), _probe(), qc={"black_seconds": 3, "freeze_events": 1, "clipping_samples": 2})
    assert result["valid"] is False
    assert "excessive black frames" in result["failures"]
    assert "frozen frames detected" in result["failures"]
    assert evaluate_qc({"silence_seconds": 5}, max_silence_seconds=1)["valid"] is False


def test_validation_can_check_video_only_branch_artifacts():
    source = _probe()
    output = {"format": {"duration": "10"}, "streams": [source["streams"][0]]}
    assert validate_invariants(source, output, require_audio=False)["valid"] is True


def test_qc_parser_aggregates_ffmpeg_filter_diagnostics():
    log = "black_duration:1.25 freeze_duration:2 silence_duration:3 Number of clipped samples: 4"
    assert parse_qc_log(log) == {"black_seconds": 1.25, "silence_seconds": 3.0, "freeze_events": 1, "clipping_samples": 4}


def test_run_qc_uses_fixed_command_and_returns_parsed_observations(monkeypatch):
    class Result:
        stderr = "freeze_duration:2"

    seen = []
    monkeypatch.setattr("comfyui_restoration.validation.run_command", lambda command: seen.append(command) or Result())
    result = run_qc("output.mkv")
    assert result["observations"]["freeze_events"] == 1
    assert "-vf" in seen[0]
