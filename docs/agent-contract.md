# Agent-facing contract

The core exposes these logical operations for a future ComfyUI/MCP bridge:

`inspect_restoration_capabilities`, `probe_media`, `plan_samples`, `run_sample_candidates`,
`get_run_status`, `cancel_run`, `list_candidates`, `build_review_bundle`, `record_human_approval`,
`run_approved_full_restoration`, `validate_output`, and `export_restoration_report`.

Each request carries an idempotency key and a workspace-relative path. The bridge must resolve
paths with `workspace_path`, reject symlinks and traversal, refuse source collisions, and apply
bounded duration, chunk, concurrency, and storage limits. Commands are selected by the adapter;
workflow input cannot supply shell text, executable paths, downloads, or Python.

Analysis may create candidates and review material. Only a human-authority `Approval` whose
candidate hash exactly matches the requested parameters may start a full run. The agent cannot
construct an approval through the public operation. Reports must redact absolute paths and private
media metadata before export.

The stdio launcher reads the optional `COMFYUI_RESTORATION_APPROVAL_SECRET` only from the host
environment and passes it to the local service; it is never accepted as a workflow or request
field. Without that host configuration, approval and full-run operations fail closed.

Approval records returned by `record_human_approval` are JSON-serializable and can be passed
unchanged to `run_approved_full_restoration`; the service reconstructs and re-verifies the typed
record before execution.

`validate_output` accepts an optional `include_qc` flag. When enabled, it returns the fixed FFmpeg
QC record alongside decode/probe and preservation evidence; it does not accept caller-supplied
filters.
