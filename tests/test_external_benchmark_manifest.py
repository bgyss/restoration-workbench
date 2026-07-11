import json
from pathlib import Path


def test_external_manifest_is_rights_traceable_and_does_not_bundle_media():
    path = Path(__file__).parents[1] / "examples" / "benchmarks" / "external-sources.json"
    document = json.loads(path.read_text())
    sources = document["sources"]
    assert len(sources) >= 3
    assert len({source["id"] for source in sources}) == len(sources)
    for source in sources:
        assert source["source_url"].startswith("https://")
        assert source["rights_url"].startswith("https://")
        assert source["license"]
        assert source["failure_modes"]
        assert source["download_status"] == "not_fetched"
        assert source["sha256"] is None


def test_external_manifest_has_checked_in_schema():
    schema = Path(__file__).parents[1] / "comfyui_restoration" / "schemas" / "external-sources.schema.json"
    assert schema.exists()
    assert json.loads(schema.read_text())["properties"]["sources"]["minItems"] == 3
