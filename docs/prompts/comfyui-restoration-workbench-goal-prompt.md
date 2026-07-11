# Goal Prompt: ComfyUI Audio/Video Restoration Workbench

## Mission

Build and publish an open-source, local-first ComfyUI restoration workbench for long-form
digitized analog video. The workbench must combine robust audio repair, conservative and
experimental video enhancement, reproducible quality-control evidence, and safe FFmpeg remuxing
in one inspectable node graph. It must ship custom ComfyUI nodes, a documented sample workflow,
tests, and an agent-facing automation surface suitable for later operation through a ComfyUI MCP
server.

Use the existing conservative pipeline in `docs/prompts/restoration-goal-prompt.md` as the
behavioral and safety baseline. This is a new, more ambitious track, not permission to weaken the
existing source-preservation, sample-review, sync, chapter, aspect-ratio, or full-decode gates.
Where generative restoration conflicts with fidelity, preserve both choices as explicit graph
branches and make the conservative result the default.

The first integration target is the ignored local capture at
`video/The Garden (Wiseman, 2005).mkv`. The repository and example workflow must remain useful
when a different video is supplied, and no source or restored copyrighted media may be committed
or published.

## Product principles

1. **Repair before reconstruction.** Prefer deterministic declicking, denoising, deblocking, and
   color correction before using a model that invents content.
2. **Models are optional branches, not a mandatory ladder.** Do not blindly run DeepFilterNet,
   VoiceFixer, and Resemble Enhance in series. Benchmark useful individual and combined branches;
   make every stage bypassable.
3. **Preserve identity and evidence.** Speech enhancement must not change the speaker, words,
   timing, room tone, or emotional delivery. Video enhancement must not change faces, objects,
   text, actions, shot boundaries, or chronology.
4. **Sample first, then scale.** Default to short representative samples and require human review
   before any full-length or generative run.
5. **Long media is file-backed.** Do not keep a feature-length video or WAV as one in-memory
   ComfyUI tensor. Pass typed artifact references plus manifests between nodes and stream or chunk
   the actual media.
6. **Resume rather than repeat.** Every expensive node must support deterministic cache keys,
   persisted outputs, progress reporting, cancellation, and restart after interruption.
7. **The graph explains itself.** Record commands, versions, model identifiers and hashes,
   parameters, timings, metrics, warnings, and parent artifacts in a machine-readable run manifest.
8. **Local-first and replaceable.** Core operation must not require a paid service. Keep model and
   execution adapters narrow enough that maintained alternatives can replace abandoned upstreams.
9. **The agent proposes; policy gates dispose.** MCP automation may analyze, construct sample runs,
   and compare candidates, but may not overwrite inputs, approve subjective QC, publish media, or
   start an unapproved full run.

## Known first-source facts

For the local Garden capture, inherit the verified facts from the existing goal prompt:

- Matroska container; H.264 video at 720x544, 4:3 DAR, 25 fps, progressive.
- AAC LC stereo at 48 kHz with a -21 ms audio delay.
- Approximately 3h18m duration and 27 chapters.
- Worse hiss and clicks near the beginning; meaningful dialogue and ambient/location sound.

Do not hard-code these facts as universal assumptions. A replacement input must be probed and its
own restoration plan derived. In particular, do not deinterlace the Garden capture, but detect and
properly handle genuinely interlaced material in other inputs.

## Initial technical hypothesis, to be tested rather than assumed

The proposed high-level graph is:

```text
media input
  -> probe + immutable ingest manifest
  -> representative sample planner
  -> audio extraction as lossless 48 kHz PCM
  -> audio analysis + selectable restoration candidates
  -> video analysis + selectable restoration candidates
  -> synchronized QC and comparison bundle
  -> human approval gate
  -> resumable full execution
  -> final EQ/loudness guardrail
  -> preservation-aware FFmpeg remux
  -> final validation and report
```

Candidate audio stages include:

