# VHS restoration environment

This repository contains the reproducible environment for the pipeline in
[`docs/prompts/restoration-goal-prompt.md`](docs/prompts/restoration-goal-prompt.md).
The source capture and generated media stay outside version control.

The next-generation plan in
[`docs/prompts/comfyui-restoration-workbench-goal-prompt.md`](docs/prompts/comfyui-restoration-workbench-goal-prompt.md)
extends that conservative baseline into a public ComfyUI audio/video restoration workbench with
optional neural reconstruction, sample-gated long runs, and an MCP-ready agent interface.

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

The Nix shell provides ffmpeg (including x264), SoX, the Rust `deep-filter`
CLI with its embedded model, the DeepFilterNet LADSPA plugin, mkvtoolnix,
mediainfo, uv, mise, and rustup. The shell exports the plugin through
`LADSPA_PATH`. DeepFilterNet is speech-oriented and remains subject to the
three-sample ambience review before a full restoration.

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

DeepFilterNet is the default audio method. `--audio-method auto` uses it when
available, then conservative SoX noise reduction, and finally ffmpeg `afftdn`.
The fallback video chain is
`pp7=qp=2:mode=medium,hqdn3d=3:2:6:4`; VapourSynth is not required for this
reproducible first path. The runner never writes to the source and records
commands, tool versions, metrics, and deviations in `RESTORATION_REPORT.md`.
