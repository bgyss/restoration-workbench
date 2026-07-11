import json
from pathlib import Path

from comfyui_restoration.benchmark import FIXTURES, manifest


def test_checked_in_synthetic_manifest_matches_executable_fixture_contract():
    path = Path(__file__).parents[1] / "examples" / "benchmarks" / "synthetic.json"
    checked_in = json.loads(path.read_text())
    generated = manifest()
    assert checked_in == generated
    assert {fixture["name"] for fixture in checked_in["fixtures"]} == {fixture.name for fixture in FIXTURES}