```text
48 kHz PCM
  -> deterministic click detection and repair
  -> one or more denoise/enhancement candidates:
       A. conservative DSP baseline
       B. DeepFilterNet
       C. VoiceFixer on speech regions
       D. Resemble Enhance denoise-only or enhancement on speech regions
       E. explicitly tested combinations, only when they beat individual stages
  -> optional Demucs routing for demonstrably useful stem-aware processing
  -> restrained EQ
  -> loudness and true-peak guardrails
```

The implementation must test whether click repair works better before or after denoising. Avoid a
fixed order until evidence from representative samples supports it. Automatic click *detection*
alone is not restoration: the graph must expose detections for review and implement a repair
strategy such as short-gap interpolation, model-based/local spectral repair, or FFmpeg/SoX
declicking, with unchanged audio available as a bypass.

## Upstream reconnaissance and licensing gate

Before writing adapters, create `docs/upstream-evaluation.md` and verify, as of implementation
time, each candidate's:

- canonical repository and release or commit used;
- code, model-weight, and transitive dependency licenses;
- supported platforms, Python/PyTorch/CUDA versions, sample rates, channel handling, and memory;
- CLI and library interfaces, determinism, chunking behavior, maintenance status, and known limits;
- whether redistribution of weights is allowed, or installation must download them separately;
- whether the dependency can coexist in one environment or needs a subprocess/container adapter.

At minimum evaluate:

- FFmpeg and FFprobe for decode, analysis, deterministic filters, encode, and remux.
- DeepFilterNet (`Rikorose/DeepFilterNet`) for speech denoising.
- VoiceFixer (`haoheliu/voicefixer`) for speech restoration and bandwidth reconstruction.
- Resemble Enhance (`resemble-ai/resemble-enhance`) for speech denoising and enhancement.
- Essentia `ClickDetector` and `DiscontinuityDetector` for impulsive-defect locations.
- Demucs (`adefossez/demucs`) for optional source separation.
- ComfyUI, its current custom-node API, API-format workflows, workflow templates, and Registry
  publication requirements.
- ComfyUI-VideoHelperSuite or a maintained alternative for video I/O, while retaining custom
  preservation-aware ingest/remux nodes where generic video-combine nodes lose metadata.
- At least two non-generative and two temporally aware/generative video restoration candidates.

Important known risks to confirm:

- Essentia is AGPL-3.0; determine whether importing/linking it is compatible with the chosen
  repository license and distribution model. If not, isolate it behind an optional executable
  boundary or implement/test a permissively licensed detector.
- Demucs is MIT-licensed but its maintainer states that active feature development has stopped.
  Treat it as an optional adapter, not a foundational dependency.
- VoiceFixer and Resemble Enhance operate around 44.1 kHz internally/training-wise. Make all
  resampling boundaries explicit, use high-quality resampling, and verify sample count and timing
  after returning to the 48 kHz master timeline.
- Speech reconstruction models may behave like vocoders and can hallucinate bandwidth or alter
  voice identity. Label their output `experimental_reconstruction`, never `lossless repair`.
- The referenced public Comfy workflow is an LTX video-to-video restoration example that splits
  video into frames and recombines them; it does not by itself guarantee original audio, chapters,
  metadata, cadence, temporal truth, or feature-length scalability.

Do not copy third-party implementation code or workflow JSON without license review and proper
attribution. Pin tested versions or commits, but provide a documented upgrade path.

## Target repository architecture

Refactor or extend this repository into an installable ComfyUI custom-node package. Use the final
package name chosen during implementation consistently; the illustrative layout is:

```text
comfyui_restoration/
  __init__.py
  nodes/
    ingest.py
    sampling.py
    audio_analysis.py
    audio_restore.py
    video_analysis.py
    video_restore.py
    quality_control.py
    execution.py
    remux.py
  adapters/
    ffmpeg.py
    deepfilternet.py
    voicefixer.py
    resemble_enhance.py
    essentia.py
    demucs.py
  manifests/
  policies/
examples/
  workflows/
  manifests/
scripts/
tests/
docs/
```

