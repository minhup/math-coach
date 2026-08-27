import base64
from decimal import Decimal

import httpx

from app.transcription.http_provider import (
    post_provider_json,
    required_list,
    required_object,
    required_text,
    structured_payload,
    usage_integer,
)
from app.transcription.prompt import (
    PROMPT_HASH,
    PROMPT_VERSION,
    PROVIDER_SCHEMA_VERSION,
    provider_instruction,
)
from app.transcription.provider import (
    ConfiguredProviderIdentity,
    ProviderCall,
    ProviderRequest,
    StrictTranscriptionProvider,
)
from app.transcription.provider_schema import PROVIDER_JSON_SCHEMA

ANTHROPIC_MODEL = "claude-sonnet-5"


class AnthropicTranscriptionProvider(StrictTranscriptionProvider):
    def __init__(
        self,
        *,
        api_key: str,
        client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 60,
    ) -> None:
        super().__init__(
            ConfiguredProviderIdentity(
                provider="anthropic",
                model_snapshot=ANTHROPIC_MODEL,
                prompt_version=PROMPT_VERSION,
                prompt_hash=PROMPT_HASH,
                schema_version=PROVIDER_SCHEMA_VERSION,
                pricing_version="claude-sonnet-5-2026-08-27",
                input_usd_per_million=Decimal("2.00"),
                output_usd_per_million=Decimal("10.00"),
            )
        )
        self._api_key = api_key
        self._client = client
        self._timeout_seconds = timeout_seconds

    async def _invoke(self, request: ProviderRequest, *, repair_schema: bool) -> ProviderCall:
        body: dict[str, object] = {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 3_000,
            "thinking": {"type": "disabled"},
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": request.content_type,
                                "data": base64.b64encode(request.image_bytes).decode("ascii"),
                            },
                        },
                        {
                            "type": "text",
                            "text": provider_instruction(
                                request.problem_context,
                                repair_schema=repair_schema,
                            ),
                        },
                    ],
                }
            ],
            "output_config": {"format": {"type": "json_schema", "schema": PROVIDER_JSON_SCHEMA}},
        }
        envelope, latency_ms = await post_provider_json(
            client=self._client,
            url="https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
            },
            body=body,
            timeout_seconds=self._timeout_seconds,
        )
        try:
            content = required_object(required_list(envelope.get("content"))[0])
            if content.get("type") != "text":
                raise ValueError("Anthropic output content is not text")
            text = required_text(content.get("text"))
            usage = required_object(envelope.get("usage"))
            input_tokens = usage_integer(usage.get("input_tokens"))
            output_tokens = usage_integer(usage.get("output_tokens"))
        except (IndexError, ValueError):
            text = ""
            input_tokens = 0
            output_tokens = 0
        return ProviderCall(
            payload=structured_payload(text),
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
