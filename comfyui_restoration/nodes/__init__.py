"""Thin ComfyUI node adapters; media policy remains in :mod:`comfyui_restoration.core`."""

from pathlib import Path
from typing import Any

from ..core import AudioArtifact, MediaSource, SamplePlan, VideoArtifact
from ..execution import Approval, ResumableRun, candidate_hash
from ..media import extract_audio, ffprobe, ingest, run_command
from ..audio import detect_clicks, repair_command
from ..audio import guard_loudness_command
from ..adapters.audio_models import AudioModelRequest, command as audio_model_command
from ..review import build_review_bundle
from ..video import baseline_command, deinterlace_command
from ..chunking import audio_route_manifest, plan_video_chunks
from ..video import stitch_qc
from ..sampling import plan_samples as build_sample_plan
from ..adapters.video_models import VideoModelRequest, request_manifest
from ..remux import remux_command, validation_command
from ..report import export_json, export_markdown
from ..analysis import analyze_probe


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
        return (analyze_probe(source.probe),)


class ExtractLosslessAudio:
    CATEGORY = "Restoration/02 Audio"
    RETURN_TYPES = ("RESTORATION_AUDIO",)
    FUNCTION = "extract"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"source": ("RESTORATION_SOURCE",), "workspace": ("STRING", {"default": "work"}), "output": ("STRING", {"default": "runs/audio-src.wav"})}}

    def extract(self, source: MediaSource, workspace: str, output: str):
        root = Path(workspace).expanduser()
        args = extract_audio(source, root, Path(output))
        run_command(args)
        probe = ffprobe(root / output)
        stream = next(item for item in probe.get("streams", []) if item.get("codec_type") == "audio")
        rate = int(stream.get("sample_rate", 0))
        count = int(stream.get("nb_frames", 0) or 0) or int(float(probe.get("format", {}).get("duration", 0) or 0) * rate)
        source_audio = next((item for item in source.probe.get("streams", []) if item.get("codec_type") == "audio"), {})
        offset_ms = float(source_audio.get("start_time", 0) or 0) * 1000
        return (AudioArtifact(output, rate, int(stream.get("channels", 0)), count, offset_ms, (source.path,)),)


class DetectAudioDefects:
    CATEGORY = "Restoration/03 Audio"
    RETURN_TYPES = ("JSON",)
    FUNCTION = "detect"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"wav_path": ("STRING", {"default": "runs/audio-src.wav"})}}

    def detect(self, wav_path: str):
        return (detect_clicks(Path(wav_path)),)


class RepairAudioDefects:
    CATEGORY = "Restoration/03 Audio"
    RETURN_TYPES = ("STRING",)
    FUNCTION = "repair"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"source": ("STRING",), "destination": ("STRING",), "method": (["adeclick", "bypass"],)}}

    def repair(self, source: str, destination: str, method: str):
        run_command(repair_command(Path(source), Path(destination), method=method))
        return (destination,)


class AudioEQLoudnessGuard:
    CATEGORY = "Restoration/03 Audio"
    RETURN_TYPES = ("STRING",)
    FUNCTION = "guard"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"source": ("STRING",), "destination": ("STRING",), "true_peak": ("FLOAT", {"default": -1.0, "max": 0})}}

    def guard(self, source: str, destination: str, true_peak: float):
        run_command(guard_loudness_command(Path(source), Path(destination), true_peak=true_peak))
        return (destination,)


class OptionalAudioModel:
    CATEGORY = "Restoration/03 Audio/Experimental"
    RETURN_TYPES = ("JSON",)
    FUNCTION = "configure"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"adapter": (["deepfilternet", "voicefixer", "resemble_enhance", "demucs"],), "source": ("STRING",), "destination": ("STRING",), "mode": (["denoise", "enhance"],), "attenuation_db": ("FLOAT", {"default": 6.0, "min": 0, "max": 30}), "device": (["auto", "cpu", "cuda", "mps"],), "chunk_seconds": ("FLOAT", {"default": 30.0, "min": 1}), "overlap_seconds": ("FLOAT", {"default": 2.0, "min": 0}), "master_rate": ("INT", {"default": 48000, "min": 8000}), "model_rate": ("INT", {"default": 48000, "min": 8000}), "experimental_reconstruction": ("BOOLEAN", {"default": False}), "bypass": ("BOOLEAN", {"default": False})}}

    def configure(self, adapter: str, source: str, destination: str, mode: str, attenuation_db: float, device: str, chunk_seconds: float, overlap_seconds: float, master_rate: int, model_rate: int, experimental_reconstruction: bool, bypass: bool):
        request = AudioModelRequest(adapter, Path(source), Path(destination), mode=mode, attenuation_db=attenuation_db, device=device, experimental_reconstruction=experimental_reconstruction, chunk_seconds=chunk_seconds, overlap_seconds=overlap_seconds, bypass=bypass, master_rate=master_rate, model_rate=model_rate)
        return ({"request": request.__dict__, "command": audio_model_command(request) if adapter in {"deepfilternet", "demucs"} or bypass else None},)


