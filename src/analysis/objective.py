OBJECTIVE_WEIGHTS = {
    "Brand Awareness": {
        "hook": 0.35,
        "message": 0.30,
        "cta": 0.10,
        "story": 0.25,
    },

    "Engagement": {
        "hook": 0.40,
        "message": 0.20,
        "cta": 0.15,
        "story": 0.25,
    },

    "Lead Generation": {
        "hook": 0.20,
        "message": 0.30,
        "cta": 0.35,
        "story": 0.15,
    },

    "Sales / Conversion": {
        "hook": 0.20,
        "message": 0.30,
        "cta": 0.35,
        "story": 0.15,
    },

    "Community Building": {
        "hook": 0.25,
        "message": 0.30,
        "cta": 0.15,
        "story": 0.30,
    },

    "Event Promotion": {
        "hook": 0.25,
        "message": 0.25,
        "cta": 0.35,
        "story": 0.15,
    },

    "Recruitment": {
        "hook": 0.20,
        "message": 0.35,
        "cta": 0.25,
        "story": 0.20,
    },

    "Trust / Authority": {
        "hook": 0.15,
        "message": 0.40,
        "cta": 0.10,
        "story": 0.35,
    },
}


def calculate_objective_score(
    objective: str,
    hook_score: float,
    message_score: float,
    cta_score: float,
    story_score: float,
) -> dict:

    weights = OBJECTIVE_WEIGHTS.get(
        objective,
        OBJECTIVE_WEIGHTS["Brand Awareness"]
    )

    score = (
        hook_score * weights["hook"]
        + message_score * weights["message"]
        + cta_score * weights["cta"]
        + story_score * weights["story"]
    )

    return {
        "score": round(score, 1),
        "objective": objective,
        "weights": weights,
    }