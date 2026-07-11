from comfyui_restoration.video_candidates import candidate_by_id, candidate_catalog


def test_video_catalog_has_two_faithful_and_two_temporal_candidates():
    catalog = candidate_catalog()
    assert sum(item["lane"] == "faithful" for item in catalog) >= 2
    assert sum(item["kind"] == "temporally_aware_neural" for item in catalog) >= 2
    assert candidate_by_id("ffmpeg-faithful-baseline").default is True


def test_unavailable_candidates_are_explicitly_opt_in():
    for item in candidate_catalog():
        if item["id"] != "ffmpeg-faithful-baseline":
            assert item["available"] is False
