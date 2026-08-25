PLATFORM_REQUIREMENTS = {
    "Instagram Reels": {
        "orientations": ["Vertical"],
        "aspect_ratios": ["9:16"],
        "min_short_edge": 720,
        "ideal_duration": (6, 90),
    },
    "TikTok": {
        "orientations": ["Vertical"],
        "aspect_ratios": ["9:16"],
        "min_short_edge": 720,
        "ideal_duration": (6, 90),
    },
    "YouTube Shorts": {
        "orientations": ["Vertical"],
        "aspect_ratios": ["9:16"],
        "min_short_edge": 720,
        "ideal_duration": (6, 60),
    },
    "LinkedIn": {
        "orientations": ["Landscape", "Square", "Vertical"],
        "aspect_ratios": ["16:9", "1:1", "4:5", "9:16"],
        "min_short_edge": 720,
        "ideal_duration": (15, 120),
    },
    "Facebook": {
        "orientations": ["Landscape", "Square", "Vertical"],
        "aspect_ratios": ["16:9", "1:1", "4:5", "9:16"],
        "min_short_edge": 720,
        "ideal_duration": (6, 120),
    },
    "Website": {
        "orientations": ["Landscape", "Square"],
        "aspect_ratios": ["16:9", "1:1"],
        "min_short_edge": 720,
        "ideal_duration": (15, 180),
    },
}

PLATFORM_COMPONENT_WEIGHTS = {
    "orientation": 20,
    "aspect_ratio": 30,
    "resolution": 20,
    "frame_rate": 10,
    "duration": 20,
}


def _label(score: float) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Strong"
    if score >= 50:
        return "Moderate"
    return "Needs work"


def _duration_score(duration: float, ideal_range: tuple[int, int]) -> tuple[int, str]:
    minimum, maximum = ideal_range

    if minimum <= duration <= maximum:
        return 100, f"Duration is within the preferred {minimum}-{maximum}s range."
    if duration < minimum:
        return 55, f"Duration is shorter than the preferred {minimum}s minimum."
    if duration <= maximum * 1.5:
        return 65, f"Duration is longer than the preferred {maximum}s maximum."
    return 35, f"Duration is well above the preferred {maximum}s maximum."


def score_platform_fit(video_metadata: dict, platform: str) -> dict:
    requirements = PLATFORM_REQUIREMENTS.get(platform)

    if not requirements:
        return {
            "platform": platform,
            "score": 0,
            "label": "Not scored",
            "components": {},
            "reasons": ["No compatibility profile is available for this platform."],
            "weights": PLATFORM_COMPONENT_WEIGHTS,
        }

    width = video_metadata.get("width", 0)
    height = video_metadata.get("height", 0)
    short_edge = min(width, height)
    fps = video_metadata.get("fps", 0)
    duration = video_metadata.get("duration", 0)
    orientation = video_metadata.get("orientation", "Unknown")
    aspect_ratio = video_metadata.get("aspect_ratio", "Unknown")

    components = {}
    reasons = []

    if orientation in requirements["orientations"]:
        components["orientation"] = 100
        reasons.append(f"{orientation} orientation is suitable for {platform}.")
    else:
        components["orientation"] = 35
        expected = ", ".join(requirements["orientations"])
        reasons.append(f"{platform} is better suited to {expected} orientation.")

    if aspect_ratio in requirements["aspect_ratios"]:
        components["aspect_ratio"] = 100
        reasons.append(f"{aspect_ratio} aspect ratio matches {platform} guidance.")
    else:
        components["aspect_ratio"] = 40
        expected = ", ".join(requirements["aspect_ratios"])
        reasons.append(f"Consider reframing to one of these aspect ratios: {expected}.")

    if short_edge >= requirements["min_short_edge"]:
        components["resolution"] = 100
        reasons.append("Resolution has enough detail for a clean platform export.")
    elif short_edge >= 540:
        components["resolution"] = 65
        reasons.append("Resolution is usable but may look soft after compression.")
    else:
        components["resolution"] = 35
        reasons.append("Resolution is likely too low for a polished platform export.")

    if 24 <= fps <= 60:
        components["frame_rate"] = 100
        reasons.append("Frame rate is in a standard social-video range.")
    elif fps > 0:
        components["frame_rate"] = 55
        reasons.append("Frame rate is outside the common 24-60 FPS delivery range.")
    else:
        components["frame_rate"] = 0
        reasons.append("Frame rate could not be read.")

    duration_score, duration_reason = _duration_score(
        duration,
        requirements["ideal_duration"],
    )
    components["duration"] = duration_score
    reasons.append(duration_reason)

    score = sum(
        components[name] * weight / 100
        for name, weight in PLATFORM_COMPONENT_WEIGHTS.items()
    )

    return {
        "platform": platform,
        "score": round(score, 1),
        "label": _label(score),
        "components": components,
        "reasons": reasons,
        "weights": PLATFORM_COMPONENT_WEIGHTS,
    }


def score_all_platforms(video_metadata: dict) -> dict:
    return {
        platform: score_platform_fit(video_metadata, platform)
        for platform in PLATFORM_REQUIREMENTS
    }
