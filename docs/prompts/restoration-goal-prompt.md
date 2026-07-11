# Goal Prompt: VHS Capture Restoration Pipeline

## Objective

Restore the audio and video of a digitized VHS capture, producing a cleaned MKV that is noticeably more watchable than the source without introducing restoration artifacts (waxiness, smearing, over-suppressed ambience). Prioritize "cleaner and faithful" over "remastered." When in doubt, be conservative.

## Source file facts

Derive these facts from the user-supplied input with `ffprobe` and record them in the run manifest.
Do not hard-code a title, codec, duration, geometry, delay, chapter count, or noise profile from a
different capture. Preserve the measured audio offset, chapters, display geometry, cadence, and
color metadata for the selected input.

## Hard constraints

1. Never overwrite or modify the source file. All work happens on copies in a working directory.
2. Do NOT deinterlace. The source is progressive. Adding QTGMC or any deinterlacer is a defect, not an improvement. (Exception: if the combing check in Phase 1 finds real interlacing artifacts, stop and report before proceeding.)
3. Audio work happens on a lossless intermediate (PCM WAV extracted from the AAC), never lossy-to-lossy directly.
4. Final video encode: x264, CRF 18-20, preset slow or slower, keep 720x544, 4:3 DAR, 25 fps, 8-bit 4:2:0. No upscaling, no frame rate changes, no AI super-resolution in this pipeline.
5. Final audio encode: AAC at 192 kbps or higher (or FLAC if size is not a concern; prefer AAC 192k as default).
6. Final remux must preserve: chapter marks, the -21 ms audio delay, and correct 4:3 display aspect ratio.
7. Sample-first workflow (see Phase 2). Never run a filter chain across the full 3h18m file until it has passed review on samples.

## Phase 0: Environment setup

Install and verify, reporting versions:
- ffmpeg (with libx264)
- Audio: DeepFilterNet CLI (`deep-filter`) preferred for hiss; ffmpeg `adeclick`/`adeclip` for pops; sox as fallback
- Video (preferred path): VapourSynth + plugins: a deblocker (Deblock_QED or vs-deblock), SMDegrain or TemporalDegrain2 (MVTools-based), optionally a dehalo (FineDehalo or similar)
- Video (fallback path if VapourSynth setup fails or is impractical): ffmpeg-only chain using `pp7`/`deblock` + `hqdn3d` (or `atadenoise` on samples where speed allows)

If a preferred tool cannot be installed, fall back gracefully and note the substitution in the final report. Do not stall on environment issues for more than a reasonable effort; the fallback path is acceptable.

## Phase 1: Verification and baseline

1. Confirm stream properties match the facts above (`ffprobe`).
2. Combing sanity check: extract 10-15 single frames from moments of fast motion across the input and inspect for interlace combing. If combing IS found, STOP and report; the pipeline design changes.
3. Extract audio to `audio_src.wav` (pcm_s16le, 48 kHz, stereo).
4. Capture baseline metrics for later comparison: audio loudness stats (`ffmpeg -af astats,ebur128`), and 6 reference PNG frame grabs at fixed timestamps (one in chapter 1 where noise is worst, plus five spread across the runtime). Save all baselines to `baseline/`.

## Phase 2: Sample extraction (the test bed)

Extract three representative sample clips, 60 seconds each, video+audio:
- Sample A: early runtime or a high-defect region
- Sample B: middle runtime
- Sample C: late runtime

All filter tuning happens on these samples. A filter chain graduates to the full run only after passing Phase 3 and Phase 4 checks on ALL THREE samples.

## Phase 3: Audio restoration (tune on samples, then full run)

Pipeline order: declick first, then dehiss.

1. Pop/click removal: `ffmpeg -af adeclick` (default settings first; tighten only if pops survive). Verify pops are reduced by comparing before/after waveform peak counts around transients and by generating spectrograms (`ffmpeg -lavfi showspectrumpic`) for visual diffing.
2. Hiss removal: run DeepFilterNet on the declicked WAV. It is speech-tuned, so verify on all three samples that meaningful ambience, room tone, and environmental sound remain audible and natural. If it over-suppresses, retry with reduced attenuation or fall back to SoX `noisered` with a profile taken from a quiet passage, at conservative strength (0.15-0.25).
3. If defect severity varies across the input, a stronger setting for a short problem region and a lighter setting elsewhere is acceptable, but prefer one global setting for simplicity.
4. Loudness: do NOT loudness-normalize creatively. Match the original program loudness within +/- 1 LU (compare ebur128 integrated loudness before/after).
5. Full-run output: `audio_clean.wav`, then encode to AAC 192k as `audio_clean.m4a`.

