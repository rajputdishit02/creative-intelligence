TECHNICAL_COMPONENT_WEIGHTS = {
    "resolution": 25,
    "frame_rate": 20,
    "orientation": 15,
    "aspect_ratio": 20,
    "duration": 20,
}

COMMON_ASPECT_RATIOS = {"9:16", "16:9", "1:1", "4:5", "3:4"}


def _label(score: float) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Strong"
    if score >= 50:
        return "Moderate"
    return "Needs work"


def score_technical_quality(video_metadata: dict) -> dict:
    """
    Score production readiness from video metadata.

    This is a transparent heuristic, not a validated performance prediction.
    """

    width = video_metadata.get("width", 0)
    height = video_metadata.get("height", 0)
    fps = video_metadata.get("fps", 0)
    duration = video_metadata.get("duration", 0)
    orientation = video_metadata.get("orientation", "Unknown")
    aspect_ratio = video_metadata.get("aspect_ratio", "Unknown")
    short_edge = min(width, height)
    long_edge = max(width, height)

    components = {}
    reasons = []

    if short_edge >= 1080 or long_edge >= 1920:
        components["resolution"] = 100
        reasons.append("Resolution supports a high-quality 1080p-style export.")
    elif short_edge >= 720 or long_edge >= 1280:
        components["resolution"] = 80
        reasons.append("Resolution is HD and suitable for most digital placements.")
    elif short_edge >= 540:
        components["resolution"] = 55
        reasons.append("Resolution is usable but may appear soft after compression.")
    else:
        components["resolution"] = 30
        reasons.append("Resolution is low for a polished marketing video.")

    if 24 <= fps <= 60:
        components["frame_rate"] = 100
        reasons.append("Frame rate is within the standard 24-60 FPS delivery range.")
    elif 15 <= fps < 24:
        components["frame_rate"] = 65
        reasons.append("Frame rate is below the usual delivery range and may feel less smooth.")
    elif fps > 60:
        components["frame_rate"] = 75
        reasons.append("Frame rate is high; confirm the export platform preserves it cleanly.")
    else:
        components["frame_rate"] = 20
        reasons.append("Frame rate could not be read or is unusually low.")

    if orientation in {"Vertical", "Landscape", "Square"}:
        components["orientation"] = 100
        reasons.append(f"{orientation} orientation was detected clearly.")
    else:
        components["orientation"] = 40
        reasons.append("Orientation could not be classified clearly.")

    if aspect_ratio in COMMON_ASPECT_RATIOS:
        components["aspect_ratio"] = 100
        reasons.append(f"{aspect_ratio} is a common digital-video aspect ratio.")
    else:
        components["aspect_ratio"] = 60
        reasons.append("Aspect ratio is uncommon and may require custom cropping.")

    if 6 <= duration <= 90:
        components["duration"] = 100
        reasons.append("Duration is suitable for short-form campaign creative.")
    elif 3 <= duration < 6:
        components["duration"] = 70
        reasons.append("Duration is very short; confirm the message has enough time to land.")
    elif 90 < duration <= 180:
        components["duration"] = 70
        reasons.append("Duration is long for short-form placements but usable in broader contexts.")
    elif duration > 180:
        components["duration"] = 40
        reasons.append("Duration is likely too long for most short-form placements.")
    else:
        components["duration"] = 20
        reasons.append("Duration could not be read or is too short to evaluate confidently.")

    score = sum(
        components[name] * weight / 100
        for name, weight in TECHNICAL_COMPONENT_WEIGHTS.items()
    )

    return {
        "score": round(score, 1),
        "label": _label(score),
        "components": components,
        "reasons": reasons,
        "weights": TECHNICAL_COMPONENT_WEIGHTS,
    }
