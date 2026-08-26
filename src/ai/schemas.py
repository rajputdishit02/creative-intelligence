import json


VALID_PRIORITIES = {"high", "medium", "low"}

CREATIVE_REVIEW_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "summary",
        "what_works",
        "priority_improvements",
        "hook_review",
        "cta_review",
        "suggested_structure",
        "platform_advice",
        "final_takeaway",
    ],
    "properties": {
        "summary": {"type": "string"},
        "what_works": {
            "type": "array",
            "minItems": 1,
            "maxItems": 5,
            "items": {"type": "string"},
        },
        "priority_improvements": {
            "type": "array",
            "minItems": 1,
            "maxItems": 5,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "priority",
                    "area",
                    "recommendation",
                    "evidence",
                ],
                "properties": {
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    },
                    "area": {"type": "string"},
                    "recommendation": {"type": "string"},
                    "evidence": {"type": "string"},
                },
            },
        },
        "hook_review": {
            "type": "object",
            "additionalProperties": False,
            "required": ["current_hook", "assessment", "alternatives"],
            "properties": {
                "current_hook": {"type": "string"},
                "assessment": {"type": "string"},
                "alternatives": {
                    "type": "array",
                    "minItems": 0,
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["style", "text"],
                        "properties": {
                            "style": {"type": "string"},
                            "text": {"type": "string"},
                        },
                    },
                },
            },
        },
        "cta_review": {
            "type": "object",
            "additionalProperties": False,
            "required": ["current_cta", "assessment", "alternatives"],
            "properties": {
                "current_cta": {"type": "string"},
                "assessment": {"type": "string"},
                "alternatives": {
                    "type": "array",
                    "minItems": 0,
                    "maxItems": 3,
                    "items": {"type": "string"},
                },
            },
        },
        "suggested_structure": {
            "type": "array",
            "minItems": 1,
            "maxItems": 6,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["section", "start", "end", "purpose"],
                "properties": {
                    "section": {"type": "string"},
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "purpose": {"type": "string"},
                },
            },
        },
        "platform_advice": {
            "type": "array",
            "minItems": 1,
            "maxItems": 5,
            "items": {"type": "string"},
        },
        "final_takeaway": {"type": "string"},
    },
}

CREATIVE_REVIEW_SCHEMA = {
    "type": "json_schema",
    "name": "creative_director_review",
    "strict": True,
    "schema": CREATIVE_REVIEW_JSON_SCHEMA,
}

def parse_review_json(raw_text: str) -> dict:
    if not raw_text or not raw_text.strip():
        raise ValueError("AI review response was empty.")

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as error:
        raise ValueError("AI review response was not valid JSON.") from error


def validate_creative_review(review: dict, video_duration: float) -> dict:
    if not isinstance(review, dict):
        raise ValueError("AI review must be a JSON object.")

    required_fields = [
        "summary",
        "what_works",
        "priority_improvements",
        "hook_review",
        "cta_review",
        "suggested_structure",
        "platform_advice",
        "final_takeaway",
    ]

    for field in required_fields:
        if field not in review:
            raise ValueError(f"AI review is missing required field: {field}.")

    if not isinstance(review["summary"], str):
        raise ValueError("AI review summary must be text.")

    for list_field in [
        "what_works",
        "priority_improvements",
        "suggested_structure",
        "platform_advice",
    ]:
        if not isinstance(review[list_field], list):
            raise ValueError(f"AI review field must be a list: {list_field}.")

    for improvement in review["priority_improvements"]:
        if not isinstance(improvement, dict):
            raise ValueError("Each priority improvement must be an object.")

        priority = improvement.get("priority")

        if priority not in VALID_PRIORITIES:
            raise ValueError("AI review contains an invalid priority value.")

        for field in ["area", "recommendation", "evidence"]:
            if not isinstance(improvement.get(field), str):
                raise ValueError(
                    f"Priority improvement field must be text: {field}."
                )

    _validate_hook_review(review["hook_review"])
    _validate_cta_review(review["cta_review"])
    _validate_structure(review["suggested_structure"], video_duration)

    if not all(isinstance(item, str) for item in review["what_works"]):
        raise ValueError("What works entries must be text.")

    if not all(isinstance(item, str) for item in review["platform_advice"]):
        raise ValueError("Platform advice entries must be text.")

    if not isinstance(review["final_takeaway"], str):
        raise ValueError("Final takeaway must be text.")

    return review


def _validate_hook_review(hook_review: dict) -> None:
    if not isinstance(hook_review, dict):
        raise ValueError("Hook review must be an object.")

    for field in ["current_hook", "assessment"]:
        if not isinstance(hook_review.get(field), str):
            raise ValueError(f"Hook review field must be text: {field}.")

    alternatives = hook_review.get("alternatives")

    if not isinstance(alternatives, list):
        raise ValueError("Hook alternatives must be a list.")

    for alternative in alternatives:
        if not isinstance(alternative, dict):
            raise ValueError("Each hook alternative must be an object.")

        if not isinstance(alternative.get("style"), str):
            raise ValueError("Hook alternative style must be text.")

        if not isinstance(alternative.get("text"), str):
            raise ValueError("Hook alternative text must be text.")


def _validate_cta_review(cta_review: dict) -> None:
    if not isinstance(cta_review, dict):
        raise ValueError("CTA review must be an object.")

    for field in ["current_cta", "assessment"]:
        if not isinstance(cta_review.get(field), str):
            raise ValueError(f"CTA review field must be text: {field}.")

    alternatives = cta_review.get("alternatives")

    if not isinstance(alternatives, list):
        raise ValueError("CTA alternatives must be a list.")

    if not all(isinstance(item, str) for item in alternatives):
        raise ValueError("CTA alternatives must be text.")


def _validate_structure(structure: list, video_duration: float) -> None:
    previous_end = 0.0
    duration = max(0.0, float(video_duration or 0))

    for section in structure:
        if not isinstance(section, dict):
            raise ValueError("Each suggested structure section must be an object.")

        for field in ["section", "purpose"]:
            if not isinstance(section.get(field), str):
                raise ValueError(
                    f"Suggested structure field must be text: {field}."
                )

        start = section.get("start")
        end = section.get("end")

        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            raise ValueError("Suggested structure timestamps must be numeric.")

        if start < 0 or end < 0 or start >= end:
            raise ValueError("Suggested structure timestamps are invalid.")

        if duration and end > duration:
            raise ValueError("Suggested structure exceeds the video duration.")

        if start + 0.25 < previous_end:
            raise ValueError("Suggested structure sections overlap too much.")

        previous_end = end
