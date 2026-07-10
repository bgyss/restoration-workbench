# VHS restoration environment

This repository contains the reproducible environment for the pipeline in
[`docs/prompts/restoration-goal-prompt.md`](docs/prompts/restoration-goal-prompt.md).
The source capture and generated media stay outside version control.

## First use

With Nix installed:

```sh
nix develop
mise trust
mise run sync
mise run doctor
```

`mise` pins Python 3.12, uv, and the stable Rust toolchain. `rust-toolchain.toml`
also makes rustup select stable with `rustfmt` and `clippy` whenever Rust is
invoked from this checkout.

The Nix shell provides ffmpeg (including x264), sox, mkvtoolnix, mediainfo,
uv, mise, and rustup. DeepFilterNet is intentionally not locked into the base
Python project because it is a larger, speech-oriented dependency and must be
evaluated on the three restoration samples before use. Install it into the
project environment when the audio samples are ready:

```sh
uv pip install deepfilternet
```

Use `UV_CACHE_DIR=.uv-cache` for direct uv commands outside mise. Never place
the source media in the checkout; use a separate working directory as required
by the restoration prompt.

## Run the pipeline

The checked-in runner performs Phase 1 verification, extracts the three
sample clips, restores audio, encodes filtered samples, and writes a report.
It stops before the expensive full encode until the combing frames and all
sample comparisons have been reviewed:

```sh
python scripts/restore.py \
  --source "/path/to/The Garden (Wiseman, 2005).mkv" \
  --workdir "/path/to/garden-restoration"

# After reviewing baseline/combing-check-* and review/sample-* assets:
python scripts/restore.py \
  --source "/path/to/The Garden (Wiseman, 2005).mkv" \
  --workdir "/path/to/garden-restoration" \
  --approve-samples --full
```

`--audio-method auto` uses DeepFilterNet when `deep-filter` is installed and
otherwise uses conservative SoX noise reduction. The fallback video chain is
`pp7=qp=2:mode=medium,hqdn3d=3:2:6:4`; VapourSynth is not required for this
reproducible first path. The runner never writes to the source and records
commands, tool versions, metrics, and deviations in `RESTORATION_REPORT.md`.
