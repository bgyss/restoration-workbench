import hashlib
from pathlib import Path

import pytest

from comfyui_restoration.external_fixtures import record_fixture


def test_record_fixture_hashes_external_file_without_copying_media(tmp_path: Path):
    repository = tmp_path / "repo"
    repository.mkdir()
    source = tmp_path / "download" / "clip.mp4"
    source.parent.mkdir()
    source.write_bytes(b"fixture")
    record = repository / "work" / "fixture.json"
    evidence = record_fixture(
        source, record, source_id="fixture", source_url="https://example.test/source",
        rights_url="https://example.test/rights", license_name="public-domain",
        repository_root=repository, probe={"streams": []},
    )
    assert evidence["sha256"] == hashlib.sha256(b"fixture").hexdigest()
    assert source.exists()
    assert record.exists()


def test_record_fixture_rejects_repository_media(tmp_path: Path):
    source = tmp_path / "repo" / "clip.mp4"
    source.parent.mkdir()
    source.write_bytes(b"fixture")
    with pytest.raises(ValueError, match="outside the repository"):
        record_fixture(
            source, tmp_path / "record.json", source_id="fixture",
            source_url="https://example.test/source", rights_url="https://example.test/rights",
            license_name="public-domain", repository_root=tmp_path / "repo", probe={},
        )
