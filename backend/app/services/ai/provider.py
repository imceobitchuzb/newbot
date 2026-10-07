"""AI Provider registry and factory."""
from typing import Optional

from backend.app.services.ai.base import BaseAIProvider
from backend.app.services.ai.openai_provider import OpenAIProvider

_active_provider: Optional[BaseAIProvider] = None


def get_ai_provider() -> BaseAIProvider:
    """Return the active AI provider singleton or default to OpenAIProvider."""
    global _active_provider
    if _active_provider is not None:
        return _active_provider
    return OpenAIProvider()


def set_ai_provider(provider: Optional[BaseAIProvider]) -> None:
    """Set custom or fake provider for testing/overriding."""
    global _active_provider
    _active_provider = provider


def reset_ai_provider() -> None:
    """Reset to default provider factory."""
    global _active_provider
    _active_provider = None
