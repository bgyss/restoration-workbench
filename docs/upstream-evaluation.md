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

The official ComfyUI documentation describes custom nodes as ordinary nodes and supports API
workflows and workflow templates. See [custom nodes](https://docs.comfy.org/custom-nodes/overview),
[workflow API concepts](https://docs.comfy.org/development/core-concepts/workflow), and
[workflow templates](https://docs.comfy.org/custom-nodes/workflow_templates). Candidate model
repositories are linked from the goal prompt and must be pinned with a commit, model hash, and
license record before enabling an adapter. No weights, third-party code, or media are committed.

