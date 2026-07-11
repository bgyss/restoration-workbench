# Release-readiness checklist

This checkout is prepared for review but is not a release claim. Before publication:

- replace the placeholder repository URL in `CITATION.cff`;
- verify the `bgyss/restoration-workbench` repository and `bgyss` PublisherId after authenticated creation;
- retain the short Registry node ID `restoration-workbench`; the Python import namespace remains `comfyui_restoration`;
- validate the Registry archive against `.comfyignore` before any publication;
- review the GitHub issue templates for privacy-safe reproduction guidance;
- run `mise run check`, `mise run test-workflows`, `mise run test-e2e-small`, and `mise run audit-public`;
- CI runs the public-history audit and CPU-only tiny FFmpeg E2E after installing FFmpeg on the runner;
- use `mise run check-lite` when pytest/model dependencies are not available; it does not replace the full test suite;
- provision pytest through all three supported paths: Nix (`python312Packages.pytest`), mise (`mise run install-test-tools`), and uv (`pytest>=8` in the dev group);
- install into a pinned ComfyUI checkout and execute both API and UI workflows;
- record real adapter versions/model hashes and licenses in `docs/upstream-evaluation.md`;
- review `THIRD_PARTY_NOTICES.md` and add/update notices for every bundled or optional component;
- run the Garden sample gate only with the user-owned capture available and retain outputs outside Git;
- complete the public fixture rights review and anonymous clone/install test;
- obtain explicit confirmation immediately before GitHub or Registry publication.

No source media, model weights, personal paths, or generated review assets belong in this repository.

The production-grade identity-backed approval/attestation workflow is a stretch goal. The current
local HMAC gate is retained for the sample-first milestone only.
