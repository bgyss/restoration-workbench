# ComfyUI Desktop quickstart

This tutorial gets the restoration nodes loaded in a local ComfyUI Desktop installation and
runs the generic review workflow on a local media file. It is a test guide, not a release claim:
do not formally release this workflow or node setup until it has been tested and reviewed in
ComfyUI Desktop.

## 1. Install the custom node package

1. Download or clone this repository.
2. Copy the repository directory into your ComfyUI `custom_nodes/` directory. For example:

   ```text
   ComfyUI/
     custom_nodes/
       comfyui-restoration/
         comfyui_restoration/
         examples/
         pyproject.toml
   ```

3. Restart ComfyUI Desktop.
4. Open the ComfyUI log or node search and confirm that nodes such as `Restoration Load Media`
   and `Plan Representative Samples` are available.

The conservative nodes use the ComfyUI host Python environment and external FFmpeg. Optional
neural adapters are not required for this first test. Install optional model runners separately
only after reviewing their license and hardware requirements.

## 2. Prepare a safe test input

Use a video that you are allowed to process. Keep the source outside the repository and choose a
separate writable work directory for generated files. The generic workflow starts with:

```text
path: video/input.mkv
workspace: work
```

Replace these values in `Restoration Load Media` with paths appropriate to your local setup. The
path is the input seen by the ComfyUI process; the workspace is where manifests, samples, review
assets, and outputs are written. Never point an output destination at the source file.

## 3. Load and run the review workflow

1. In ComfyUI Desktop, open `examples/workflows/generic_restoration_review.json` using the workflow
   open/import control.
2. In `Restoration Load Media`, set the input path and workspace.
3. Leave `Plan Representative Samples` at its default seed, or set a duration and seed suitable
   for your test clip.
4. Keep `Video Baseline Restore` set to `target_aspect: preserve` for the first run. The node
   exposes `4:3`, `16:9`, and `1:1` as explicit crop alternatives for later review.
5. Queue the workflow. The graph should probe the source, create a deterministic sample plan, and
   write the requested conservative video candidate under the workspace.

Review the generated sample media and manifests before scaling up. Check dimensions, cadence,
audio sync, combing/interlacing behavior, clicks/hiss, speech identity, ambience, and any crop.
The workflow records a visual human review decision. This Desktop path does not require an
approval secret or signature.

The matching API-format file is
`examples/workflows/generic_restoration_review_api.json`. Use it only with an API client or the
ComfyUI queue API; the UI-format JSON is the file to open interactively in Desktop.

## 4. Record visual review and continue

After comparing the candidates, enter the decision JSON in `Human Approval Gate`, for example
`[{"sample":"A","decision":"approve"}]`. The node records the candidate hash and reviewer
decision for the local run. No approval secret or signature is needed in Desktop.

`Resumable Full Run` consumes that visual review record. This is intentionally a local usability
milestone, not a production authorization boundary. Secure signed approvals remain a stretch goal
for agent/MCP automation.

For the first Desktop test, stop after sample review unless you explicitly want to exercise the
local reviewed full-run path. Do not publish a Registry package until the sample results and the
Desktop behavior have been reviewed by a human.

## Troubleshooting

- **Nodes do not appear:** confirm the repository is directly under `custom_nodes/`, restart
  Desktop, and inspect the ComfyUI startup log for an import error.
- **FFmpeg errors:** verify that `ffmpeg` and `ffprobe` are available to the ComfyUI process, not
  only to an unrelated terminal shell.
- **Path or collision errors:** use a writable workspace outside the source location and ensure
  the destination does not overwrite the input.
- **The full workflow stops at review:** enter a non-empty visual decision JSON in `Human Approval
  Gate`; no host secret or signature is required for Desktop.
- **Workflow opens but does not queue:** use the review workflow’s terminal planning/output node,
  or update from the repository version that includes the workflow terminal-node fix.

Record the ComfyUI Desktop version, node commit, FFmpeg version, input probe, and observed errors
when reporting a test result. Do not attach source media or private absolute paths to a public
issue.