## Phase 4: Video restoration (tune on samples, then full run)

Preferred VapourSynth chain, in order:
1. Source filter (LSMASHSource or ffms2)
2. Light deblock (Deblock_QED, conservative quant settings) to address H.264 blocking
3. Temporal denoise: SMDegrain with conservative settings (thSAD in the 150-250 range as a starting point, tr=2) OR TemporalDegrain2 at its lighter presets. Target: reduce grain/noise shimmer while preserving texture in faces, foliage, and fabric.
4. Optional: mild dehalo/dering ONLY if sample review shows visible edge haloing. Skip by default.
5. No sharpening.

Fallback ffmpeg-only chain: `-vf "pp7=qp=2:mode=medium,hqdn3d=3:2:6:4"` as the starting point, tuned on samples.

Sample review gate (all three samples, against source):
- Generate side-by-side comparison frames (source vs filtered) at 4+ timestamps per sample, saved as PNGs to `review/`.
- Automated sanity metrics: compute VMAF or SSIM of filtered-vs-source on each sample. These metrics reward similarity, so do not maximize them; use them as a guardrail. SSIM in roughly the 0.92-0.98 band suggests meaningful-but-not-destructive filtering; below ~0.90 flags over-filtering for human review.
- Failure signs to check for explicitly: waxy skin, loss of fine texture, temporal ghosting/trailing on motion, banding introduced in flat areas (if banding appears, add light grain via `grain` at output or dither properly).

Full-run encode settings: x264, CRF 19, preset slow, `--tune grain` considered but only if sample encodes show grain-retention benefit; otherwise default tune. Keep SAR/DAR so the file displays 4:3.

Given ~297k frames, log encode FPS on Sample A and report a projected full-run wall-clock time BEFORE starting the full run.

## Phase 5: Remux and final QC

1. Mux cleaned video + cleaned audio into `restored.mkv` with:
   - The measured source audio delay applied (verify with `mediainfo` on the output)
   - All source chapters copied from the input (extract with `mkvextract chapters` or ffmpeg, re-attach in mux)
2. Duration check: output duration must match source within 100 ms.
3. Sync spot-check: extract 5-second A/V clips at chapter 1, chapter 14, and chapter 27 from the output and confirm no audible/visible desync drift.
4. Full-file decode check on the output: `ffmpeg -v error -i output.mkv -f null -` must produce zero errors.
5. Produce final comparison assets in `review/final/`: before/after frame pairs at the 6 baseline timestamps, and before/after spectrograms of a chapter-1 audio segment.

## Deliverables

1. `restored.mkv`
2. `review/` directory: sample clips (before/after), comparison frames, spectrograms
3. `RESTORATION_REPORT.md` containing: exact tool versions, the final filter chains and settings used (full VapourSynth script and ffmpeg command lines, reproducible verbatim), all metric results (SSIM/VMAF per sample, loudness before/after), any fallbacks or deviations taken and why, and known remaining defects

## Definition of done

- All Phase 5 QC checks pass
- Audio: pops in chapter 1 substantially reduced, hiss floor clearly lower, dialogue intelligibility unchanged or improved, ambience preserved, loudness within +/- 1 LU of source
- Video: visible reduction of noise shimmer and blocking on the review frames, no waxiness/ghosting/banding introduced
- Chapters and -21 ms delay verified present in the output
- Report is complete enough that the entire pipeline can be re-run from it verbatim

## Stop-and-ask conditions

Pause and ask a human before proceeding if:
- Combing/interlacing is found in Phase 1
- No dehiss setting can preserve ambience acceptably on Sample A
- Projected full-run encode time exceeds 24 hours on available hardware
- Any step would require modifying or deleting the source file
