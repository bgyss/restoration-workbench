# Garden sample review runbook

The local Garden capture is never copied into Git. The current sample evidence lives under the
ignored `work/garden-probe/` directory:

1. Review `review/sample-{A,B,C}-frame.png` for geometry, bars, motion, texture, faces, text, and
   scene boundaries.
2. Compare the source WAVs and `candidates/dsp/sample-*-audio.wav` for clicks, hiss, room tone,
   ambience, speech identity, stereo image, and pumping.
3. Compare the source frames/videos with the faithful candidate and inspect the SSIM logs as
   guardrails, not as an aesthetic score.
4. Record a human decision for every required sample and candidate. Keep rejected alternatives and
   reasons in the candidate manifest.
5. Only a host-held `COMFYUI_RESTORATION_APPROVAL_SECRET` can validate the HMAC approval artifact.
   The agent and workflow cannot manufacture that signature.
   To promote an already recorded human decision, configure that secret in the host environment
   and run `python scripts/sign_approval.py work/garden-probe/approval-dsp-afftdn.json`. Never put
   the secret in Git, a workflow JSON, or a chat message.
6. After approval, use the resumable full workflow with a storage/time estimate. Preserve the
   faithful master even if an experimental derivative is selected.

The current candidate manifest remains `pending_human_review`; no full Garden run is authorized by
the repository automation.
