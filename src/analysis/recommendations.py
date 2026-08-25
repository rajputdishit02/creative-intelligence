def _add_score_recommendation(recommendations: list, score: float, title: str, action: str) -> None:
    if score < 70:
        recommendations.append(
            {
                "area": title,
                "priority": "High" if score < 50 else "Medium",
                "recommendation": action,
            }
        )


def build_recommendations(
    creative_score: dict,
    technical_quality: dict,
    platform_fit: dict,
    hook_analysis: dict | None,
    cta_analysis: dict | None,
    pacing_score: dict,
    objective_analysis: dict | None,
) -> list:
    """
    Convert weak heuristic scores into concrete editing recommendations.
    """

    recommendations = []

    if objective_analysis:
        _add_score_recommendation(
            recommendations,
            objective_analysis["score"],
            "Campaign objective fit",
            "Tighten the message around the selected campaign objective and make the primary value proposition more explicit.",
        )

    _add_score_recommendation(
        recommendations,
        technical_quality["score"],
        "Technical quality",
        "Export a cleaner master with stronger resolution, standard frame rate, and a common aspect ratio before publishing.",
    )

    _add_score_recommendation(
        recommendations,
        platform_fit["score"],
        "Platform fit",
        f"Reframe or trim the edit for {platform_fit['platform']} so orientation, aspect ratio, and duration match the placement.",
    )

    if hook_analysis:
        _add_score_recommendation(
            recommendations,
            hook_analysis["score"],
            "Hook",
            "Move the strongest audience problem, benefit, question, or visual interruption into the first three seconds.",
        )
    else:
        recommendations.append(
            {
                "area": "Hook",
                "priority": "High",
                "recommendation": "Add spoken or visual hook evidence early enough for the app to evaluate the opening.",
            }
        )

    if cta_analysis:
        if not cta_analysis["cta_detected"]:
            recommendations.append(
                {
                    "area": "CTA",
                    "priority": "High",
                    "recommendation": "Add a clear call to action such as book, shop, sign up, learn more, or contact.",
                }
            )
        else:
            _add_score_recommendation(
                recommendations,
                cta_analysis["score"],
                "CTA",
                "Make the call to action more direct and place it where viewers have enough context to act.",
            )
    else:
        recommendations.append(
            {
                "area": "CTA",
                "priority": "High",
                "recommendation": "Add transcript-backed CTA evidence so the app can evaluate action clarity and timing.",
            }
        )

    _add_score_recommendation(
        recommendations,
        pacing_score["score"],
        "Pacing",
        "Adjust edit density by adding scene changes, trimming slow sections, or adding pauses if the message feels rushed.",
    )

    if not recommendations:
        recommendations.append(
            {
                "area": "Creative quality",
                "priority": "Low",
                "recommendation": "Scores are strong. Review the platform-specific reasons and polish captions, safe zones, and final export settings manually.",
            }
        )

    return recommendations
