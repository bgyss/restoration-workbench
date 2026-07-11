# Upstream evaluation (implementation baseline)

This is a decision record, not a promise that optional models are bundled. Versions and
licenses must be refreshed before a release or model download. The core package has no runtime
dependencies beyond Python and uses subprocess adapters so incompatible ML environments remain
replaceable.

| Component | Role | Distribution decision |
| --- | --- | --- |
| FFmpeg/FFprobe | decode, analysis, filters, remux | required external tool; invoke with argument arrays |
| DeepFilterNet | optional speech denoise | separate adapter; weights installed by the user |
| VoiceFixer | optional speech reconstruction | experimental only; explicit 44.1/48 kHz boundary |
| Resemble Enhance | optional denoise/reconstruction | experimental only; separate environment likely |
| Essentia | click/discontinuity analysis | not bundled: AGPL boundary must be reviewed |
| Demucs | optional stem routing | optional MIT adapter; inactive upstream risk |
| ComfyUI | graph host | optional host; nodes are thin and API-first |
| VideoHelperSuite | generic video I/O | optional; preservation-aware ingest/remux stays here |

Optional speech adapters use fixed executable names (`voicefixer-runner` and `resemble-enhance`)
with explicit input/output, mode, device, chunk, overlap, and sample-rate arguments. The graph
cannot supply an arbitrary executable path; an unavailable runner fails closed. The runner contract
is intentionally narrow so each separately reviewed environment can be replaced without changing
the artifact or approval model.

The official ComfyUI documentation describes custom nodes as ordinary nodes and supports API
workflows and workflow templates. See [custom nodes](https://docs.comfy.org/custom-nodes/overview),
[workflow API concepts](https://docs.comfy.org/development/core-concepts/workflow), and
[workflow templates](https://docs.comfy.org/custom-nodes/workflow_templates). Candidate model
repositories are linked from the goal prompt and must be pinned with a commit, model hash, and
license record before enabling an adapter. No weights, third-party code, or media are committed.

## MCP reconnaissance (2026-07-10)

The official Comfy Cloud MCP project is a cloud-facing research preview, so it is not a required
dependency for this local-first package. Community servers differ substantially: one local server
uses an HTTP MCP endpoint, while another exposes broad workflow/model-management operations and
permits external model and registry integrations. Those capabilities are broader than this
workbench's least-privilege policy. The project therefore keeps its own narrow JSON-lines contract
and treats an MCP bridge as an adapter. The relevant references are [Comfy Cloud MCP](https://github.com/Comfy-Org/comfy-cloud-mcp),
[local ComfyUI MCP server](https://github.com/joenorton/comfyui-mcp-server), and
[workflow automation MCP server](https://github.com/IO-AtelierTech/comfyui-mcp).

ComfyUI's registry standards prohibit `eval`/`exec` and runtime package installation in custom
nodes; the implementation follows that boundary and keeps subprocess arguments fixed by adapters.
See the [registry security standards](https://docs.comfy.org/registry/standards). Registry names
are globally unique and published versions are immutable, so publication remains a separately
approved release step; see the [registry overview](https://docs.comfy.org/registry/overview).
