"""Thin ComfyUI node adapters; media policy remains in :mod:`comfyui_restoration.core`."""

from pathlib import Path
from typing import Any

from ..core import MediaSource, SamplePlan
from ..execution import Approval, ResumableRun, candidate_hash
from ..media import extract_audio, ingest


class RestorationLoadMedia:
    CATEGORY = "Restoration/01 Ingest"
    RETURN_TYPES = ("RESTORATION_SOURCE",)
    FUNCTION = "load"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"path": ("STRING", {"default": "video/input.mkv"}), "workspace": ("STRING", {"default": "work"})}}

    def load(self, path: str, workspace: str):
        root = Path(workspace).expanduser()
        return (ingest(Path(path), root),)


class AnalyzeSource:
    CATEGORY = "Restoration/01 Ingest"
    RETURN_TYPES = ("RESTORATION_ANALYSIS",)
    FUNCTION = "analyze"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"source": ("RESTORATION_SOURCE",)}}

    def analyze(self, source: MediaSource):
        streams = source.probe.get("streams", [])
        video = next((item for item in streams if item.get("codec_type") == "video"), {})
        audio = next((item for item in streams if item.get("codec_type") == "audio"), {})
        return ({"video": video, "audio": audio, "interlaced_risk": video.get("field_order") not in (None, "progressive", "unknown")},)


class ExtractLosslessAudio:
    CATEGORY = "Restoration/02 Audio"
    RETURN_TYPES = ("STRING",)
    FUNCTION = "extract"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"source": ("RESTORATION_SOURCE",), "workspace": ("STRING", {"default": "work"}), "output": ("STRING", {"default": "runs/audio-src.wav"})}}

    def extract(self, source: MediaSource, workspace: str, output: str):
        root = Path(workspace).expanduser()
        args = extract_audio(source, root, Path(output))
        return (" ".join(args),)


class PlanRepresentativeSamples:
    CATEGORY = "Restoration/02 Planning"
    RETURN_TYPES = ("RESTORATION_SAMPLE_PLAN",)
    FUNCTION = "plan"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"duration_seconds": ("FLOAT", {"default": 60.0, "min": 1.0}), "seed": ("INT", {"default": 0})}}

    def plan(self, duration_seconds: float, seed: int):
        points = [0.01, 0.5, 0.9]
        samples = tuple({"start": max(0.0, duration_seconds * p), "duration": min(60.0, duration_seconds)} for p in points)
        return (SamplePlan(samples=samples, seed=seed),)


class RestorationPassThrough:
    """Explicit bypass used for optional branches and future adapters."""
    CATEGORY = "Restoration/Branches"
    RETURN_TYPES = ("RESTORATION_ARTIFACT",)
    FUNCTION = "run"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"artifact": ("RESTORATION_ARTIFACT",)}}

    def run(self, artifact: Any):
        return (artifact,)


class HumanApprovalGate:
    CATEGORY = "Restoration/06 Review"
    RETURN_TYPES = ("RESTORATION_APPROVAL",)
    FUNCTION = "approve"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"parameters_json": ("STRING", {"default": "{}"}), "reviewer": ("STRING", {"default": "human"}), "decision_json": ("STRING", {"default": "[]"})}}

    def approve(self, parameters_json: str, reviewer: str, decision_json: str):
        import json
        parameters = json.loads(parameters_json)
        decisions = tuple(json.loads(decision_json))
        approval = Approval(candidate_hash(parameters), reviewer, decisions)
        approval.validate()
        return (approval,)


class ResumableFullRun:
    CATEGORY = "Restoration/07 Execution"
    RETURN_TYPES = ("RESTORATION_RUN",)
    FUNCTION = "start"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"workspace": ("STRING", {"default": "work"}), "run_id": ("STRING", {"default": "restoration-1"}), "parameters_json": ("STRING", {"default": "{}"}), "approval": ("RESTORATION_APPROVAL",), "chunks_json": ("STRING", {"default": "[\"sample-A\"]"})}}

    def start(self, workspace: str, run_id: str, parameters_json: str, approval: Approval, chunks_json: str):
        import json
        parameters = json.loads(parameters_json)
        run = ResumableRun(Path(workspace), run_id, parameters)
        state = run.execute(json.loads(chunks_json), lambda chunk: str(Path("runs") / run_id / f"{chunk}.done"), approval)
        return (state,)


_CAPABILITIES = (
    "DetectAudioDefects", "RepairAudioDefects",
    "DeepFilterNetAudio", "VoiceFixerAudio", "ResembleEnhanceAudio", "DemucsSeparateRecombine",
    "AudioSegmentRouter", "AudioEQLoudnessGuard", "VideoBaselineRestore", "VideoModelAdapter",
    "VideoChunkPlannerStitcher", "CompareCandidates", "HumanApprovalGate", "ResumableFullRun",
    "PreservationAwareRemux", "ValidateRestoration", "ExportReviewReport",
)


def _make_stub(name: str):
    return type(name, (RestorationPassThrough,), {"CATEGORY": "Restoration/" + name})


NODE_CLASS_MAPPINGS = {"RestorationLoadMedia": RestorationLoadMedia, "AnalyzeSource": AnalyzeSource, "ExtractLosslessAudio": ExtractLosslessAudio, "PlanRepresentativeSamples": PlanRepresentativeSamples, "HumanApprovalGate": HumanApprovalGate, "ResumableFullRun": ResumableFullRun}
NODE_CLASS_MAPPINGS.update({name: _make_stub(name) for name in _CAPABILITIES})
NODE_DISPLAY_NAME_MAPPINGS = {key: "Restoration " + key.removeprefix("Restoration").replace("Audio", " Audio") for key in NODE_CLASS_MAPPINGS}
