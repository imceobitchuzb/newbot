"""OpenAI-compatible AI Provider implementation."""
import json
import logging
import re
from typing import Any, Dict, List, Optional
import httpx

from backend.app.core.config import settings
from backend.app.services.ai.base import (
    AIProviderError,
    AIProviderInvalidResponseError,
    AIProviderNotConfiguredError,
    AIProviderRateLimitError,
    AIProviderResponse,
    AIProviderTimeoutError,
    BaseAIProvider,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    """Production provider using OpenAI Chat Completions API or compatible base URL."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or settings.AI_API_KEY
        self.model = model or settings.AI_MODEL or "gpt-4o-mini"
        self.base_url = (base_url or settings.AI_BASE_URL or "https://api.openai.com/v1").rstrip("/")
        self.timeout = timeout

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def _extract_json_payload(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract structured JSON from model output."""
        text = text.strip()
        # Direct parse attempt
        try:
            return json.loads(text)
        except Exception:
            pass

        # Check for ```json ... ``` codeblock
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        # Check for any { ... } block
        match_braces = re.search(r"(\{.*\})", text, re.DOTALL)
        if match_braces:
            try:
                return json.loads(match_braces.group(1))
            except Exception:
                pass

        return None

    async def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        mode: str = "HINT",
        user_context: Optional[Dict[str, Any]] = None,
    ) -> AIProviderResponse:
        if not self.is_configured():
            raise AIProviderNotConfiguredError("AI Tutor is not configured.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Format chat history for OpenAI
        api_messages = [{"role": "system", "content": system_prompt}]
        for m in messages:
            api_messages.append({"role": m["role"], "content": m["content"]})

        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": settings.AI_TEMPERATURE,
            "max_tokens": settings.AI_MAX_TOKENS,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            logger.error(f"AI Provider timeout: {exc}")
            raise AIProviderTimeoutError("AI Tutor request timed out.") from exc
        except httpx.RequestError as exc:
            logger.error(f"AI Provider request error: {exc}")
            raise AIProviderError(f"Network error connecting to AI provider: {exc}") from exc

        if response.status_code == 429:
            raise AIProviderRateLimitError("AI Provider rate limit reached.")
        elif response.status_code == 401 or response.status_code == 403:
            raise AIProviderNotConfiguredError("AI Provider authentication failed.")
        elif response.status_code >= 400:
            logger.error(f"AI Provider error {response.status_code}: {response.text}")
            raise AIProviderError(f"AI Provider error ({response.status_code}).")

        try:
            res_data = response.json()
            choice = res_data.get("choices", [{}])[0]
            raw_content = choice.get("message", {}).get("content", "")
            usage = res_data.get("usage", {})
            total_tokens = usage.get("total_tokens")
        except Exception as exc:
            raise AIProviderInvalidResponseError("Malformed response payload from AI provider.") from exc

        parsed = self._extract_json_payload(raw_content)
        if not parsed:
            # Fallback gracefully with raw content
            return AIProviderResponse(
                message=raw_content.strip() or "No response generated.",
                mode=mode,
                actions=[],
                suggested_skill=None,
                suggested_technique=None,
                model=self.model,
                token_count=total_tokens,
            )

        # Build clean response object
        message_text = parsed.get("message") or parsed.get("explanation") or raw_content
        actions_list = parsed.get("actions", [])
        if not isinstance(actions_list, list):
            actions_list = []

        return AIProviderResponse(
            message=message_text,
            mode=parsed.get("mode", mode),
            actions=actions_list,
            suggested_skill=parsed.get("suggested_skill"),
            suggested_technique=parsed.get("suggested_technique"),
            model=self.model,
            token_count=total_tokens,
        )
