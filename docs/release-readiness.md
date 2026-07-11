# Release-readiness checklist

This checkout is prepared for review but is not a release claim. Before publication:

- replace the placeholder repository URL in `CITATION.cff`;
- run `mise run check`, `mise run test-workflows`, `mise run test-e2e-small`, and `mise run audit-public`;
- install into a pinned ComfyUI checkout and execute both API and UI workflows;
- record real adapter versions/model hashes and licenses in `docs/upstream-evaluation.md`;
- run the Garden sample gate only with the user-owned capture available and retain outputs outside Git;
- complete the public fixture rights review and anonymous clone/install test;
- obtain explicit confirmation immediately before GitHub or Registry publication.

No source media, model weights, personal paths, or generated review assets belong in this repository.
