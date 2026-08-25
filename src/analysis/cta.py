import re


CTA_PATTERNS = [
    r"\bupload\b",
    r"\bbuy\b",
    r"\bshop\b",
    r"\bsign up\b",
    r"\bregister\b",
    r"\blearn more\b",
    r"\bcontact\b",
    r"\bbook\b",
    r"\bcall\b",
    r"\bvisit\b",
    r"\bclick\b",
    r"\bfollow\b",
    r"\bsubscribe\b",
    r"\bdownload\b",
    r"\btry\b",
    r"\bstart\b",
    r"\bget started\b",
    r"\bjoin\b",
    r"\bsave\b",
    r"\bshare\b",
]


def analyse_cta(words: list, video_duration: float) -> dict:
    """
    Detect likely spoken calls to action and estimate their timing.
    """

    if not words:
        return {
            "cta_detected": False,
            "cta_text": "",
            "cta_start": None,
            "cta_position": "Not detected",
            "score": 0,
        }

    transcript_words = [
        word["word"] for word in words
    ]

    transcript = " ".join(transcript_words)

    matched_pattern = None

    for pattern in CTA_PATTERNS:
        if re.search(pattern, transcript.lower()):
            matched_pattern = pattern
            break

    if not matched_pattern:
        return {
            "cta_detected": False,
            "cta_text": "",
            "cta_start": None,
            "cta_position": "Not detected",
            "score": 20,
        }

    # Find the first word matching a CTA keyword.
    cta_index = None

    clean_pattern = (
        matched_pattern
        .replace(r"\b", "")
        .replace("\\", "")
    )

    for index, word in enumerate(words):
        if clean_pattern.split()[0] in word["word"].lower():
            cta_index = index
            break

    if cta_index is None:
        cta_index = max(0, len(words) - 8)

    # Capture some surrounding CTA language.
    start_index = max(0, cta_index - 2)
    end_index = min(
        len(words),
        cta_index + 12
    )

    cta_words = words[start_index:end_index]

    cta_text = " ".join(
        word["word"] for word in cta_words
    )

    cta_start = words[cta_index]["start"]

    if video_duration > 0:
        relative_position = cta_start / video_duration
    else:
        relative_position = 1

    if relative_position < 0.35:
        position = "Early"
        score = 70
    elif relative_position <= 0.65:
        position = "Middle"
        score = 80
    else:
        position = "Final section"
        score = 85

    return {
        "cta_detected": True,
        "cta_text": cta_text,
        "cta_start": round(cta_start, 2),
        "cta_position": position,
        "score": score,
    }
