# Benchmarking contract

`examples/benchmarks/synthetic.json` is the redistributable baseline corpus. It contains no
external media and records the failure modes each fixture is intended to exercise. Generate a
fixture with `comfyui_restoration.benchmark.fixture_command`, then record the source identity,
candidate parameters/model hashes, commands, metrics, and review decision in the run manifest.

Synthetic signals validate timeline, clipping, click-location, channel, cadence, and resource
invariants; they do not establish that a model improves real footage. Any external source requires
separate rights and human-review records before derived media is retained or shared.

`plan_audio_candidates(["A", "B", "C"])` expands the required per-sample matrix, including the
untouched baseline, both click/DeepFilterNet orders, routed speech candidates, and a deferred
evidence-selected two-stage branch. Demucs is recorded as rejected unless a sample is explicitly
marked as having a demonstrated overlapping speech/music use case. Every branch carries its
parameters and rejection reason so pruning does not become an undocumented subjective choice.

The agent service persists returned sample results at `review/candidate-results.json`, keeping
candidate parameters and measured metrics available for later human review and approval.

The opt-in command `python scripts/benchmark_deepfilter.py INPUT.wav OUTPUT_DIR RECORD.json`
records an explicit `unavailable` result when DeepFilterNet is not installed. When available, it
runs only the fixed adapter command and records runner version, input/output hashes, and PCM
metrics; it never substitutes the DSP branch or silently downloads a model.

`examples/benchmarks/external-sources.json` records three Library of Congress public-domain
selection candidates with source and rights URLs, intended failure modes, and an explicit
not-fetched/null-checksum state. It is a fetch plan, not a claim that media has been downloaded or
validated. After an authorized fetch, replace `sha256: null` with the digest of the exact file and
record the selected download URL and probe in the run manifest. The repository never fetches these
sources during normal tests.

For an authorized local download, record evidence with:

```sh
python scripts/record_external_fixture.py /path/outside/repo/clip.mp4 work/external/clip.json \
  --source-id loc-memphis-belle \
  --source-url https://www.loc.gov/item/2023602007/ \
  --rights-url https://www.loc.gov/free-to-use/public-domain-films-from-the-national-film-registry/ \
  --license public-domain
```

The command never downloads or copies media. It refuses files inside the repository, hashes the
exact local file, probes it, and writes only a JSON evidence record.

## Video candidate lanes

The benchmark planner exposes four explicit candidates: the available FFmpeg faithful baseline,
an optional OpenCV multi-frame non-generative denoiser, and the opt-in BasicVSR++ and RVRT
temporally aware neural candidates. The latter three are catalog entries rather than bundled
implementations: installation, commit/model hashes, license terms, and hardware measurements must
be recorded before execution. All candidates retain the source-faithful branch, and every
temporally aware candidate requires seam, flicker, cadence, identity, and text review.

Interlaced inputs use the separate `VideoInterlaceHandler` node. It requires the detected field
order and an explicit `send_frame` or `send_field` mode; the faithful progressive baseline never
invokes it implicitly. Because `send_frame` changes cadence, that decision remains visible in the
graph and must be included in the approval and validation record.
