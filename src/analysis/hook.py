import re


HOOK_PATTERNS = {
    "direct_command": [
        r"\bstop\b",
        r"\bwatch\b",
        r"\blisten\b",
        r"\blook\b",
        r"\bwait\b",
        r"\bdon't\b",
    ],
    "question": [
        r"\?",
        r"\bdid you know\b",
        r"\bhave you ever\b",
        r"\bwhat if\b",
        r"\bwhy\b",
        r"\bhow\b",
    ],
    "curiosity": [
        r"\bsecret\b",
        r"\bmistake\b",
        r"\bmost people\b",
        r"\byou need to know\b",
        r"\bhere's why\b",
        r"\bthis is why\b",
    ],
    "benefit": [
        r"\bsave\b",
        r"\bimprove\b",
        r"\bincrease\b",
        r"\bgrow\b",
        r"\bbetter\b",
        r"\bfaster\b",
    ],
}


def analyse_hook(words: list, hook_window: float = 3.0) -> dict:
    """
    Analyse spoken words occurring within the opening hook window.

    This is a transparent heuristic score, not an ML prediction.
    """

    if not words:
        return {
            "hook_present": False,
            "hook_text": "",
            "hook_start": None,
            "hook_end": None,
            "hook_type": "No spoken hook",
            "score": 0,
            "reasons": ["No spoken words were detected in the opening."],
        }

    hook_words = [
        word for word in words
        if word["start"] <= hook_window
    ]

    if not hook_words:
        return {
            "hook_present": False,
            "hook_text": "",
            "hook_start": None,
            "hook_end": None,
            "hook_type": "Late speech",
            "score": 15,
            "reasons": [
                f"No speech was detected within the first {hook_window:.0f} seconds."
            ],
        }

    hook_text = " ".join(
        word["word"] for word in hook_words
    ).strip()

    lower_text = hook_text.lower()

    matched_types = []

    for hook_type, patterns in HOOK_PATTERNS.items():
        if any(
            re.search(pattern, lower_text)
            for pattern in patterns
        ):
            matched_types.append(hook_type)

    start = hook_words[0]["start"]
    end = hook_words[-1]["end"]

    score = 40
    reasons = []

    # Earlier spoken openings score better.
    if start <= 0.5:
        score += 20
        reasons.append("Speech begins almost immediately.")
    elif start <= 1.5:
        score += 12
        reasons.append("Speech begins early.")
    else:
        reasons.append("The spoken opening begins relatively late.")

    # Reward recognised hook structures.
    if matched_types:
        score += min(30, 12 * len(matched_types))
        reasons.append(
            "Opening uses recognised attention patterns: "
            + ", ".join(
                item.replace("_", " ")
                for item in matched_types
            )
            + "."
        )
    else:
        reasons.append(
            "No strong command, question, curiosity or benefit pattern was detected."
        )

    # Extremely long hook sections can weaken clarity.
    word_count = len(hook_words)

    if 2 <= word_count <= 12:
        score += 10
        reasons.append("Opening message is concise.")

    score = max(0, min(100, score))

    hook_type = (
        ", ".join(
            item.replace("_", " ").title()
            for item in matched_types
        )
        if matched_types
        else "General opening"
    )

    return {
        "hook_present": True,
        "hook_text": hook_text,
        "hook_start": round(start, 2),
        "hook_end": round(end, 2),
        "hook_type": hook_type,
        "score": score,
        "reasons": reasons,
    }