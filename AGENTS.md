# Repository Guidelines

## Project Structure & Module Organization

- `scripts/restore.py` is the conservative, sample-first restoration runner.
- `tests/test_restore.py` covers pure helper and safety behavior.
- `docs/prompts/restoration-goal-prompt.md` is the restoration contract; read it before changing pipeline behavior.
- `flake.nix`, `mise.toml`, and `pyproject.toml` define the reproducible toolchain and Python checks.
- Source captures belong outside Git. Root `video/` and `work/` are ignored local directories; use `work/` for generated samples, reports, and outputs.

## Build, Test, and Development Commands

Enter the declared environment and verify media tools:

```sh
nix develop
mise run sync
mise run doctor
```

Run the standard checks with `mise run check`. For a quick Python-only pass,
use `ruff check scripts tests` and `python -m pytest -q`. Run sample restoration
with `python scripts/restore.py --source /path/to/input.mkv --workdir work/run`.
Do not pass `--approve-samples --full` until a human has reviewed all sample
comparison frames, spectrograms, and combing checks.

## Coding Style & Naming Conventions

Target Python 3.12. Use four-space indentation, type annotations for public
functions, `snake_case` identifiers, and concise docstrings where behavior is
not obvious. Keep media actions as explicit ffmpeg/SoX subprocess commands so
the generated report remains reproducible. Ruff enforces a 100-character line
limit; run it before submitting changes.

## Testing Guidelines

Name tests `test_<behavior>` and keep them deterministic and media-free. Test
command construction, parsing, safety checks, and edge cases with temporary
paths; do not commit captures, WAVs, MKVs, or generated review assets. When
changing filters or remux logic, run the three-sample gate and record the
resulting SSIM/loudness evidence in the local restoration report.

## Commit & Pull Request Guidelines

Use short, imperative commit subjects, such as `Add restoration report metrics`
or `Ignore root worktree directory`. Keep each commit focused. Pull requests
should explain pipeline effects, list validation commands, identify any tool
fallbacks, and include representative review assets only when they are safe to
share. Never include source media or absolute local paths.
