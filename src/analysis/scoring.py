CREATIVE_SCORE_WEIGHTS = {
    "campaign_objective_fit": 0.25,
    "technical_quality": 0.20,
    "platform_fit": 0.20,
    "hook": 0.15,
    "cta": 0.10,
    "pacing": 0.10,
}


def score_pacing_for_creative(pacing_analysis: dict) -> dict:
    label = pacing_analysis.get("pacing_label", "Unknown")

    scores = {
        "Very Fast": 70,
        "Fast": 90,
        "Moderate": 85,
        "Slow": 60,
        "Very Slow": 40,
    }

    reasons = {
        "Very Fast": "Pacing is energetic but may need breathing room for clarity.",
        "Fast": "Pacing is strong for short-form attention.",
        "Moderate": "Pacing is clear and easy to follow.",
        "Slow": "Pacing may need tighter edits to hold attention.",
        "Very Slow": "Pacing is likely too slow for most short-form placements.",
    }

    score = scores.get(label, 50)

    return {
        "score": score,
        "label": label,
        "reasons": [reasons.get(label, "Pacing could not be classified clearly.")],
    }


def calculate_creative_score(
    objective_score: float,
    technical_score: float,
    platform_score: float,
    hook_score: float,
    cta_score: float,
    pacing_score: float,
) -> dict:
    """
    Combine creative diagnostics into one transparent heuristic score.

    The result is not a validated reach, conversion, or performance prediction.
    """

    components = {
        "campaign_objective_fit": objective_score,
        "technical_quality": technical_score,
        "platform_fit": platform_score,
        "hook": hook_score,
        "cta": cta_score,
        "pacing": pacing_score,
    }

    score = sum(
        components[name] * weight
        for name, weight in CREATIVE_SCORE_WEIGHTS.items()
    )

    if score >= 85:
        label = "Excellent"
    elif score >= 70:
        label = "Strong"
    elif score >= 50:
        label = "Moderate"
    else:
        label = "Needs work"

    return {
        "score": round(score, 1),
        "label": label,
        "components": components,
        "weights": CREATIVE_SCORE_WEIGHTS,
        "disclaimer": (
            "This is a transparent heuristic quality score, not a validated "
            "reach or conversion prediction."
        ),
    }
