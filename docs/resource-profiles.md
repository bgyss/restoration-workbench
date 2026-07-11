# Resource profiles

The base package is CPU-safe for probing, planning, detection, command generation, and manifest
work. Optional neural candidates are measured per adapter and are never silently substituted.

| Profile | Intended use | Default policy |
| --- | --- | --- |
| CPU/conservative | probe, samples, FFmpeg faithful lane | no neural reconstruction |
| 8–12 GB VRAM | short DeepFilterNet/video samples | one candidate at a time, chunked |
| 16–24 GB VRAM | larger sample matrix | bounded concurrency, fixed overlap |
| high-memory | approved full run | only after measured sample projection and free-space check |

The adapter boundary exists because model stacks can require incompatible Python/PyTorch/CUDA
versions. Install each optional runner separately, record its version and model hash, and preserve
the unchanged branch for comparison.

The conservative default is 48 kHz end to end. Select 44.1 kHz explicitly only for adapters whose
tested model boundary requires it, and record the integer sample-count compensation in the run
manifest.

Full-run parameters may include `estimated_storage_bytes`, `min_free_bytes`, and `max_chunks`.
The resumable executor records a free-space preflight before marking a run `running` and refuses
to start when the estimate or chunk bound is unsafe. Use `estimate_storage_bytes()` for a
conservative source-bitrate/intermediate multiplier estimate; replace it with measured sample
projections when available.

Cancellation is persisted as `cancelled`, not `complete`; a later invocation with the same run ID
skips completed chunks and resumes the remaining queue after rechecking approval and resources.

Worker exceptions persist a `failed` status and structured error event before being re-raised. A
later invocation with the same approved parameters can retry the unfinished chunk queue.

When configured, the run state and manifest retain the resource-preflight result and
`projected_seconds` timing estimate alongside actual chunk events, so projected-versus-actual
execution can be audited after completion.

`comfyui_restoration.validation.qc_command()` also provides a decode-time FFmpeg probe for
black-frame, frozen-frame, silence, and clipping observations. Feed parsed observations into
`parse_qc_log()` and then into `evaluate_qc()` or `validate_invariants(..., qc=...)`; these are
hard integrity failures, not subjective quality scores.

Branch artifacts can be validated with `require_audio=False` (for a video-only intermediate) or
`require_video=False`; final remux outputs should use both defaults and an authoritative source
probe, including the source audio timeline offset.

For a local output, `python scripts/run_qc.py OUTPUT QC_RECORD.json` runs that fixed command and
persists both parsed observations and the raw diagnostic log. The script accepts only a media path
and output record path; filter expressions are not workflow inputs.

`mise run doctor` reports tool versions, optional adapter availability, configured ComfyUI/node
versions, model-hash records, GPU backend summary, free disk space, and unavailable optional
branches. It performs no model download or network probe.
