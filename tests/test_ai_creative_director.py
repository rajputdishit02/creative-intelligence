import json

import httpx2
from openai import APITimeoutError, AuthenticationError, BadRequestError, NotFoundError

from src.ai.creative_director import (
    check_ai_connectivity,
    check_openai_connectivity,
    generate_creative_review,
    get_provider,
)
from src.ai.payload import build_creative_review_payload, payload_fingerprint
from src.ai.schemas import parse_review_json, validate_creative_review


def _valid_review():
    return {
        "summary": "A concise review for the selected campaign and platform.",
        "what_works": [
            "The format aligns with the selected platform.",
            "The visual quality is consistent.",
            "The CTA timing is structurally clear.",
        ],
        "priority_improvements": [
            {
                "priority": "medium",
                "area": "pacing",
                "recommendation": "Add one meaningful visual change near the midpoint.",
                "evidence": "Only one scene was detected across the clip.",
            }
        ],
        "hook_review": {
            "current_hook": "Need better video results?",
            "assessment": "The hook is direct and easy to understand.",
            "alternatives": [
                {"style": "direct", "text": "Stop wasting your best video ideas."},
                {"style": "curiosity", "text": "What makes one marketing video clearer than another?"},
                {"style": "problem-led", "text": "If your message feels buried, start here."},
            ],
        },
        "cta_review": {
            "current_cta": "Learn more",
            "assessment": "The CTA is clear and suitable for a soft action.",
            "alternatives": [
                "Explore the campaign.",
                "Learn more today.",
                "Follow for more examples.",
            ],
        },
        "suggested_structure": [
            {
                "section": "Hook",
                "start": 0.0,
                "end": 3.0,
                "purpose": "Introduce the main problem quickly.",
            },
            {
                "section": "Value",
                "start": 3.0,
                "end": 10.0,
                "purpose": "Show the practical benefit.",
            },
        ],
        "platform_advice": [
            "Keep the opening visually clear for the selected platform.",
            "Use the existing vertical framing consistently.",
        ],
        "final_takeaway": "Keep the message clear and add one stronger visual change.",
    }


def _payload(transcript_text="Need better video results? Learn more."):
    return build_creative_review_payload(
        client_name="Example client",
        campaign_name="Launch",
        objective="Brand Awareness",
        target_platform="Instagram Reels",
        video_metadata={
            "duration": 12,
            "resolution": "1080 x 1920",
            "width": 1080,
            "height": 1920,
            "fps": 30,
            "aspect_ratio": "9:16",
            "orientation": "Vertical",
            "file_size_mb": 4.2,
        },
        transcript={
            "transcript": transcript_text,
            "confidence": 0.94,
        },
        speech_analysis={
            "word_count": 6,
            "words_per_minute": 120,
            "speech_rate": "Conversational",
        },
        hook_analysis={
            "hook_text": "Need better video results?",
            "score": 85,
            "hook_type": "Question",
            "hook_start": 0,
            "hook_end": 2.1,
            "reasons": ["Speech begins early."],
        },
        cta_analysis={
            "cta_detected": True,
            "cta_text": "Learn more",
            "score": 80,
            "cta_start": 9.0,
            "cta_position": "Final section",
        },
        message_analysis={
            "score": 75,
            "clarity_label": "Clear",
            "problem_detected": True,
            "value_detected": True,
            "reasons": ["The message communicates a value."],
        },
        story_analysis={
            "score": 100,
            "label": "Complete",
            "components": {
                "hook": True,
                "problem": True,
                "value": True,
                "cta": True,
            },
            "missing": [],
        },
        scene_analysis={
            "scene_count": 1,
        },
        pacing_analysis={
            "average_scene_duration": 12,
            "scenes_per_minute": 5,
            "pacing_label": "Slow",
        },
        visual_quality={
            "score": 84,
            "sharpness_score": 90,
            "exposure_score": 80,
            "contrast_score": 85,
            "consistency_score": 82,
            "warnings": [],
        },
        motion_analysis={
            "motion_level": "Low movement",
            "warnings": ["The video remains visually static for long periods."],
        },
        technical_quality={
            "score": 90,
            "label": "Excellent",
            "reasons": ["Resolution supports a high-quality export."],
        },
        platform_fit={
            "score": 100,
            "platform": "Instagram Reels",
            "label": "Excellent",
            "reasons": ["9:16 aspect ratio matches platform guidance."],
        },
        objective_analysis={
            "score": 82,
            "objective": "Brand Awareness",
        },
        creative_score={
            "score": 84,
            "label": "Strong",
            "weights": {"visual_quality": 0.15},
            "components": {"visual_quality": 84},
        },
        recommendations=[
            {
                "area": "Visual activity",
                "priority": "Low",
                "recommendation": "Add a cutaway.",
            }
        ],
    )


