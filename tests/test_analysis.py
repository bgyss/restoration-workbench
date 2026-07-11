from comfyui_restoration.analysis import analyze_probe


def test_analysis_reports_progressive_geometry_and_audio_layout():
    result = analyze_probe({"format": {"duration": "12.5"}, "streams": [{"codec_type": "video", "width": 720, "height": 544, "r_frame_rate": "25/1", "field_order": "progressive"}, {"codec_type": "audio", "sample_rate": "48000", "channels": 2}]})
    assert result["duration_seconds"] == 12.5
    assert result["video"]["width"] == 720
    assert result["interlaced_risk"] is False
    assert result["audio"]["channels"] == 2


def test_analysis_flags_interlaced_source():
    result = analyze_probe({"streams": [{"codec_type": "video", "field_order": "tt"}]})
    assert result["interlaced_risk"] is True
