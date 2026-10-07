"""Base abstractions and schemas for AI Providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AIProviderError(Exception):
    """Base class for AI provider errors."""
    pass


class AIProviderNotConfiguredError(AIProviderError):
    """Raised when the AI provider or API key is not configured."""
    pass


class AIProviderTimeoutError(AIProviderError):
    """Raised when the AI provider request times out."""
    pass


class AIProviderRateLimitError(AIProviderError):
    """Raised when the AI provider returns a rate limit error."""
    pass


class AIProviderInvalidResponseError(AIProviderError):
    """Raised when the AI provider returns an invalid response."""
    pass


@dataclass
class TutorActionItem:
    type: str  # PRACTICE_SKILL, REVIEW_MISTAKE, OPEN_DESMOS, PRACTICE_ADAPTIVE, VIEW_DIAGNOSTIC
    title: str
    description: Optional[str] = None
    target_id: Optional[str] = None  # skill name, mistake_id, technique slug
    url: Optional[str] = None


@dataclass
class AIProviderResponse:
    message: str
    mode: str
    actions: List[Dict[str, Any]] = field(default_factory=list)
    suggested_skill: Optional[str] = None
    suggested_technique: Optional[str] = None
    model: Optional[str] = None
    token_count: Optional[int] = None


class BaseAIProvider(ABC):
    """Abstract interface for all LLM providers."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if the provider has all required credentials and is ready."""
        pass

    @abstractmethod
    async def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        mode: str = "HINT",
        user_context: Optional[Dict[str, Any]] = None,
    ) -> AIProviderResponse:
        """Generate a structured response for the SAT Tutor."""
        pass