class _FakeResponse:
    def __init__(self, output_text):
        self.output_text = output_text


class _FakeResponses:
    def __init__(self, output_text=None, error=None):
        self.output_text = output_text
        self.error = error

    def create(self, **kwargs):
        if self.error:
            raise self.error

        return _FakeResponse(self.output_text)


class _FakeClient:
    def __init__(self, output_text=None, error=None):
        self.responses = _FakeResponses(output_text=output_text, error=error)


class _FakeGeminiResponse:
    def __init__(self, text):
        self.text = text


class _FakeGeminiModels:
    def __init__(self, text=None, error=None):
        self.text = text
        self.error = error

    def generate_content(self, **kwargs):
        if self.error:
            raise self.error

        return _FakeGeminiResponse(self.text)


class _FakeGeminiClient:
    def __init__(self, text=None, error=None):
        self.models = _FakeGeminiModels(text=text, error=error)


class _GeminiError(Exception):
    def __init__(self, status_code=None, code=None, message="safe test error"):
        super().__init__(message)
        self.status_code = status_code
        self.code = code


def _openai_error(error_type, status_code=400):
    request = httpx2.Request("POST", "https://api.openai.com/v1/responses")
    response = httpx2.Response(status_code, request=request)

    return error_type("safe test error", response=response, body=None)


def test_creative_review_payload_generation_includes_expected_sections():
    payload = _payload()

    assert payload["campaign"]["objective"] == "Brand Awareness"
    assert payload["transcript"]["available"] is True
    assert payload["visual"]["motion_level"] == "Low movement"
    assert "full_transcript" in payload["transcript"]


def test_payload_generation_handles_empty_transcript_and_missing_optional_fields():
    payload = build_creative_review_payload(
        client_name="",
        campaign_name="",
        objective="Engagement",
        target_platform="TikTok",
        video_metadata={},
        transcript=None,
        speech_analysis=None,
        hook_analysis=None,
        cta_analysis=None,
        message_analysis=None,
        story_analysis=None,
        scene_analysis={},
        pacing_analysis={},
        visual_quality={},
        motion_analysis={},
        technical_quality={},
        platform_fit={},
        objective_analysis={},
        creative_score={},
        recommendations=[],
    )

    assert payload["transcript"]["available"] is False
    assert payload["hook"]["score"] == 0
    assert payload["cta"]["detected"] is False


def test_parse_review_json_rejects_malformed_input():
    try:
        parse_review_json("{not json")
    except ValueError as error:
        assert "valid JSON" in str(error)
    else:
        raise AssertionError("Malformed JSON should fail validation.")


def test_schema_validation_rejects_invalid_priority():
    review = _valid_review()
    review["priority_improvements"][0]["priority"] = "urgent"

    try:
        validate_creative_review(review, video_duration=12)
    except ValueError as error:
        assert "invalid priority" in str(error)
    else:
        raise AssertionError("Invalid priority should fail validation.")


def test_schema_validation_rejects_invalid_timestamps():
    review = _valid_review()
    review["suggested_structure"][0]["end"] = 99

    try:
        validate_creative_review(review, video_duration=12)
    except ValueError as error:
        assert "video duration" in str(error)
    else:
        raise AssertionError("Invalid timestamp should fail validation.")


