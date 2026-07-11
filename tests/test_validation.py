from comfyui_restoration.validation import validate_invariants


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
