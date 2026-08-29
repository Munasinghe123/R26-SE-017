from __future__ import annotations

import asyncio
import re
import time

from groq import AsyncGroq, Groq

from config.config import GROQ_API_KEY
from llm.provider import LLMResponse


class GroqProvider:
    provider_name = "groq"

    def __init__(
        self,
        api_key: str | None = None,
        client: Groq | None = None,
        async_client: AsyncGroq | None = None,
    ) -> None:
        self.api_key = api_key or GROQ_API_KEY
        self.client = client
        self.async_client = async_client

    def complete(
        self,
        *,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        response, latency_ms = self._create_completion_with_retry(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        message = response.choices[0].message
        usage = self._extract_usage(response)

        return LLMResponse(
            content=message.content or "",
            provider=self.provider_name,
            model=model,
            input_tokens=self._usage_value(usage, "prompt_tokens"),
            output_tokens=self._usage_value(usage, "completion_tokens"),
            total_tokens=self._usage_value(usage, "total_tokens"),
            latency_ms=latency_ms,
            raw_usage=usage,
        )

    async def acomplete(
        self,
        *,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        response, latency_ms = await self._acreate_completion_with_retry(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        message = response.choices[0].message
        usage = self._extract_usage(response)

        return LLMResponse(
            content=message.content or "",
            provider=self.provider_name,
            model=model,
            input_tokens=self._usage_value(usage, "prompt_tokens"),
            output_tokens=self._usage_value(usage, "completion_tokens"),
            total_tokens=self._usage_value(usage, "total_tokens"),
            latency_ms=latency_ms,
            raw_usage=usage,
        )

    def _create_completion_with_retry(
        self,
        *,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        max_attempts: int = 3,
    ):
        last_error = None

        for attempt in range(max_attempts):
            started_at = time.perf_counter()
            try:
                response = self._client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    max_completion_tokens=max_tokens,
                    messages=messages,
                )
                latency_ms = (time.perf_counter() - started_at) * 1000
                return response, latency_ms
            except Exception as exc:
                last_error = exc
                is_rate_limited = (
                    getattr(exc, "status_code", None) == 429
                    or exc.__class__.__name__ == "RateLimitError"
                )
                if not is_rate_limited or attempt == max_attempts - 1:
                    raise

                delay = self._extract_retry_delay(exc, attempt)
                if delay > 0:
                    time.sleep(delay)

        raise last_error

    async def _acreate_completion_with_retry(
        self,
        *,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        max_attempts: int = 3,
    ):
        last_error = None

        for attempt in range(max_attempts):
            started_at = time.perf_counter()
            try:
                response = await self._async_client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    max_completion_tokens=max_tokens,
                    messages=messages,
                )
                latency_ms = (time.perf_counter() - started_at) * 1000
                return response, latency_ms
            except Exception as exc:
                last_error = exc
                is_rate_limited = (
                    getattr(exc, "status_code", None) == 429
                    or exc.__class__.__name__ == "RateLimitError"
                )
                if not is_rate_limited or attempt == max_attempts - 1:
                    raise

                delay = self._extract_retry_delay(exc, attempt)
                if delay > 0:
                    await asyncio.sleep(delay)

        raise last_error

    @property
    def _client(self):
        if self.client is None:
            self.client = Groq(api_key=self.api_key)
        return self.client

    @property
    def _async_client(self):
        if self.async_client is None:
            self.async_client = AsyncGroq(api_key=self.api_key)
        return self.async_client

    @staticmethod
    def _extract_retry_delay(error: Exception, attempt: int) -> float:
        message = str(error)
        match = re.search(
            r"try again in ([0-9]+(?:\.[0-9]+)?)s",
            message,
            flags=re.IGNORECASE,
        )
        if match:
            return max(float(match.group(1)) + 0.5, 1.0)

        status_code = getattr(error, "status_code", None)
        if status_code == 429:
            return min(2 ** attempt, 12)

        return 0.0

    @staticmethod
    def _extract_usage(response) -> dict | None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return None
        if isinstance(usage, dict):
            return dict(usage)
        if hasattr(usage, "model_dump"):
            return usage.model_dump()
        if hasattr(usage, "dict"):
            return usage.dict()
        return {
            key: getattr(usage, key)
            for key in ("prompt_tokens", "completion_tokens", "total_tokens")
            if hasattr(usage, key)
        }

    @staticmethod
    def _usage_value(usage: dict | None, key: str) -> int | None:
        if not usage:
            return None
        value = usage.get(key)
        return value if isinstance(value, int) else None