Keep orchestration and media-domain logic testable without launching ComfyUI. ComfyUI node classes
should be thin adapters over typed Python services. Invoke external media tools with explicit
argument arrays, never an interpolated shell command. Do not accept arbitrary command fragments
from a workflow or MCP client.

### Artifact model

Define versioned, serializable artifact types such as:

- `MediaSource`: immutable path/reference, file identity, hash policy, probe data, stream selection.
- `SamplePlan`: timestamps or frame ranges, reasons, coverage, and deterministic seed.
- `AudioArtifact`: path, format, sample rate, channels, sample count, timeline offset, parents.
- `VideoArtifact`: path or frame sequence, dimensions, SAR/DAR, cadence, color metadata, parents.
- `RestorationCandidate`: branch name, parameters, model identities, output, metrics, warnings.
- `ReviewBundle`: synchronized before/after assets, plots, detections, metrics, and approval state.
- `RunManifest`: graph/workflow hash, environment, commands, events, timing, status, and outputs.

Use JSON Schema or an equivalent explicit schema. Reject stale, malformed, out-of-workspace, or
type-incompatible artifacts with useful errors. Store file paths in manifests as paths relative to
the run directory wherever possible; never publish personal absolute paths.

## Required ComfyUI nodes

Names may improve during implementation, but the public capability set must include:

1. **Restoration Load Media** — safe file selection, stream selection, FFprobe, immutable source
   identity, metadata/chapters/time-base capture, and rejection of output/source collisions.
2. **Analyze Source** — detects cadence/interlacing risk, black bars/aspect/color metadata, clipping,
   loudness, noise profile, channel correlation, speech/music/activity regions, and likely clicks.
3. **Plan Representative Samples** — combines chapter boundaries, early/middle/late coverage,
   defect severity, speech, ambience/music, silence, motion, faces, and scene cuts. Allow manual
   additions. For Garden, include the established early, middle, and late samples.
4. **Extract Lossless Audio** — writes PCM WAV at the declared master rate (48 kHz default), keeps
   the original timeline offset in metadata, and records exact extraction commands.
5. **Detect Audio Defects** — emits timestamped click/pop/discontinuity candidates with confidence,
   channel, duration, plots, and machine-readable JSON. Support Essentia when license-compatible
   and at least one fallback.
6. **Repair Audio Defects** — offers conservative repair algorithms and a bypass; produces repair
   masks and zoomed before/after review assets.
7. **DeepFilterNet Audio** — configurable attenuation, chunk overlap, device, and bypass.
8. **VoiceFixer Audio** — mode/device/chunk controls, explicit resampling, speech-region routing,
   and `experimental_reconstruction` labeling.
9. **Resemble Enhance Audio** — separate denoise-only and enhancement modes, solver/temperature or
   current equivalent controls, explicit resampling, speech-region routing, and experimental label.
10. **Demucs Separate/Recombine** — optional, model/stem/device controls, mixture-consistency and
    level checks, and an unchanged bypass. Never discard ambience by default.
11. **Audio Segment Router** — applies speech-only processing using padded regions and equal-power
    crossfades while leaving ambience/music-only regions on a conservative branch. Preserve stereo
    image unless a user explicitly approves a mono speech treatment.
12. **Audio EQ and Loudness Guard** — restrained, reviewable EQ; default loudness match within
    +/-1 LU of source; configurable true-peak ceiling; no automatic "broadcast sound" preset.
13. **Video Baseline Restore** — deterministic deblock/denoise/chroma cleanup/color-level branch.
    Properly handles real interlacing but refuses accidental deinterlacing or cadence conversion.
14. **Video Model Adapter** — a uniform interface for experimental restoration/upscale/video-to-
    video backends. Expose model hash, tiling, overlap, temporal window, seed, strength, scale, and
    device/offload controls. Generative strength defaults low.
