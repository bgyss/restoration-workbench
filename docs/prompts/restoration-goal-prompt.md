# Goal Prompt: VHS Capture Restoration Pipeline

## Objective

Restore the audio and video of a digitized VHS capture, producing a cleaned MKV that is noticeably more watchable than the source without introducing restoration artifacts (waxiness, smearing, over-suppressed ambience). Prioritize "cleaner and faithful" over "remastered." When in doubt, be conservative.

## Source file facts (verified, do not re-derive)

- File: `The Garden (Wiseman, 2005).mkv`
- Container: Matroska. Integrity verified: a full `ffmpeg -v error` decode pass produced no errors. Ignore the mediainfo header-size conformance warning; the stream is complete and decodable.
- Video: H.264 (x264 core 135, 2014 encode), 720x544, 4:3 DAR, 25.000 fps constant, progressive (`interlaced=0`), 8-bit 4:2:0, CRF 23. Duration 3h18m (~297,000 frames).
- Audio: AAC LC stereo, 48 kHz, lossy. Delay relative to video: -21 ms. This delay MUST be preserved in the final remux.
- Chapters: 27 chapter marks present. These MUST be carried into the final output.
- Noise profile (per human review): consistent analog tape hiss throughout, pops/clicks in audio, worse in roughly the first chapter. Video carries tape noise smeared through a generation of lossy H.264 compression: expect grain remnants plus blocking and ringing.

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
2. Combing sanity check: extract 10-15 single frames from moments of fast motion (sample across chapters) and inspect for interlace combing. Expected result: none. If combing IS found, STOP and report; the pipeline design changes.
3. Extract audio to `audio_src.wav` (pcm_s16le, 48 kHz, stereo).
4. Capture baseline metrics for later comparison: audio loudness stats (`ffmpeg -af astats,ebur128`), and 6 reference PNG frame grabs at fixed timestamps (one in chapter 1 where noise is worst, plus five spread across the runtime). Save all baselines to `baseline/`.

## Phase 2: Sample extraction (the test bed)

Extract three sample clips, 60 seconds each, video+audio:
- Sample A: from chapter 1 (worst noise region)
- Sample B: from mid-film (~1h39m)
- Sample C: from late film (~3h00m)

All filter tuning happens on these samples. A filter chain graduates to the full run only after passing Phase 3 and Phase 4 checks on ALL THREE samples.

## Phase 3: Audio restoration (tune on samples, then full run)

Pipeline order: declick first, then dehiss.

1. Pop/click removal: `ffmpeg -af adeclick` (default settings first; tighten only if pops survive). Verify pops are reduced by comparing before/after waveform peak counts around transients and by generating spectrograms (`ffmpeg -lavfi showspectrumpic`) for visual diffing.
2. Hiss removal: run DeepFilterNet on the declicked WAV. IMPORTANT check: DeepFilterNet is speech-tuned. This is a Wiseman documentary (vérité dialogue plus meaningful ambient/location sound). Verify on all three samples that ambience is not gutted. Acceptance heuristic: noise floor in silent passages should drop substantially, but room tone and environmental sound during dialogue must remain audible and natural. If DeepFilterNet over-suppresses, retry with reduced attenuation (its attenuation limit flag), or fall back to sox `noisered` with a hiss profile taken from a quiet passage in chapter 1, at conservative strength (0.15-0.25).
3. Because the first chapter is worse: it is acceptable to apply a stronger dehiss setting to the first ~7 minutes and a lighter one to the remainder, then crossfade-join. Only do this if a single global setting fails the sample review; prefer one global setting for simplicity.
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

1. Mux cleaned video + cleaned audio into `The Garden (Wiseman, 2005) [restored].mkv` with:
   - The -21 ms audio delay applied (verify with `mediainfo` on the output)
   - All 27 chapters copied from the source (extract with `mkvextract chapters` or ffmpeg, re-attach in mux)
2. Duration check: output duration must match source within 100 ms.
3. Sync spot-check: extract 5-second A/V clips at chapter 1, chapter 14, and chapter 27 from the output and confirm no audible/visible desync drift.
4. Full-file decode check on the output: `ffmpeg -v error -i output.mkv -f null -` must produce zero errors.
5. Produce final comparison assets in `review/final/`: before/after frame pairs at the 6 baseline timestamps, and before/after spectrograms of a chapter-1 audio segment.

## Deliverables

1. `The Garden (Wiseman, 2005) [restored].mkv`
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
