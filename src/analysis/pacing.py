"""Pacing analysis for the Creative Intelligence Platform."""
def analyse_pacing(
    duration: float,
    scene_count: int
) -> dict:

    if duration <= 0:
        raise ValueError("Video duration must be greater than zero.")

    average_scene_duration = duration / scene_count

    scenes_per_minute = (
        scene_count / duration
    ) * 60

    if average_scene_duration <= 2:
        pacing_label = "Very Fast"
    elif average_scene_duration <= 4:
        pacing_label = "Fast"
    elif average_scene_duration <= 7:
        pacing_label = "Moderate"
    elif average_scene_duration <= 12:
        pacing_label = "Slow"
    else:
        pacing_label = "Very Slow"

    return {
        "average_scene_duration": round(
            average_scene_duration,
            2
        ),
        "scenes_per_minute": round(
            scenes_per_minute,
            2
        ),
        "pacing_label": pacing_label,
    }