class VideoBaselineRestore:
    CATEGORY = "Restoration/04 Video"
    RETURN_TYPES = ("RESTORATION_VIDEO",)
    FUNCTION = "restore"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"source": ("STRING",), "destination": ("STRING",), "crf": ("INT", {"default": 19, "min": 16, "max": 24}), "target_aspect": (["preserve", "4:3", "16:9", "1:1"],)}}

    def restore(self, source: str, destination: str, crf: int, target_aspect: str):
        run_command(baseline_command(Path(source), Path(destination), crf=crf, target_aspect=target_aspect))
        probe = ffprobe(Path(destination))
        stream = next(item for item in probe.get("streams", []) if item.get("codec_type") == "video")
        return (VideoArtifact(destination, int(stream.get("width", 0)), int(stream.get("height", 0)), int(stream.get("nb_frames", 0) or 0), str(stream.get("r_frame_rate", "")), stream.get("sample_aspect_ratio"), stream.get("display_aspect_ratio"), (source,)),)


class VideoInterlaceHandler:
    CATEGORY = "Restoration/04 Video"
    RETURN_TYPES = ("RESTORATION_VIDEO",)
    FUNCTION = "deinterlace"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"source": ("STRING",), "destination": ("STRING",), "field_order": (["tt", "bb", "tb", "bt"],), "mode": (["send_frame", "send_field"],)}}

    def deinterlace(self, source: str, destination: str, field_order: str, mode: str):
        run_command(deinterlace_command(Path(source), Path(destination), field_order=field_order, mode=mode))
        return (destination,)


class CompareCandidates:
    CATEGORY = "Restoration/05 Review"
    RETURN_TYPES = ("STRING",)
    FUNCTION = "compare"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"workspace": ("STRING",), "source": ("STRING",), "candidates_json": ("STRING",)}}

    def compare(self, workspace: str, source: str, candidates_json: str):
        import json
        return (str(build_review_bundle(Path(workspace), source=source, candidates=json.loads(candidates_json))),)


class AudioSegmentRouter:
    CATEGORY = "Restoration/03 Audio"
    RETURN_TYPES = ("JSON",)
    FUNCTION = "route"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"total_samples": ("INT", {"min": 1}), "speech_regions_json": ("STRING", {"default": "[]"})}}

    def route(self, total_samples: int, speech_regions_json: str):
        import json
        return (audio_route_manifest(total_samples, json.loads(speech_regions_json)),)


class VideoChunkPlannerStitcher:
    CATEGORY = "Restoration/04 Video"
    RETURN_TYPES = ("JSON",)
    FUNCTION = "plan"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"total_frames": ("INT", {"min": 1}), "chunk_frames": ("INT", {"default": 150, "min": 1}), "overlap_frames": ("INT", {"default": 12, "min": 0}), "scene_cuts_json": ("STRING", {"default": "[]"})}}

    def plan(self, total_frames: int, chunk_frames: int, overlap_frames: int, scene_cuts_json: str):
        import json
        chunks = plan_video_chunks(total_frames, chunk_frames=chunk_frames, overlap_frames=overlap_frames, scene_cuts=json.loads(scene_cuts_json))
        return ({"chunks": [chunk.__dict__ for chunk in chunks], "qc": stitch_qc(chunks, expected_frames=total_frames)},)


class VideoModelAdapter:
    CATEGORY = "Restoration/04 Video"
    RETURN_TYPES = ("JSON",)
    FUNCTION = "configure"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"backend": ("STRING",), "source": ("STRING",), "destination": ("STRING",), "model_hash": ("STRING",), "scale": ("INT", {"default": 1, "min": 1}), "temporal_window": ("INT", {"default": 5, "min": 1}), "strength": ("FLOAT", {"default": 0.1, "min": 0, "max": 1}), "seed": ("INT", {"default": 0}), "tile_size": ("INT", {"default": 0, "min": 0}), "tile_overlap": ("INT", {"default": 0, "min": 0}), "offload": ("BOOLEAN", {"default": False})}}

    def configure(self, backend: str, source: str, destination: str, model_hash: str, scale: int, temporal_window: int, strength: float, seed: int, tile_size: int, tile_overlap: int, offload: bool):
        return (request_manifest(VideoModelRequest(backend, Path(source), Path(destination), model_hash, scale, temporal_window, strength, seed, tile_size=tile_size or None, tile_overlap=tile_overlap, offload=offload)),)


