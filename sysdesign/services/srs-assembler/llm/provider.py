from __future__ import annotations

import os
import time
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
import httpx

logger = logging.getLogger("srs-assembler.llm")

MAX_RETRIES = 3
INITIAL_BACKOFF = 2.0
BACKOFF_FACTOR = 2.0
MAX_BACKOFF = 15.0
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: float | None = None


class LLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def acomplete(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        pass


class OpenRouterProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "openrouter"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://sysdesign.research",
            "X-Title": "SRS-Assembler-Agent",
        }

    def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        for attempt in range(1, MAX_RETRIES + 1):
            t0 = time.perf_counter()
            try:
                with httpx.Client(timeout=120.0) as client:
                    resp = client.post(url, headers=self._headers(), json=payload)

                    if resp.status_code in RETRY_STATUS_CODES and attempt < MAX_RETRIES:
                        retry_after = resp.headers.get("retry-after")
                        delay = (
                            float(retry_after)
                            if retry_after and retry_after.isdigit()
                            else min(INITIAL_BACKOFF * (BACKOFF_FACTOR ** (attempt - 1)), MAX_BACKOFF)
                        )
                        logger.warning(
                            f"[OpenRouter Retry] HTTP {resp.status_code} on attempt {attempt}/{MAX_RETRIES} "
                            f"for model '{model}'. Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        continue

                    resp.raise_for_status()
                    data = resp.json()

                latency_ms = (time.perf_counter() - t0) * 1000.0
                if "error" in data:
                    err_info = data.get("error", {})
                    err_msg = err_info.get("message", str(err_info)) if isinstance(err_info, dict) else str(err_info)
                    if attempt < MAX_RETRIES and any(kw in str(err_msg).lower() for kw in ("rate", "limit", "overload", "busy", "quota")):
                        delay = min(INITIAL_BACKOFF * (BACKOFF_FACTOR ** (attempt - 1)), MAX_BACKOFF)
                        logger.warning(
                            f"[OpenRouter Retry] API Error payload on attempt {attempt}/{MAX_RETRIES}: {err_msg}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        continue
                    raise RuntimeError(f"OpenRouter API Error: {err_msg}")

                choice = data.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content", "")
                usage = data.get("usage", {})

                return LLMResponse(
                    content=content,
                    provider="openrouter",
                    model=model,
                    input_tokens=usage.get("prompt_tokens"),
                    output_tokens=usage.get("completion_tokens"),
                    total_tokens=usage.get("total_tokens"),
                    latency_ms=latency_ms,
                )
            except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                if attempt < MAX_RETRIES:
                    delay = min(INITIAL_BACKOFF * (BACKOFF_FACTOR ** (attempt - 1)), MAX_BACKOFF)
                    logger.warning(
                        f"[OpenRouter Retry] Network error on attempt {attempt}/{MAX_RETRIES} "
                        f"({net_err.__class__.__name__}). Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"[OpenRouter] All {MAX_RETRIES} retry attempts failed for network error.")
                    raise net_err
            except httpx.HTTPStatusError as http_err:
                if http_err.response.status_code in RETRY_STATUS_CODES and attempt < MAX_RETRIES:
                    delay = min(INITIAL_BACKOFF * (BACKOFF_FACTOR ** (attempt - 1)), MAX_BACKOFF)
                    logger.warning(
                        f"[OpenRouter Retry] HTTP {http_err.response.status_code} on attempt {attempt}/{MAX_RETRIES}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"[OpenRouter] HTTP status {http_err.response.status_code} unrecoverable.")
                    raise http_err

        raise RuntimeError(f"OpenRouter complete failed after {MAX_RETRIES} attempts.")

    async def acomplete(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        for attempt in range(1, MAX_RETRIES + 1):
            t0 = time.perf_counter()
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    resp = await client.post(url, headers=self._headers(), json=payload)

                    if resp.status_code in RETRY_STATUS_CODES and attempt < MAX_RETRIES:
                        retry_after = resp.headers.get("retry-after")
                        delay = (
                            float(retry_after)
                            if retry_after and retry_after.isdigit()
                            else min(INITIAL_BACKOFF * (BACKOFF_FACTOR ** (attempt - 1)), MAX_BACKOFF)
                        )
                        logger.warning(
                            f"[OpenRouter Retry] HTTP {resp.status_code} on attempt {attempt}/{MAX_RETRIES} "
                            f"for model '{model}'. Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                        continue

                    resp.raise_for_status()
                    data = resp.json()

                latency_ms = (time.perf_counter() - t0) * 1000.0
                if "error" in data:
                    err_info = data.get("error", {})
                    err_msg = err_info.get("message", str(err_info)) if isinstance(err_info, dict) else str(err_info)
                    if attempt < MAX_RETRIES and any(kw in str(err_msg).lower() for kw in ("rate", "limit", "overload", "busy", "quota")):
                        delay = min(INITIAL_BACKOFF * (BACKOFF_FACTOR ** (attempt - 1)), MAX_BACKOFF)
                        logger.warning(
                            f"[OpenRouter Retry] API Error payload on attempt {attempt}/{MAX_RETRIES}: {err_msg}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                        continue
                    raise RuntimeError(f"OpenRouter API Error: {err_msg}")

                choice = data.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content", "")
                usage = data.get("usage", {})

                return LLMResponse(
                    content=content,
                    provider="openrouter",
                    model=model,
                    input_tokens=usage.get("prompt_tokens"),
                    output_tokens=usage.get("completion_tokens"),
                    total_tokens=usage.get("total_tokens"),
                    latency_ms=latency_ms,
                )
            except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                if attempt < MAX_RETRIES:
                    delay = min(INITIAL_BACKOFF * (BACKOFF_FACTOR ** (attempt - 1)), MAX_BACKOFF)
                    logger.warning(
                        f"[OpenRouter Retry] Network/Timeout error on attempt {attempt}/{MAX_RETRIES} "
                        f"({net_err.__class__.__name__}). Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"[OpenRouter] All {MAX_RETRIES} retry attempts failed for network error.")
                    raise net_err
            except httpx.HTTPStatusError as http_err:
                if http_err.response.status_code in RETRY_STATUS_CODES and attempt < MAX_RETRIES:
                    delay = min(INITIAL_BACKOFF * (BACKOFF_FACTOR ** (attempt - 1)), MAX_BACKOFF)
                    logger.warning(
                        f"[OpenRouter Retry] HTTP {http_err.response.status_code} on attempt {attempt}/{MAX_RETRIES}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"[OpenRouter] HTTP status {http_err.response.status_code} unrecoverable.")
                    raise http_err

        raise RuntimeError(f"OpenRouter acomplete failed after {MAX_RETRIES} attempts.")

