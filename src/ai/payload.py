import hashlib
import json


def _get(data: dict | None, key: str, default=None):
    if not isinstance(data, dict):
        return default

    return data.get(key, default)


def _round_number(value, digits: int = 2):
    if isinstance(value, (int, float)):
        return round(value, digits)

    return value


def build_creative_review_payload(
    client_name: str,
    campaign_name: str,
    objective: str,
    target_platform: str,
    video_metadata: dict,
    transcript: dict | None,
    speech_analysis: dict | None,
    hook_analysis: dict | None,
    cta_analysis: dict | None,
    message_analysis: dict | None,
    story_analysis: dict | None,
    scene_analysis: dict,
    pacing_analysis: dict,
    visual_quality: dict,
    motion_analysis: dict,
    technical_quality: dict,
    platform_fit: dict,
    objective_analysis: dict,
    creative_score: dict,
    recommendations: list,
) -> dict:
    """
    Build the compact evidence payload sent to the AI Creative Director.
    """

    full_transcript = _get(transcript, "transcript", "") or ""

    return {
        "campaign": {
            "client_name": client_name or "Not specified",
            "campaign_name": campaign_name or "Not specified",
            "objective": objective,
            "target_platform": target_platform,
        },
        "video": {
            "duration": _get(video_metadata, "duration", 0),
            "resolution": _get(video_metadata, "resolution", ""),
            "width": _get(video_metadata, "width", 0),
            "height": _get(video_metadata, "height", 0),
            "fps": _get(video_metadata, "fps", 0),
            "aspect_ratio": _get(video_metadata, "aspect_ratio", ""),
            "orientation": _get(video_metadata, "orientation", ""),
            "file_size_mb": _get(video_metadata, "file_size_mb", 0),
        },
        "transcript": {
            "available": bool(full_transcript.strip()),
            "full_transcript": full_transcript,
            "confidence": _get(transcript, "confidence"),
        },
        "speech": {
            "word_count": _get(speech_analysis, "word_count", 0),
            "words_per_minute": _get(speech_analysis, "words_per_minute", 0),
            "speech_rate": _get(speech_analysis, "speech_rate", "No speech"),
        },
        "hook": {
            "current_hook": _get(hook_analysis, "hook_text", ""),
            "score": _get(hook_analysis, "score", 0),
            "hook_type": _get(hook_analysis, "hook_type", "Not available"),
            "hook_start": _get(hook_analysis, "hook_start"),
            "hook_end": _get(hook_analysis, "hook_end"),
            "reasons": _get(hook_analysis, "reasons", []),
        },
        "cta": {
            "detected": _get(cta_analysis, "cta_detected", False),
            "current_cta": _get(cta_analysis, "cta_text", ""),
            "score": _get(cta_analysis, "score", 0),
            "cta_start": _get(cta_analysis, "cta_start"),
            "cta_position": _get(cta_analysis, "cta_position", "Not detected"),
        },
        "message": {
            "score": _get(message_analysis, "score", 0),
            "clarity_label": _get(message_analysis, "clarity_label", "Not available"),
            "problem_detected": _get(message_analysis, "problem_detected", False),
            "value_detected": _get(message_analysis, "value_detected", False),
            "reasons": _get(message_analysis, "reasons", []),
        },
        "story": {
            "score": _get(story_analysis, "score", 0),
            "label": _get(story_analysis, "label", "Not available"),
            "components": _get(story_analysis, "components", {}),
            "missing": _get(story_analysis, "missing", []),
        },
        "pacing": {
            "scene_count": _get(scene_analysis, "scene_count", 0),
            "average_scene_duration": _get(
                pacing_analysis,
                "average_scene_duration",
                0,
            ),
            "scenes_per_minute": _get(pacing_analysis, "scenes_per_minute", 0),
            "pacing_label": _get(pacing_analysis, "pacing_label", "Not available"),
        },
        "visual": {
            "score": _get(visual_quality, "score", 0),
            "sharpness_score": _get(visual_quality, "sharpness_score", 0),
            "exposure_score": _get(visual_quality, "exposure_score", 0),
            "contrast_score": _get(visual_quality, "contrast_score", 0),
            "consistency_score": _get(visual_quality, "consistency_score", 0),
            "motion_level": _get(motion_analysis, "motion_level", "Not available"),
            "warnings": _get(visual_quality, "warnings", [])
            + _get(motion_analysis, "warnings", []),
        },
        "technical": {
            "score": _get(technical_quality, "score", 0),
            "label": _get(technical_quality, "label", "Not available"),
            "reasons": _get(technical_quality, "reasons", []),
        },
        "platform": {
            "score": _get(platform_fit, "score", 0),
            "target_platform": _get(platform_fit, "platform", target_platform),
            "label": _get(platform_fit, "label", "Not available"),
            "reasons": _get(platform_fit, "reasons", []),
        },
        "objective": {
            "score": _get(objective_analysis, "score", 0),
            "objective": _get(objective_analysis, "objective", objective),
        },
        "overall": {
            "score": _get(creative_score, "score", 0),
            "label": _get(creative_score, "label", "Not available"),
            "weights": _get(creative_score, "weights", {}),
            "component_scores": _get(creative_score, "components", {}),
        },
        "recommendations": recommendations or [],
    }


def payload_fingerprint(payload: dict) -> str:
    payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
