import os

from google import genai
from google.genai import errors

from src.ai.prompts import SYSTEM_PROMPT, build_user_prompt
from src.ai.providers.base import (
    CreativeDirectorProvider,
    failure_result,
    safe_message,
    success_result,
    validation_error_category,
)
from src.ai.schemas import (
    CREATIVE_REVIEW_JSON_SCHEMA,
    parse_review_json,
    validate_creative_review,
)


class GeminiProvider(CreativeDirectorProvider):
    name = "gemini"

    def __init__(self, model: str, client=None):
        super().__init__(model)
        self.client = client

    def is_configured(self) -> bool:
        return bool(os.getenv("GEMINI_API_KEY", "").strip())

    def check_connectivity(self) -> dict:
        if self.client is None and not self.is_configured():
            return failure_result(
                category="missing_api_key",
                message=safe_message("missing_api_key"),
                provider=self.name,
                model=self.model,
            )

        try:
            client = self.client or self._client()
            response = client.models.generate_content(
                model=self.model,
                contents="Return only the word ok.",
            )

            if not getattr(response, "text", None):
                return failure_result(
                    category="malformed_ai_response",
                    message=safe_message("malformed_ai_response"),
                    provider=self.name,
                    model=self.model,
                )

            return success_result(
                review=None,
                provider=self.name,
                model=self.model,
            )

        except Exception as error:
            return self._safe_error_result(error)

    def generate_review(self, payload: dict) -> dict:
        if self.client is None and not self.is_configured():
            return failure_result(
                category="missing_api_key",
                message=safe_message("missing_api_key"),
                provider=self.name,
                model=self.model,
            )

        duration = payload.get("video", {}).get("duration", 0)

        try:
            client = self.client or self._client()
            response = client.models.generate_content(
                model=self.model,
                contents=build_user_prompt(payload),
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "response_mime_type": "application/json",
                    "response_json_schema": CREATIVE_REVIEW_JSON_SCHEMA,
                    "temperature": 0.7,
                },
            )

            review = validate_creative_review(
                parse_review_json(_extract_response_text(response)),
                video_duration=duration,
            )

            return success_result(
                review=review,
                provider=self.name,
                model=self.model,
            )

        except ValueError as error:
            category = validation_error_category(error)

            return failure_result(
                category=category,
                message=safe_message(category),
                provider=self.name,
                model=self.model,
                details=str(error),
            )

        except Exception as error:
            return self._safe_error_result(error)

    def _client(self):
        return genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options={
                "timeout": 30000,
            },
        )

    def _safe_error_result(self, error: Exception) -> dict:
        category = _categorize_error(error)

        return failure_result(
            category=category,
            message=safe_message(category),
            provider=self.name,
            model=self.model,
            details=_safe_details(error),
        )


def _extract_response_text(response) -> str:
    text = getattr(response, "text", None)

    if text:
        return text

    raise ValueError("AI response did not include output text.")


def _categorize_error(error: Exception) -> str:
    status_code = getattr(error, "status_code", None)
    code = str(getattr(error, "code", "") or "").lower()
    message = str(error).lower()
    error_type = type(error).__name__.lower()

    if status_code in {401, 403} or code in {"401", "403"} or "api_key_invalid" in code:
        return "authentication_failure"

    if status_code == 404 or code == "404" or "not found" in message:
        return "model_not_found_or_unavailable"

    if (
        status_code == 429
        or code == "429"
        or "resource_exhausted" in message
        or "quota" in message
    ):
        return "rate_limit_or_quota"

    if status_code == 400 or code == "400":
        return "malformed_request"

    if isinstance(error, TimeoutError) or "timeout" in message:
        return "timeout"

    if (
        isinstance(error, ConnectionError)
        or "connection" in message
        or "connect" in error_type
    ):
        return "network_error"

    if isinstance(error, errors.APIError):
        return "unknown_api_error"

    return "unknown_api_error"


def _safe_details(error: Exception) -> str:
    status_code = getattr(error, "status_code", None)

    if status_code:
        return f"status_{status_code}"

    code = getattr(error, "code", None)

    if code:
        return str(code)

    return type(error).__name__
