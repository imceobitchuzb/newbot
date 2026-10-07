"""Fake AI Provider for automated tests only.

This provider MUST NEVER be used in production.
"""
from typing import Any, Dict, List, Optional
from backend.app.services.ai.base import (
    AIProviderError,
    AIProviderInvalidResponseError,
    AIProviderNotConfiguredError,
    AIProviderRateLimitError,
    AIProviderResponse,
    AIProviderTimeoutError,
    BaseAIProvider,
)


class FakeAIProvider(BaseAIProvider):
    """Deterministic test provider for backend unit & integration tests."""

    def __init__(
        self,
        configured: bool = True,
        simulate_timeout: bool = False,
        simulate_rate_limit: bool = False,
        simulate_error: bool = False,
        simulate_invalid_response: bool = False,
        custom_message: Optional[str] = None,
        custom_actions: Optional[List[Dict[str, Any]]] = None,
    ):
        self._configured = configured
        self.simulate_timeout = simulate_timeout
        self.simulate_rate_limit = simulate_rate_limit
        self.simulate_error = simulate_error
        self.simulate_invalid_response = simulate_invalid_response
        self.custom_message = custom_message
        self.custom_actions = custom_actions

    def is_configured(self) -> bool:
        return self._configured

    async def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        mode: str = "HINT",
        user_context: Optional[Dict[str, Any]] = None,
    ) -> AIProviderResponse:
        if not self._configured:
            raise AIProviderNotConfiguredError("AI Tutor is not configured.")

        if self.simulate_timeout:
            raise AIProviderTimeoutError("Simulated AI provider timeout.")

        if self.simulate_rate_limit:
            raise AIProviderRateLimitError("Simulated AI provider rate limit reached.")

        if self.simulate_error:
            raise AIProviderError("Simulated provider failure.")

        if self.simulate_invalid_response:
            raise AIProviderInvalidResponseError("Simulated invalid JSON response.")

        # Default deterministic reply according to mode
        last_msg = messages[-1]["content"] if messages else ""
        if self.custom_message:
            msg = self.custom_message
        elif mode == "HINT":
            msg = f"Step 1: Identify the key variable in the equation. Do not solve fully yet."
        elif mode == "EXPLANATION":
            msg = f"Here is why: First we isolate the term, then apply the quadratic formula."
        elif mode == "SOLUTION":
            msg = f"Complete step-by-step solution for the problem."
        elif mode == "DESMOS_HELP":
            msg = f"Type the equation directly into line 1 in Desmos and inspect the x-intercepts."
        elif mode == "CONCEPT":
            msg = f"This concept tests fundamental algebraic structures and proportional relationships."
        else:
            msg = f"I am your SAT Tutor. You asked: '{last_msg}'. Let's break this down together."

        actions = self.custom_actions or [
            {
                "type": "PRACTICE_SKILL",
                "title": "Practice Linear Equations",
                "target_id": "Linear equations in one variable",
                "url": "/math",
            }
        ]

        return AIProviderResponse(
            message=msg,
            mode=mode,
            actions=actions,
            suggested_skill="Linear equations in one variable",
            suggested_technique="intersection",
            model="fake-test-model",
            token_count=120,
        )