15. **Video Chunk Planner/Stitcher** — scene-aware, temporally overlapped processing with explicit
    seam and flicker checks. Preserve frame count and timestamps unless an approved branch declares
    a cadence change.
16. **Compare Candidates** — creates synchronized A/B/X audio clips, waveform/spectrogram/loudness
    views, side-by-side video, difference views, contact sheets, metric tables, and artifact flags.
17. **Human Approval Gate** — blocks full execution until all required sample decisions are stored
    in an approval record tied to exact candidate hashes. Graph execution alone cannot self-approve.
18. **Resumable Full Run** — chunk queue, bounded resource usage, progress, cancellation, retry,
    cache/resume, free-space estimate, and projected completion time.
19. **Preservation-Aware Remux** — FFmpeg/mkvtoolnix-backed remux that preserves approved streams,
    chapters, language/disposition tags, attachments as policy allows, SAR/DAR, frame rate/time
    bases, color tags, and source A/V offset. Support FLAC archival audio and a documented delivery
    codec.
20. **Validate Restoration** — duration/sample/frame counts, sync drift, black/silent output,
    clipping, decode errors, metadata preservation, frozen frames, temporal seams, and full report.
21. **Export Review/Report** — redacted Markdown plus JSON report with complete reproducibility data.

Avoid one opaque "restore everything" node. A convenience group or subgraph is welcome, but the
individual decisions must remain inspectable and replaceable.

## Audio experiment design

### Candidate matrix

On every representative sample, render at least:

- untouched PCM baseline;
- deterministic declick/dehiss baseline;
- DeepFilterNet alone;
- click repair plus DeepFilterNet in both plausible orders if click behavior differs;
- VoiceFixer alone on routed speech regions;
- Resemble Enhance denoise-only on routed speech regions;
- Resemble Enhance full enhancement on routed speech regions;
- the best evidence-supported two-stage combination, if any;
- a Demucs-assisted branch only for samples containing overlapping speech/music or a demonstrated
  separation use case.

Prune combinations after the sample phase; do not multiply full-run compute without evidence.
Persist every evaluated parameter set and rejection reason.

### Chunking and timeline invariants

- Determine chunk size from model receptive field, available memory, and measured seam behavior.
- Use padding/overlap and equal-power crossfades. Compare seam regions against non-chunked short
  references.
- Track exact sample counts using integer sample indices, not accumulated floating-point seconds.
- After any 44.1/48 kHz round trip, match the master sample count or document and compensate a
  measured fixed latency. Never stretch audio merely to hide a bug.
- Preserve original channel count and layout by default. If a model is mono-only, define a tested
  downmix/upmix or mid/side strategy and measure image collapse.
- Keep processing headroom in float WAV; dither once, only if reducing bit depth.

### Audio evaluation

Use metrics as guardrails, not as automatic truth. Include:

- integrated/short-term loudness, loudness range, true peak, clipping count, DC offset, and noise
  floor estimates;
- click detector precision/recall on a small human-labeled Garden set and synthetic known-location
  click fixtures;
- speech intelligibility/quality metrics when their licenses and assumptions fit, clearly labeled;
- residual-to-source plots, stereo correlation, and spectral balance;
- transcript consistency or ASR word-change alarms as a hallucination warning, not a quality score;
- randomized, level-matched A/B/X listening for speech identity, intelligibility, clicks, hiss,
  ambience, musical artifacts, pumping, metallic voice, and invented consonants.

A neural candidate fails if it changes words or identity, removes meaningful ambience, produces
unstable tone across chunk boundaries, or merely sounds brighter while scoring worse in blind
review.

## Video experiment design

Maintain two visibly separate lanes:

### Faithful lane (default)

- Analyze before filtering; detect true field structure per source.
- For Garden, preserve 720x544, 4:3, 25 fps progressive output unless a separately reviewed
  delivery derivative is requested.