class PreservationAwareRemux:
    CATEGORY = "Restoration/07 Output"
    RETURN_TYPES = ("STRING",)
    FUNCTION = "build"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"source": ("STRING",), "video": ("STRING",), "audio": ("STRING",), "destination": ("STRING",), "delay_ms": ("INT", {"default": 0})}}

    def build(self, source: str, video: str, audio: str, destination: str, delay_ms: int):
        run_command(remux_command(Path(source), Path(video), Path(audio), Path(destination), delay_ms=delay_ms))
        return (destination,)


class ValidateRestoration:
    CATEGORY = "Restoration/07 Output"
    RETURN_TYPES = ("STRING",)
    FUNCTION = "validate"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"output": ("STRING",)}}

    def validate(self, output: str):
        run_command(validation_command(Path(output)))
        return (output,)


class ExportReviewReport:
    CATEGORY = "Restoration/06 Review"
    RETURN_TYPES = ("STRING",)
    FUNCTION = "export"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"source_json": ("STRING",), "destination": ("STRING",), "workspace": ("STRING",)}}

    def export(self, source_json: str, destination: str, workspace: str):
        source = Path(source_json)
        output = Path(destination)
        root = Path(workspace)
        export_json(source, output.with_suffix(".json"), root)
        export_markdown(source, output.with_suffix(".md"), root)
        return (destination,)


class PlanRepresentativeSamples:
    CATEGORY = "Restoration/02 Planning"
    RETURN_TYPES = ("RESTORATION_SAMPLE_PLAN",)
    FUNCTION = "plan"
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"duration_seconds": ("FLOAT", {"default": 60.0, "min": 1.0}), "seed": ("INT", {"default": 0})}, "optional": {"source": ("RESTORATION_SOURCE",)}}

    def plan(self, duration_seconds: float, seed: int):
        samples = tuple(build_sample_plan(duration_seconds))
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
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"workspace": ("STRING", {"default": "work"}), "run_id": ("STRING", {"default": "restoration-1"}), "parameters_json": ("STRING", {"default": "{}"}), "approval": ("RESTORATION_APPROVAL",), "chunks_json": ("STRING", {"default": "[\"sample-A\"]"})}}

    def start(self, workspace: str, run_id: str, parameters_json: str, approval: Approval, chunks_json: str):
        import json
        approval.validate()
        parameters = json.loads(parameters_json)
        run = ResumableRun(Path(workspace), run_id, parameters)
        state = run.execute(json.loads(chunks_json), lambda chunk: str(Path("runs") / run_id / f"{chunk}.done"), approval)
        return (state,)


NODE_CLASS_MAPPINGS = {"RestorationLoadMedia": RestorationLoadMedia, "AnalyzeSource": AnalyzeSource, "ExtractLosslessAudio": ExtractLosslessAudio, "DetectAudioDefects": DetectAudioDefects, "RepairAudioDefects": RepairAudioDefects, "AudioEQLoudnessGuard": AudioEQLoudnessGuard, "DeepFilterNetAudio": OptionalAudioModel, "VoiceFixerAudio": OptionalAudioModel, "ResembleEnhanceAudio": OptionalAudioModel, "DemucsSeparateRecombine": OptionalAudioModel, "PlanRepresentativeSamples": PlanRepresentativeSamples, "VideoBaselineRestore": VideoBaselineRestore, "VideoInterlaceHandler": VideoInterlaceHandler, "CompareCandidates": CompareCandidates, "AudioSegmentRouter": AudioSegmentRouter, "VideoChunkPlannerStitcher": VideoChunkPlannerStitcher, "VideoModelAdapter": VideoModelAdapter, "PreservationAwareRemux": PreservationAwareRemux, "ValidateRestoration": ValidateRestoration, "ExportReviewReport": ExportReviewReport, "HumanApprovalGate": HumanApprovalGate, "ResumableFullRun": ResumableFullRun}
NODE_DISPLAY_NAME_MAPPINGS = {key: "Restoration " + key.removeprefix("Restoration").replace("Audio", " Audio") for key in NODE_CLASS_MAPPINGS}
