"""Explicit sample candidate matrix; combinations are evidence-driven, not automatic."""

from __future__ import annotations

from copy import deepcopy


def audio_candidate_matrix() -> list[dict]:
    return [
        {"id": "untouched", "stages": [], "lane": "faithful", "status": "required_baseline"},
        {"id": "dsp_declick_dehiss", "stages": ["declick", "dsp_denoise"], "lane": "faithful", "status": "required"},
        {"id": "deepfilternet", "stages": ["deepfilternet"], "lane": "optional_model", "status": "optional"},
        {"id": "declick_then_deepfilternet", "stages": ["declick", "deepfilternet"], "lane": "optional_model", "status": "optional"},
        {"id": "deepfilternet_then_declick", "stages": ["deepfilternet", "declick"], "lane": "optional_model", "status": "optional"},
        {"id": "voicefixer_speech", "stages": ["speech_router", "voicefixer"], "lane": "experimental_reconstruction", "status": "optional"},
        {"id": "resemble_denoise_speech", "stages": ["speech_router", "resemble_denoise"], "lane": "experimental_reconstruction", "status": "optional"},
        {"id": "resemble_enhance_speech", "stages": ["speech_router", "resemble_enhance"], "lane": "experimental_reconstruction", "status": "optional"},
        {"id": "demucs_speech_music", "stages": ["demucs", "speech_router"], "lane": "optional_model", "status": "conditional"},
        {"id": "best_evidence_two_stage", "stages": [], "lane": "evidence_selected", "status": "deferred_until_sample_review"},
    ]


def plan_audio_candidates(sample_ids: list[str], *, include_demucs_samples: set[str] | None = None) -> dict[str, list[dict]]:
    """Expand the required matrix for each sample without selecting a subjective winner."""
    if not sample_ids or any(not sample.strip() for sample in sample_ids):
        raise ValueError("at least one non-empty sample id is required")
    if len(set(sample_ids)) != len(sample_ids):
        raise ValueError("sample ids must be unique")
    demucs_samples = include_demucs_samples or set()
    result: dict[str, list[dict]] = {}
    for sample_id in sample_ids:
        branches = []
        for candidate in audio_candidate_matrix():
            branch = deepcopy(candidate)
            branch["sample_id"] = sample_id
            branch["parameters"] = {"master_rate": 48000, "chunk_seconds": 30, "overlap_seconds": 2}
            if candidate["id"] == "demucs_speech_music" and sample_id not in demucs_samples:
                branch["status"] = "rejected"
                branch["rejection_reason"] = "no demonstrated overlapping speech/music use case"
            branches.append(branch)
        result[sample_id] = branches
    return result


def record_candidate(candidate: dict, *, metrics: dict, review_status: str = "pending", rejection_reason: str | None = None) -> dict:
    if review_status not in {"pending", "approved", "rejected"}:
        raise ValueError("invalid candidate review status")
    if review_status == "rejected" and not rejection_reason:
        raise ValueError("rejected candidates require a rejection reason")
    result = {**candidate, "metrics": metrics, "review_status": review_status}
    if rejection_reason:
        result["rejection_reason"] = rejection_reason
    return result