- Benchmark conservative FFmpeg/VapourSynth or maintained equivalents for light deblocking,
  temporal/chroma noise reduction, ringing control, legal/full-range correction, and restrained
  color balance.
- No sharpening, frame interpolation, face restoration, or upscaling by default.

### Experimental reconstruction lane (opt-in)

- Evaluate current temporally aware video restoration or video-to-video candidates, including the
  referenced LTX-style workflow and maintained non-generative neural restoration/upscale models.
- Process scene-aware clips with temporal overlap. Use fixed seeds where supported.
- Make scale independent from restoration: allow restore at native size, optional upscale, and
  upscale-then-downsample experiments.
- Preserve an archival faithful master even if an enhanced delivery derivative is selected.
- Label generative outputs and embed/report provenance. Never present generated detail as recovered
  historical fact.

### Video evaluation

For all samples, inspect and report:

- blocking/ringing/noise reduction versus texture retention;
- faces, hands, signs/text, thin lines, foliage/fabric, fast motion, fades, and scene cuts;
- temporal flicker, crawling detail, ghosting, duplicated/dropped frames, and chunk seams;
- frame count, cadence, SAR/DAR, color range/primaries/transfer/matrix, and black-bar policy;
- SSIM/VMAF or suitable full-reference guardrails, plus no-reference metrics only as secondary
  evidence;
- optical-flow/temporal-difference stability and identity/text alarms;
- randomized human comparisons against source and the faithful lane.

Any result that invents a face, alters text/action, breaks temporal continuity, or changes the
documentary record fails regardless of aesthetic appeal.

## Sample workflow requirements

Ship both ComfyUI UI-format and API-format JSON if current ComfyUI tooling requires both:

- `examples/workflows/garden_restoration_review.json`: configured for a user-supplied local file
  named `The Garden (Wiseman, 2005).mkv`, but containing no bundled media or personal absolute path.
- `examples/workflows/generic_restoration_review.json`: same graph with a neutral replaceable input.
- `examples/workflows/generic_restoration_full.json`: consumes a signed/recorded approval artifact
  from the review workflow and performs the resumable full run.

Expose the input path, stream choices, sample plan, restoration presets, devices, chunk sizes,
output directory, and delivery profile as obvious graph inputs. Add Markdown notes that explain
the faithful/experimental split, costs, expected VRAM, model downloads, licensing, and approval
gate. Package workflows using ComfyUI's current `example_workflows` template mechanism where
appropriate.

The workflow must not rely on node IDs as a public automation API. Define stable logical parameter
names and a small manifest-driven command/API layer that maps those names to the current workflow.

## Testing on local and public material

### Garden acceptance corpus

Use the existing local video without committing it. Build a defect annotation set and sample suite
covering:

- the noisy first chapter;
- clean and difficult dialogue;
- ambience and any music;
- silence/low-level room tone;
- representative clicks/pops;
- early, middle, and late runtime for sync drift;
- low/high motion, faces, fine texture, text, and scene transitions.

Retain the existing approximate early/middle/late 60-second samples for regression continuity, but
allow the analyzer to add shorter high-information clips.

### Public and synthetic corpus

Select at least three legally usable external sources with different failure modes, for example:

- public-domain or clearly permissive analog/VHS footage from an authoritative archive;
- a genuinely interlaced capture to exercise field handling;
- a source with music plus speech to evaluate routing and Demucs;
- synthetic degradations created from clean, redistributable reference media for objective tests.

Before downloading or publishing any clip, record its source URL, rights statement/license,
checksum, and permitted redistribution. Prefer scripts that fetch pinned public fixtures over
committing large binaries. If redistribution is unclear, store only a manifest and local fetch
instructions. Never use "found online" as a license.

Synthetic fixtures should include known click positions, hiss, hum, clipping, bandwidth limits,
dropouts, compression artifacts, chroma noise, blocking, interlace, and cadence changes, without
claiming that synthetic defects perfectly model VHS.

## Reproducible environments and resource profiles

