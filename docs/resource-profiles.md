# Resource profiles

The base package is CPU-safe for probing, planning, detection, command generation, and manifest
work. Optional neural candidates are measured per adapter and are never silently substituted.

| Profile | Intended use | Default policy |
| --- | --- | --- |
| CPU/conservative | probe, samples, FFmpeg faithful lane | no neural reconstruction |
| 8–12 GB VRAM | short DeepFilterNet/video samples | one candidate at a time, chunked |
| 16–24 GB VRAM | larger sample matrix | bounded concurrency, fixed overlap |
| high-memory | approved full run | only after measured sample projection and free-space check |

The adapter boundary exists because model stacks can require incompatible Python/PyTorch/CUDA
versions. Install each optional runner separately, record its version and model hash, and preserve
the unchanged branch for comparison.
