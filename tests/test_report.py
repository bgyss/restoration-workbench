import json
from pathlib import Path

from comfyui_restoration.report import export_json, export_markdown


def test_report_exports_redacted_json_and_markdown(tmp_path: Path):
    source = tmp_path / "source.json"
    source.write_text(json.dumps({"status": "complete", "path": str(tmp_path / "media.mkv")}))
    json_out, markdown_out = tmp_path / "out.json", tmp_path / "out.md"
    export_json(source, json_out, tmp_path)
    export_markdown(source, markdown_out, tmp_path)
    assert "<workspace>" in json_out.read_text()
    assert "# Restoration report" in markdown_out.read_text()
