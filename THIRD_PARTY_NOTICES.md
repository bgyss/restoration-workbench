# Third-party notices

This repository distributes the workbench code under the MIT license in `LICENSE`. It does not
bundle third-party model weights, third-party model source, media, or ComfyUI itself.

## Required external tools

- FFmpeg/FFprobe, SoX, mkvtoolnix, and mediainfo are invoked as user-provided system tools. Their
  installed versions and corresponding distribution notices remain the operator's responsibility.
- ComfyUI is an optional host and is not included in this repository.

## Optional adapters

The following are replaceable subprocess boundaries, not bundled dependencies. Before installing
or redistributing one, record the exact repository commit, model-weight terms, transitive licenses,
and runner version in `docs/upstream-evaluation.md`:

| Adapter | Role | Notice boundary |
| --- | --- | --- |
| DeepFilterNet | Speech denoise | User-installed runner and weights |
| VoiceFixer | Experimental speech reconstruction | User-installed runner and weights; 44.1/48 kHz boundary |
| Resemble Enhance | Experimental speech denoise/enhancement | User-installed runner and weights |
| Demucs | Optional stem routing | MIT upstream; maintenance and model terms require review |
| Essentia | Optional click/discontinuity detection | AGPL-3.0; not bundled or linked |
| BasicVSR++ / RVRT | Experimental temporal video | User-installed code/weights; repository and weight terms require review |

No optional component may be enabled in a public release merely because it appears in this list.
The release checklist must be rerun after each adapter or model change.
