import re


VALUE_PATTERNS = [
    r"\bhelp\b",
    r"\bimprove\b",
    r"\bsave\b",
    r"\bincrease\b",
    r"\bgrow\b",
    r"\breduce\b",
    r"\bbetter\b",
    r"\bfaster\b",
    r"\bstronger\b",
]

PROBLEM_PATTERNS = [
    r"\bproblem\b",
    r"\blose\b",
    r"\bstruggle\b",
    r"\bdifficult\b",
    r"\bmistake\b",
    r"\bissue\b",
    r"\battention\b",
    r"\bwaste\b",
]


def analyse_message(transcript: str) -> dict:
    """
    Analyse basic message clarity using transparent heuristics.
    """

    if not transcript.strip():
        return {
            "score": 0,
            "problem_detected": False,
            "value_detected": False,
            "message_length": 0,
            "clarity_label": "No message",
            "reasons": ["No transcript was available."],
        }

    text = transcript.lower()
    word_count = len(transcript.split())

    problem_detected = any(
        re.search(pattern, text)
        for pattern in PROBLEM_PATTERNS
    )

    value_detected = any(
        re.search(pattern, text)
        for pattern in VALUE_PATTERNS
    )

    score = 35
    reasons = []

    if problem_detected:
        score += 20
        reasons.append(
            "A clear audience problem or pain point is communicated."
        )
    else:
        reasons.append(
            "No clear problem or pain point was detected."
        )

    if value_detected:
        score += 25
        reasons.append(
            "The video communicates a value or improvement."
        )
    else:
        reasons.append(
            "The value proposition could be made more explicit."
        )

    if 15 <= word_count <= 80:
        score += 15
        reasons.append(
            "Message length is concise enough for short-form content."
        )
    elif word_count > 80:
        reasons.append(
            "The spoken message may be too dense for short-form content."
        )

    if problem_detected and value_detected:
        score += 5

    score = min(score, 100)

    if score >= 80:
        label = "Very Clear"
    elif score >= 65:
        label = "Clear"
    elif score >= 45:
        label = "Moderate"
    else:
        label = "Unclear"

    return {
        "score": score,
        "problem_detected": problem_detected,
        "value_detected": value_detected,
        "message_length": word_count,
        "clarity_label": label,
        "reasons": reasons,
    }