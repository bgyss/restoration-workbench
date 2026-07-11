# Local sample review runbook

The local source capture is never copied into Git. Keep current sample evidence under an ignored
work directory, for example `work/local-review/`:

1. Review `review/sample-{A,B,C}-frame.png` for geometry, bars, motion, texture, faces, text, and
   scene boundaries.
2. Compare the source WAVs and `candidates/dsp/sample-*-audio.wav` for clicks, hiss, room tone,
   ambience, speech identity, stereo image, and pumping.
3. Compare the source frames/videos with the faithful candidate and inspect the SSIM logs as
   guardrails, not as an aesthetic score.
4. Record a human decision for every required sample and candidate. Keep rejected alternatives and
   reasons in the candidate manifest.
5. Record the visual decision in the Desktop gate or local service. No host secret or signature is
   required for the current milestone; secure attestation is a future stretch goal.
6. After review, use the resumable full workflow with a storage/time estimate. Preserve the
   faithful master even if an experimental derivative is selected.

The current candidate manifest remains `pending_human_review`; repository automation does not
authorize a full run automatically.

## Stretch goal: production approval workflow

The current local workflow uses visual review only. A future production deployment may add
identity-backed asymmetric attestation and a policy decision point (for example, OPA/Cedar plus an
in-toto/DSSE-style receipt), with expiry, revocation, key rotation, and reviewer authentication.
Secure approval is intentionally punted to a stretch goal.