- Preserve the current Nix/mise/Python check path for CPU-safe orchestration and tests.
- Document the primary GPU path and at least one CPU/fallback path. Do not pretend heavyweight
  neural restoration is practical on CPU.
- Because model stacks may have conflicting PyTorch/CUDA requirements, prefer per-adapter
  subprocess environments or containers over a fragile universal environment. Keep local file and
  GPU access narrowly scoped.
- Provide `doctor` output that reports FFmpeg features, ComfyUI/API versions, node versions, model
  availability/hashes, GPU/VRAM, disk space, and incompatible optional branches.
- Provide resource presets such as CPU/conservative, 8-12 GB VRAM, 16-24 GB VRAM, and high-memory,
  based on measured runs rather than promises.
- Check free space before extraction/full execution and estimate peak intermediate storage.

## ComfyUI MCP and agent automation

Implement the core as API-first ComfyUI workflows before selecting an MCP bridge. Evaluate current
local ComfyUI MCP projects and any official/cloud option for maintenance, license, tool coverage,
authentication, and security. Do not couple the custom nodes to one MCP implementation.

Define a minimal agent-facing tool contract, directly or through a compatible MCP server:

- `inspect_restoration_capabilities`
- `probe_media`
- `plan_samples`
- `run_sample_candidates`
- `get_run_status`
- `cancel_run`
- `list_candidates`
- `build_review_bundle`
- `record_human_approval`
- `run_approved_full_restoration`
- `validate_output`
- `export_restoration_report`

Agent-accessible operations must enforce:

- allowlisted input/output roots with symlink/path-traversal checks;
- immutable sources and collision refusal;
- bounded parameters, file sizes, concurrency, GPU use, time, and storage;
- no arbitrary shell, Python, node installation, model download, network fetch, or workflow-supplied
  executable path;
- explicit approval for model/node installation, external downloads, full runs, and publication;
- structured progress/errors and idempotency keys;
- separation between "candidate recommended" and "human approved";
- redaction of local paths, tokens, prompts, and private media metadata from logs/public reports.

Create MCP contract tests using a fake client and tiny synthetic fixtures. The agent should be able
to reproduce a sample run from a manifest, but it must be technically unable to forge the human
approval artifact under the same authority used for analysis.

## Public-repository readiness and publication

Prepare this checkout as the canonical public repository for the custom nodes and workflows.
Before publishing:

1. Choose a clear package/repository name and a permissive project license compatible with all
   bundled code. Optional AGPL components must remain clearly separated and documented.
2. Add a polished README with problem statement, architecture, quick start, screenshots using safe
   fixtures, node catalog, faithful-versus-generative warning, hardware matrix, and limitations.
