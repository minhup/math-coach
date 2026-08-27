import json
from time import perf_counter
from typing import Any

import httpx

from app.transcription.provider import ProviderPermanentError, ProviderTransportError


def required_object(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError("Provider envelope is not an object")
    return value


def required_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("Provider envelope field is not a list")
    return value


def required_text(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("Provider envelope field is not text")
    return value


def usage_integer(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("Provider usage is invalid")
    return value


def structured_payload(text: str) -> object:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


async def post_provider_json(
    *,
    client: httpx.AsyncClient | None,
    url: str,
    headers: dict[str, str],
    body: dict[str, object],
    timeout_seconds: float,
) -> tuple[dict[str, Any], int]:
    started = perf_counter()
    try:
        if client is None:
            async with httpx.AsyncClient(timeout=timeout_seconds) as owned_client:
                response = await owned_client.post(url, headers=headers, json=body)
        else:
            response = await client.post(
                url,
                headers=headers,
                json=body,
                timeout=timeout_seconds,
            )
    except httpx.TimeoutException as error:
        raise ProviderTransportError("timeout") from error
    except httpx.RequestError as error:
        raise ProviderTransportError("transport_failed") from error
    latency_ms = max(0, round((perf_counter() - started) * 1000))
    if response.status_code == 429:
        raise ProviderTransportError("rate_limited")
    if response.status_code in {408, 504}:
        raise ProviderTransportError("timeout")
    if response.status_code >= 500:
        raise ProviderTransportError("transport_failed")
    if response.status_code >= 400:
        raise ProviderPermanentError("provider_rejected")
    try:
        return required_object(response.json()), latency_ms
    except (ValueError, json.JSONDecodeError):
        return {}, latency_ms
