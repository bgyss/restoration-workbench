from comfyui_restoration.sampling import plan_samples


def test_sample_planner_has_early_middle_late_and_reasons():
    samples = plan_samples(1000, chapters=[100], defect_times=[900], manual_times=[700], sample_duration=60)
    reasons = {sample["reason"] for sample in samples}
    assert {"early runtime coverage", "middle runtime coverage", "late runtime coverage"} <= reasons
    assert "chapter boundary" in reasons
    assert all(0 <= sample["start"] <= 940 for sample in samples)
