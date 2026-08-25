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
    visual_quality: dict | None,
    motion_analysis: dict | None,
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

    if visual_quality:
        visual_warnings = visual_quality.get("warnings", [])

        if visual_quality["sharpness_score"] < 70:
            recommendations.append(
                {
                    "area": "Visual sharpness",
                    "priority": "High" if visual_quality["sharpness_score"] < 50 else "Medium",
                    "recommendation": "Several sampled frames appear soft or blurred. Re-export from a sharper source or replace blurred shots.",
                }
            )

        if visual_quality["exposure_score"] < 70:
            recommendation = "Adjust lighting or exposure so the subject remains readable throughout the edit."

            if any("underexposed" in warning for warning in visual_warnings):
                recommendation = "The image is consistently underexposed. Lift exposure or replace the darkest shots."
            elif any("overexposed" in warning for warning in visual_warnings):
                recommendation = "Some sampled frames appear overexposed. Recover highlights or reduce exposure in the edit."

            recommendations.append(
                {
                    "area": "Visual exposure",
                    "priority": "High" if visual_quality["exposure_score"] < 50 else "Medium",
                    "recommendation": recommendation,
                }
            )

        if visual_quality["contrast_score"] < 70:
            recommendations.append(
                {
                    "area": "Visual contrast",
                    "priority": "High" if visual_quality["contrast_score"] < 50 else "Medium",
                    "recommendation": "Increase subject/background separation with contrast, lighting, or color grade adjustments.",
                }
            )

        if visual_quality["consistency_score"] < 70:
            recommendations.append(
                {
                    "area": "Visual consistency",
                    "priority": "High" if visual_quality["consistency_score"] < 50 else "Medium",
                    "recommendation": "Lighting varies substantially across the video. Match exposure and color between shots.",
                }
            )
    else:
        recommendations.append(
            {
                "area": "Visual quality",
                "priority": "Medium",
                "recommendation": "Extract readable keyframes so visual sharpness, exposure, contrast, and consistency can be assessed.",
            }
        )

    if motion_analysis:
        if motion_analysis["motion_level"] == "Visually static":
            recommendations.append(
                {
                    "area": "Visual activity",
                    "priority": "Medium",
                    "recommendation": "The video remains visually static for long periods. Consider introducing a visual change around the middle of the video.",
                }
            )
        elif motion_analysis["motion_level"] == "Low movement":
            recommendations.append(
                {
                    "area": "Visual activity",
                    "priority": "Low",
                    "recommendation": "Consider adding a cutaway, product detail, text treatment, or camera movement to create more visual change.",
                }
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
                "area": "Visual and creative quality",
                "priority": "Low",
                "recommendation": "Visual quality is strong and consistent. Review captions, safe zones, and final export settings manually.",
            }
        )

    return recommendations