3. Add `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, security policy, issue templates, citation
   and third-party notices as appropriate.
4. Add installation compatible with current ComfyUI custom-node conventions and Registry metadata;
   provide pinned reproducible development setup.
5. Add CI for formatting, lint, types if adopted, unit/integration tests, workflow/schema validation,
   license/path/privacy checks, and a CPU-only tiny end-to-end FFmpeg test. GPU tests may be manual
   or scheduled but must have recorded procedures.
6. Scan the complete Git history and working tree for source media, generated media, credentials,
   private metadata, absolute paths, and oversized blobs. Ignore rules alone are insufficient.
7. Confirm every screenshot, sample, fixture, model, weight, and copied workflow is publishable and
   attributed.
8. Create the public GitHub repository under the authenticated user's chosen account, set topics
   and description, push the reviewed default branch, and verify the anonymous clone/install/test
   path. Do not force-push or rewrite an existing remote without explicit human approval.
9. If ComfyUI Registry publication is desired and credentials are available, validate the package
   first and request a final human confirmation immediately before registry publication.

The example Garden workflow may name the expected local input but must not contain the Garden
capture, extracted frames/audio, hashes that expose private provenance unnecessarily, or outputs.

## Implementation phases

### Phase 0 — Contract, audit, and baseline preservation

- Read the existing prompt, runner, tests, reports, and environment.
- Run the existing checks and a non-destructive baseline sample if practical.
- Record dirty-worktree state; preserve all unrelated user changes.
- Write upstream/license evaluation, architecture decision records, threat model, schemas, and an
  implementation/test plan.

### Phase 1 — Media core independent of ComfyUI

- Implement immutable ingest, manifests, safe process execution, sampling, file-backed artifacts,
  cache/resume, FFmpeg extraction/remux, validation, and synthetic fixtures.
- Unit-test command construction, schemas, paths, timeline math, collisions, cancellation, and
  failure recovery.

### Phase 2 — Audio workbench

- Implement analysis, defect detection/repair, model adapters, routing, chunking, EQ/loudness,
  comparisons, and evaluation.
- Benchmark the candidate matrix on Garden samples and synthetic/public fixtures.
- Select conservative defaults from evidence. Keep experimental reconstruction opt-in.

### Phase 3 — Video workbench

- Implement faithful video baseline, backend interface, chunking/stitching, comparisons, and
  temporal QC.
- Benchmark candidate video approaches on samples only. Document compute and failure modes.

### Phase 4 — ComfyUI package and workflows

- Add thin custom-node wrappers, categories, descriptions, validation, progress, cancellation, and
  template workflows.
- Test UI-format/API-format round trips and headless workflow execution against a pinned compatible
  ComfyUI version.

### Phase 5 — Human review and full Garden run

- Produce sample review bundles with randomized/level-matched comparisons.
- Pause for explicit human selection of audio and video candidates.
- Estimate time/storage, then run the approved resumable full workflow.
- Remux and perform end-to-end sync, metadata, decode, and subjective QC.

### Phase 6 — External validation

- Run the legally reviewed public/synthetic corpus.
- Fix source-specific assumptions exposed by interlaced, music-heavy, differently sized, or
  differently encoded inputs.
- Document which presets generalize and which require tuning.

### Phase 7 — MCP-ready automation

- Freeze stable logical workflow parameters and implement/test the agent tool contract.
- Demonstrate an agent planning and executing sample candidates, reporting results, and stopping at
  the human gate; then demonstrate resuming only after a valid approval record.

### Phase 8 — Public release

- Complete privacy/license/security audit and documentation.
- Publish GitHub repository, verify clean installation, tag an initial semantic release, and attach
  only safe small artifacts.
- Produce a release report listing known limitations and exact tested hardware/software.

Do not skip directly to a polished ComfyUI graph while the file-backed media core, timeline
invariants, license decisions, and tests remain undefined.

## Validation commands and evidence

Keep `mise run check` green. Add focused tasks as implementation evolves, for example:

```sh
mise run doctor
mise run check
mise run test-workflows
mise run test-e2e-small
mise run audit-public
```

The exact commands may differ, but equivalent checked-in entry points must exist. Tests must be
deterministic and media-free unless they use generated tiny fixtures or fetch explicitly licensed,
pinned test data. Mock neural adapters in normal CI; validate real models in opt-in integration
tests with model identifiers and hashes recorded.

For each real sample/full run, capture:

- source identity and probe manifest;
- sample plan and rationale;
- exact graph, API workflow, node/model/environment versions and hashes;
- command arguments and normalized relative artifact paths;
- candidate metrics, review assets, human decision, and rejected alternatives;
- wall time, peak VRAM/RAM/disk, chunk/retry events, and projected-versus-actual duration;
- output stream/metadata comparison, sync checks, and full decode result.

## Deliverables

1. Installable, documented ComfyUI custom-node package in this repository.
2. File-backed restoration core and versioned manifests/schemas.
3. Audio adapters for DeepFilterNet, VoiceFixer, Resemble Enhance, optional Essentia and Demucs,
   plus deterministic fallbacks.
4. Faithful and experimental video restoration adapters with temporal/chunk QC.
5. Garden and generic review/full workflow JSON files, valid in UI and API execution modes.
6. Automated unit, schema, security, workflow, and tiny end-to-end tests.
7. Public/synthetic benchmark manifests and a source-backed evaluation report.
8. Garden sample review bundle and, only after human approval, a local full restored output and
   restoration report.
9. MCP/agent tool contract, threat model, fake-client tests, and gated demonstration.
10. Public GitHub repository with clean anonymous installation and an initial tagged release.

## Definition of done

- A new user can install the package into a supported ComfyUI setup, load the generic workflow,
  swap in a legally held video, and complete the sample-review flow from the documentation.
- The local Garden workflow probes the actual file, preserves its 4:3 geometry, 25 fps cadence,
  chapters, and -21 ms audio offset, and produces an approved full result that passes decode and
  sync checks without publishing the media.
- Audio branches demonstrably reduce clicks/hiss or improve degraded speech while preserving words,
  speaker identity, ambience, stereo behavior, sample count, sync, and loudness guardrails.
- Video faithful output reduces diagnosed artifacts without accidental deinterlacing, waxiness,
  ghosting, cadence errors, or metadata loss; generative output is separate, labeled, and provenance
  recorded.
- Long runs are cancellable, restartable, bounded, and do not require keeping full media in memory.
- Replacing the input does not depend on Garden-specific constants; interlaced and music-heavy test
  sources exercise alternate paths.
- CI is green, public audit finds no private/source media or personal paths, third-party licensing is
  documented, and anonymous clone/install succeeds.
- An MCP-connected agent can inspect, plan, run samples, compare, and report, but cannot approve its
  own candidates, overwrite a source, escape allowed roots, or start an unapproved full run.

## Stop-and-ask conditions

Pause and request human direction when:

- licensing does not permit the proposed bundling, linking, model-weight use, or public release;
- source rights are unclear for any public fixture, screenshot, comparison, or downloadable output;
- the source is detected as interlaced or has a cadence/offset that the chosen path cannot preserve;
- all speech candidates alter words/identity or destroy meaningful ambience;
- a generative video candidate changes identity, text, actions, or temporal truth;
- sample reviewers cannot prefer a candidate under level-matched/blind conditions;
- a full run would exceed approved compute, storage, cost, or time limits;
- a requested action would overwrite/delete source media, expose private paths/data, install
  unreviewed executable code, download from an unapproved origin, or weaken the approval boundary;
- GitHub repository ownership/name is ambiguous, a remote already exists with unrelated history, or
  publication would require rewriting history;
- the Garden capture or any derived media is about to be committed, uploaded, or published.

## Starting references

- Existing contract: `docs/prompts/restoration-goal-prompt.md`
- ComfyUI video restoration example:
  <https://comfy.org/workflows/558cc012978d-558cc012978d/>
- Community discussion and cautions:
  <https://www.reddit.com/r/comfyui/comments/1nfzsnr/anyone_managed_functional_video_restore_of_old/>
- DeepFilterNet: <https://github.com/Rikorose/DeepFilterNet>
- Essentia: <https://github.com/MTG/essentia>
- Essentia ClickDetector:
  <https://essentia.upf.edu/reference/std_ClickDetector.html>
- Demucs: <https://github.com/adefossez/demucs>
- VoiceFixer: <https://github.com/haoheliu/voicefixer>
- Resemble Enhance: <https://github.com/resemble-ai/resemble-enhance>
- ComfyUI custom-node overview: <https://docs.comfy.org/custom-nodes/overview>
- ComfyUI workflow templates: <https://docs.comfy.org/custom-nodes/workflow_templates>
- ComfyUI workflow/API concepts: <https://docs.comfy.org/development/core-concepts/workflow>
- ComfyUI-VideoHelperSuite: <https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite>

Treat these as starting points, not frozen endorsements. Re-verify current documentation, releases,
security posture, maintenance, and licenses when implementation begins.
