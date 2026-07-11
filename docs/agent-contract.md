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

