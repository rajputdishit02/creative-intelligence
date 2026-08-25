def analyse_story(
    hook_analysis: dict,
    message_analysis: dict,
    cta_analysis: dict
) -> dict:
    """
    Evaluate a basic marketing story structure:

    Hook -> Problem -> Value -> CTA
    """

    components = {
        "hook": hook_analysis["hook_present"],
        "problem": message_analysis["problem_detected"],
        "value": message_analysis["value_detected"],
        "cta": cta_analysis["cta_detected"],
    }

    present_count = sum(
        1 for value in components.values()
        if value
    )

    score = int(
        present_count / len(components) * 100
    )

    missing = [
        name.title()
        for name, present in components.items()
        if not present
    ]

    if score == 100:
        label = "Complete"
    elif score >= 75:
        label = "Strong"
    elif score >= 50:
        label = "Partial"
    else:
        label = "Weak"

    return {
        "score": score,
        "label": label,
        "components": components,
        "missing": missing,
    }