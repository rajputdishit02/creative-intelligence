import os

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OpenAI,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
)

from src.ai.prompts import SYSTEM_PROMPT, build_user_prompt
from src.ai.providers.base import (
    CreativeDirectorProvider,
    failure_result,
    safe_message,
    success_result,
    validation_error_category,
)
from src.ai.schemas import (
    CREATIVE_REVIEW_SCHEMA,
    parse_review_json,
    validate_creative_review,
)


class OpenAIProvider(CreativeDirectorProvider):
    name = "openai"

    def __init__(self, model: str, client=None):
        super().__init__(model)
        self.client = client

    def is_configured(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY", "").strip())

    def check_connectivity(self) -> dict:
        if self.client is None and not self.is_configured():
            return failure_result(
                category="missing_api_key",
                message=safe_message("missing_api_key"),
                provider=self.name,
                model=self.model,
            )

        try:
            client = self.client or OpenAI(timeout=20)
            response = client.responses.create(
                model=self.model,
                input="Return only the word ok.",
                max_output_tokens=32,
            )

            if not getattr(response, "output_text", None):
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

        except OpenAIError as error:
            return self._safe_error_result(error)

        except Exception as error:
            return failure_result(
                category="unknown_api_error",
                message=safe_message("unknown_api_error"),
                provider=self.name,
                model=self.model,
                details=type(error).__name__,
            )

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
            client = self.client or OpenAI(timeout=30)
            response = client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": build_user_prompt(payload),
                    },
                ],
                text={
                    "format": CREATIVE_REVIEW_SCHEMA,
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

        except OpenAIError as error:
            return self._safe_error_result(error)

        except Exception as error:
            return failure_result(
                category="unknown_api_error",
                message=safe_message("unknown_api_error"),
                provider=self.name,
                model=self.model,
                details=type(error).__name__,
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
    output_text = getattr(response, "output_text", None)

    if output_text:
        return output_text

    output = getattr(response, "output", None) or []

    for item in output:
        content = getattr(item, "content", None) or []

        for part in content:
            text = getattr(part, "text", None)

            if text:
                return text

    raise ValueError("AI response did not include output text.")


def _categorize_error(error: Exception) -> str:
    if isinstance(error, AuthenticationError):
        return "authentication_failure"

    if isinstance(error, NotFoundError):
        return "model_not_found_or_unavailable"

    if isinstance(error, PermissionDeniedError):
        return "permission_denied"

    if isinstance(error, RateLimitError):
        return "rate_limit_or_quota"

    if isinstance(error, BadRequestError):
        return "malformed_request"

    if isinstance(error, APITimeoutError) or isinstance(error, TimeoutError):
        return "timeout"

    if isinstance(error, APIConnectionError):
        return "network_error"

    return "unknown_api_error"


def _safe_details(error: Exception) -> str:
    code = getattr(error, "code", None)

    if code:
        return str(code)

    return type(error).__name__