def test_provider_selection_defaults_to_gemini(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    provider = get_provider()

    assert provider.name == "gemini"


def test_openai_provider_still_importable_and_selectable():
    provider = get_provider(provider_name="openai", model="test-model")

    assert provider.name == "openai"
    assert provider.model == "test-model"


def test_no_key_fallback_does_not_call_api(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = generate_creative_review(_payload(), provider_name="gemini")

    assert result["success"] is False
    assert result["error_category"] == "missing_api_key"


def test_api_failure_fallback_is_user_safe():
    result = generate_creative_review(
        _payload(),
        client=_FakeClient(error=RuntimeError("network exploded")),
        model="test-model",
        provider_name="openai",
    )

    assert result["success"] is False
    assert "deterministic video analysis is still complete" in result["error"]
    assert result["error_category"] == "unknown_api_error"


def test_authentication_failure_is_categorized():
    result = generate_creative_review(
        _payload(),
        client=_FakeClient(error=_openai_error(AuthenticationError, 401)),
        model="test-model",
        provider_name="openai",
    )

    assert result["success"] is False
    assert result["error_category"] == "authentication_failure"
    assert "authentication problem" in result["error"]


def test_unavailable_model_is_categorized():
    result = generate_creative_review(
        _payload(),
        client=_FakeClient(error=_openai_error(NotFoundError, 404)),
        model="missing-model",
        provider_name="openai",
    )

    assert result["success"] is False
    assert result["error_category"] == "model_not_found_or_unavailable"


def test_timeout_is_categorized():
    request = httpx2.Request("POST", "https://api.openai.com/v1/responses")
    result = generate_creative_review(
        _payload(),
        client=_FakeClient(error=APITimeoutError(request)),
        model="test-model",
        provider_name="openai",
    )

    assert result["success"] is False
    assert result["error_category"] == "timeout"


def test_malformed_request_is_categorized():
    result = generate_creative_review(
        _payload(),
        client=_FakeClient(error=_openai_error(BadRequestError, 400)),
        model="test-model",
        provider_name="openai",
    )

    assert result["success"] is False
    assert result["error_category"] == "malformed_request"


def test_connectivity_check_uses_safe_categories(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = check_ai_connectivity(provider_name="gemini")

    assert result["success"] is False
    assert result["error_category"] == "missing_api_key"


def test_mocked_successful_ai_response_is_validated():
    review = _valid_review()
    result = generate_creative_review(
        _payload(),
        client=_FakeClient(output_text=json.dumps(review)),
        model="test-model",
        provider_name="openai",
    )

    assert result["success"] is True
    assert result["review"]["summary"] == review["summary"]


def test_validation_failure_is_categorized():
    review = _valid_review()
    review["suggested_structure"][0]["end"] = 99

    result = generate_creative_review(
        _payload(),
        client=_FakeClient(output_text=json.dumps(review)),
        model="test-model",
        provider_name="openai",
    )

    assert result["success"] is False
    assert result["error_category"] == "structured_response_validation_failed"


def test_gemini_success_is_validated():
    review = _valid_review()
    result = generate_creative_review(
        _payload(),
        client=_FakeGeminiClient(text=json.dumps(review)),
        model="gemini-test-model",
        provider_name="gemini",
    )

    assert result["success"] is True
    assert result["provider"] == "gemini"
    assert result["review"]["summary"] == review["summary"]


def test_gemini_quota_error_is_categorized():
    result = generate_creative_review(
        _payload(),
        client=_FakeGeminiClient(error=_GeminiError(status_code=429)),
        model="gemini-test-model",
        provider_name="gemini",
    )

    assert result["success"] is False
    assert result["error_category"] == "rate_limit_or_quota"


def test_gemini_model_unavailable_error_is_categorized():
    result = generate_creative_review(
        _payload(),
        client=_FakeGeminiClient(error=_GeminiError(code="404")),
        model="missing-gemini-model",
        provider_name="gemini",
    )

    assert result["success"] is False
    assert result["error_category"] == "model_not_found_or_unavailable"


def test_gemini_network_error_is_categorized():
    class ConnectError(Exception):
        pass

    result = generate_creative_review(
        _payload(),
        client=_FakeGeminiClient(error=ConnectError("safe connection issue")),
        model="gemini-test-model",
        provider_name="gemini",
    )

    assert result["success"] is False
    assert result["error_category"] == "network_error"


def test_gemini_malformed_response_is_categorized():
    result = generate_creative_review(
        _payload(),
        client=_FakeGeminiClient(text="{not json"),
        model="gemini-test-model",
        provider_name="gemini",
    )

    assert result["success"] is False
    assert result["error_category"] == "json_parsing_problem"


def test_openai_connectivity_wrapper_selects_openai(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = check_openai_connectivity(model="test-model")

    assert result["provider"] == "openai"
    assert result["error_category"] == "missing_api_key"


def test_payload_fingerprint_changes_when_inputs_change():
    first = _payload("First transcript.")
    second = _payload("Second transcript.")

    assert payload_fingerprint(first) != payload_fingerprint(second)
