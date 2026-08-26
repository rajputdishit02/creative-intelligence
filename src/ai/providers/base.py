from abc import ABC, abstractmethod


def failure_result(
    category: str,
    message: str,
    provider: str,
    model: str,
    review=None,
    details: str | None = None,
) -> dict:
    return {
        "success": False,
        "review": review,
        "error": message,
        "error_category": category,
        "details": details,
        "provider": provider,
        "model": model,
    }


def success_result(
    review: dict | None,
    provider: str,
    model: str,
) -> dict:
    return {
        "success": True,
        "review": review,
        "error": None,
        "error_category": None,
        "details": None,
        "provider": provider,
        "model": model,
    }


def safe_message(category: str) -> str:
    messages = {
        "missing_api_key": "AI review failed: provider API key is not configured.",
        "authentication_failure": "AI review failed: authentication problem.",
        "model_not_found_or_unavailable": (
            "AI review failed: configured model is unavailable."
        ),
        "permission_denied": "AI review failed: permission denied.",
        "rate_limit_or_quota": "AI review failed: rate limit or quota problem.",
        "malformed_request": "AI review failed: request format problem.",
        "malformed_ai_response": "AI review failed: malformed AI response.",
        "structured_response_validation_failed": (
            "AI review failed: structured response validation failed."
        ),
        "json_parsing_problem": "AI review failed: response JSON could not be parsed.",
        "timeout": "AI review failed: request timed out.",
        "network_error": "AI review failed: network connection problem.",
        "unknown_api_error": "AI review failed: unknown API error.",
    }

    suffix = " Your deterministic video analysis is still complete."

    return messages.get(category, messages["unknown_api_error"]) + suffix


def validation_error_category(error: ValueError) -> str:
    message = str(error).lower()

    if "json" in message:
        return "json_parsing_problem"

    return "structured_response_validation_failed"


class CreativeDirectorProvider(ABC):
    name: str

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def is_configured(self) -> bool:
        pass

    @abstractmethod
    def generate_review(self, payload: dict) -> dict:
        pass

    @abstractmethod
    def check_connectivity(self) -> dict:
        pass
