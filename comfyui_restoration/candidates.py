"""Explicit sample candidate matrix; combinations are evidence-driven, not automatic."""

from __future__ import annotations


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
    ]


def record_candidate(candidate: dict, *, metrics: dict, review_status: str = "pending", rejection_reason: str | None = None) -> dict:
    if review_status not in {"pending", "approved", "rejected"}:
        raise ValueError("invalid candidate review status")
    result = {**candidate, "metrics": metrics, "review_status": review_status}
    if rejection_reason:
        result["rejection_reason"] = rejection_reason
    return result

