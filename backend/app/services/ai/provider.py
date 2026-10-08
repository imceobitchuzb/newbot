"""AI Provider registry and factory."""
from typing import Optional

from backend.app.services.ai.base import BaseAIProvider
from backend.app.services.ai.openai_provider import OpenAIProvider
from backend.app.services.ai.pedagogical_provider import PedagogicalSATProvider

_active_provider: Optional[BaseAIProvider] = None


def get_ai_provider() -> BaseAIProvider:
    """Return active AI provider singleton, OpenAIProvider if configured, or PedagogicalSATProvider."""
    global _active_provider
    if _active_provider is not None:
        return _active_provider
    openai_provider = OpenAIProvider()
    if openai_provider.is_configured():
        return openai_provider
    return PedagogicalSATProvider()


def set_ai_provider(provider: Optional[BaseAIProvider]) -> None:
    """Set custom or fake provider for testing/overriding."""
    global _active_provider
    _active_provider = provider


def reset_ai_provider() -> None:
    """Reset to default provider factory."""
    global _active_provider
    _active_provider = None
