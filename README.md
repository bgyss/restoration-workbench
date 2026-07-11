# VHS restoration environment

This repository contains the reproducible environment for the pipeline in
[`docs/prompts/restoration-goal-prompt.md`](docs/prompts/restoration-goal-prompt.md).
The source capture and generated media stay outside version control.

The next-generation plan in
[`docs/prompts/comfyui-restoration-workbench-goal-prompt.md`](docs/prompts/comfyui-restoration-workbench-goal-prompt.md)
extends that conservative baseline into a public ComfyUI audio/video restoration workbench with
optional neural reconstruction, sample-gated long runs, and an MCP-ready agent interface.

The installable distribution is `comfyui-restoration-workbench` and its Python package is
`comfyui_restoration`. It provides file-backed typed artifacts,
workspace/path safety, versioned run manifests, and thin ComfyUI nodes. Install or copy this
checkout into `custom_nodes/`; the generic workflow in `examples/workflows/` is intentionally
media-free. Optional neural adapters are not required for the conservative path.

The package deliberately ships explicit bypass nodes while adapters are being evaluated. A stub
branch cannot claim restoration, and full execution must remain downstream of a human approval
artifact. See [`docs/upstream-evaluation.md`](docs/upstream-evaluation.md) for the current
integration/licensing boundary.

## Install as a ComfyUI custom node

Copy or clone this repository under `ComfyUI/custom_nodes/comfyui-restoration/`, then restart
ComfyUI. The base package uses Python standard-library orchestration and external FFmpeg; optional
model runners are deliberately installed and pinned separately. Load
`examples/workflows/generic_restoration_review.json` for the media-free graph, replace its local
input, and review samples before using the full workflow. API-format equivalents are provided
beside the UI workflows.

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

## Workbench architecture

The graph passes file-backed artifacts and JSON manifests rather than feature-length media tensors:

```text
ingest -> probe/analyze -> sample plan -> audio/video branches -> review bundle
       -> signed human gate -> resumable run -> preservation remux -> validation/report
```

The conservative faithful branch is always retained. Experimental neural branches are optional,
explicitly labeled, and never imply that generated detail is recovered historical fact.

## Node catalog

- Ingest and analysis: `RestorationLoadMedia`, `AnalyzeSource`, `PlanRepresentativeSamples`,
  `ExtractLosslessAudio`, `DetectAudioDefects`.
- Audio: `RepairAudioDefects`, `DeepFilterNetAudio`, `VoiceFixerAudio`, `ResembleEnhanceAudio`,
  `DemucsSeparateRecombine`, `AudioSegmentRouter`, `AudioEQLoudnessGuard`.
- Video: `VideoBaselineRestore`, `VideoInterlaceHandler`, `VideoModelAdapter`,
  `VideoChunkPlannerStitcher`.
- Review and execution: `CompareCandidates`, `HumanApprovalGate`, `ResumableFullRun`.
- Output: `PreservationAwareRemux`, `ValidateRestoration`, `ExportReviewReport`.

The review workflow is the default entry point. The full workflow requires an approval record tied
to candidate parameters and a host signature; graph execution cannot self-approve.

## Hardware and limitations

| Profile | Supported use | Expectation |
| --- | --- | --- |
| CPU/conservative | Probe, samples, DSP, faithful FFmpeg lane | Recommended baseline; no neural reconstruction |
| 8–12 GB VRAM | Short DeepFilterNet/video samples | One candidate at a time, chunked |
| 16–24 GB VRAM | Larger sample matrix | Fixed overlap and bounded concurrency |
| High memory | Approved full run | Requires measured sample projection and free-space preflight |

VoiceFixer, Resemble Enhance, Demucs, BasicVSR++, and RVRT are not bundled. Their runners,
weights, licenses, hashes, and hardware requirements must be reviewed separately. Optional model
stacks may need isolated environments because their Python/PyTorch/CUDA requirements can conflict.
The current production identity-backed approval/attestation workflow is deliberately a stretch goal;
the local HMAC gate is the sample-first milestone.

## Validation and development

```sh
mise run check
mise run test-workflows
mise run test-e2e-small
mise run audit-public
```

Use `scripts/run_qc.py` for fixed FFmpeg black/freeze/silence/clipping diagnostics and
`scripts/record_external_fixture.py` to record checksum/probe evidence for an authorized external
fixture. Neither command downloads media. See [`docs/release-readiness.md`](docs/release-readiness.md)
before treating a checkout as publishable.
