import os

from dotenv import load_dotenv

from config.settings import (
    DEFAULT_AI_PROVIDER,
    DEFAULT_GEMINI_CREATIVE_DIRECTOR_MODEL,
    DEFAULT_OPENAI_CREATIVE_DIRECTOR_MODEL,
)
from src.ai.providers.gemini import GeminiProvider
from src.ai.providers.openai import OpenAIProvider

load_dotenv()


def get_ai_provider_name() -> str:
    return os.getenv("AI_PROVIDER", DEFAULT_AI_PROVIDER).strip().lower()


def get_ai_model(provider_name: str | None = None) -> str:
    provider = (provider_name or get_ai_provider_name()).strip().lower()

    if provider == "openai":
        return os.getenv(
            "OPENAI_CREATIVE_DIRECTOR_MODEL",
            DEFAULT_OPENAI_CREATIVE_DIRECTOR_MODEL,
        )

    return os.getenv(
        "GEMINI_CREATIVE_DIRECTOR_MODEL",
        DEFAULT_GEMINI_CREATIVE_DIRECTOR_MODEL,
    )


def is_openai_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def is_gemini_configured() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


def get_provider(
    provider_name: str | None = None,
    client=None,
    model: str | None = None,
):
    provider = (provider_name or get_ai_provider_name()).strip().lower()
    selected_model = model or get_ai_model(provider)

    if provider == "openai":
        return OpenAIProvider(model=selected_model, client=client)

    if provider == "gemini":
        return GeminiProvider(model=selected_model, client=client)

    raise ValueError(f"Unsupported AI provider: {provider}")


def get_ai_service_status() -> dict:
    provider = get_provider()

    return {
        "api_key_configured": provider.is_configured(),
        "provider": provider.name,
        "model": provider.model,
    }


def check_ai_connectivity(
    client=None,
    model: str | None = None,
    provider_name: str | None = None,
) -> dict:
    try:
        provider = get_provider(
            provider_name=provider_name,
            client=client,
            model=model,
        )
        return provider.check_connectivity()

    except Exception as error:
        provider = provider_name or get_ai_provider_name()

        return {
            "success": False,
            "review": None,
            "error": (
                "AI review failed: unknown API error. "
                "Your deterministic video analysis is still complete."
            ),
            "error_category": "unknown_api_error",
            "details": type(error).__name__,
            "provider": provider,
            "model": model or get_ai_model(provider),
        }


def check_openai_connectivity(
    client=None,
    model: str | None = None,
) -> dict:
    return check_ai_connectivity(
        client=client,
        model=model,
        provider_name="openai",
    )


def generate_creative_review(
    payload: dict,
    client=None,
    model: str | None = None,
    provider_name: str | None = None,
) -> dict:
    """
    Generate a structured AI Creative Director review using the configured provider.

    Returns a safe result wrapper so Streamlit can fail gracefully.
    """

    try:
        provider = get_provider(
            provider_name=provider_name,
            client=client,
            model=model,
        )
        return provider.generate_review(payload)

    except Exception as error:
        provider = provider_name or get_ai_provider_name()

        return {
            "success": False,
            "review": None,
            "error": (
                "AI review failed: unknown API error. "
                "Your deterministic video analysis is still complete."
            ),
            "error_category": "unknown_api_error",
            "details": type(error).__name__,
            "provider": provider,
            "model": model or get_ai_model(provider),
        }
