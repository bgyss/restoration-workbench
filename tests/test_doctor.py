from comfyui_restoration.doctor import report


def test_doctor_reports_environment_and_optional_branch_fields():
    result = report()
    assert {"tools", "audio_adapters", "model_hashes", "comfyui", "node_version", "gpu", "disk", "incompatible_optional_branches"} <= result.keys()
    assert isinstance(result["disk"]["free_bytes"], int)
    assert isinstance(result["incompatible_optional_branches"], list)
