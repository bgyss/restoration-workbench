"""Repository safety audit for media, credentials, personal paths, and JSON artifacts."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

FORBIDDEN_PATHS = re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+|/Applications/[A-Za-z0-9._-]+")
MEDIA_SUFFIXES = {".mkv", ".mp4", ".mov", ".wav", ".flac", ".mp3", ".safetensors", ".onnx"}
SECRET_PATTERNS = (re.compile(r"(?:api[_-]?key|secret|token)\s*[:=]\s*['\"][^'\"]+", re.I), re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"))


def audit(root: Path) -> list[str]:
    failures: list[str] = []
    ignored = {".git", ".venv", ".uv-cache", "__pycache__", "video", "work"}
    for path in root.rglob("*"):
        if not path.is_file() or any(part in ignored for part in path.parts):
            continue
        if path.suffix.lower() in MEDIA_SUFFIXES and path.name not in {".gitkeep"}:
            failures.append(f"media or model file present: {path.relative_to(root)}")
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        if FORBIDDEN_PATHS.search(text):
            failures.append(f"personal path present: {path.relative_to(root)}")
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            failures.append(f"credential-like text present: {path.relative_to(root)}")
        if path.suffix == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError as error:
                failures.append(f"invalid JSON {path.relative_to(root)}: {error.msg}")
    return failures


def audit_git_history(root: Path) -> list[str]:
    """Scan names and blob contents reachable from Git refs without checking out media."""
    failures: list[str] = []
    result = subprocess.run(("git", "-C", str(root), "rev-list", "--objects", "--all"), capture_output=True, text=True)
    if result.returncode:
        return ["unable to inspect Git history"]
    for line in result.stdout.splitlines():
        object_id, _, name = line.partition(" ")
        path = Path(name)
        if path.suffix.lower() in MEDIA_SUFFIXES:
            failures.append(f"historical media or model object: {name}")
            continue
        blob = subprocess.run(("git", "-C", str(root), "cat-file", "-p", object_id), capture_output=True)
        if blob.returncode or len(blob.stdout) > 2_000_000:
            continue
        try:
            text = blob.stdout.decode()
        except UnicodeDecodeError:
            continue
        if FORBIDDEN_PATHS.search(text) or any(pattern.search(text) for pattern in SECRET_PATTERNS):
            failures.append(f"sensitive historical content: {name}")
    return failures


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failures = audit(root) + audit_git_history(root)
    if failures:
        print("\n".join(failures))
        return 1
    print("public audit passed")
    return 0
