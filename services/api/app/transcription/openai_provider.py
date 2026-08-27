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

OPENAI_MODEL = "gpt-5.4-2026-03-05"


class OpenAITranscriptionProvider(StrictTranscriptionProvider):
    def __init__(
        self,
        *,
        api_key: str,
        client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 60,
    ) -> None:
        super().__init__(
            ConfiguredProviderIdentity(
                provider="openai",
                model_snapshot=OPENAI_MODEL,
                prompt_version=PROMPT_VERSION,
                prompt_hash=PROMPT_HASH,
                schema_version=PROVIDER_SCHEMA_VERSION,
                pricing_version="gpt-5.4-2026-08-27",
                input_usd_per_million=Decimal("2.50"),
                output_usd_per_million=Decimal("15.00"),
            )
        )
        self._api_key = api_key
        self._client = client
        self._timeout_seconds = timeout_seconds

    async def _invoke(self, request: ProviderRequest, *, repair_schema: bool) -> ProviderCall:
        image = base64.b64encode(request.image_bytes).decode("ascii")
        body: dict[str, object] = {
            "model": OPENAI_MODEL,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": provider_instruction(
                                request.problem_context,
                                repair_schema=repair_schema,
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:{request.content_type};base64,{image}",
                        },
                    ],
                }
            ],
            "max_output_tokens": 3_000,
            "reasoning": {"effort": "none"},
            "store": False,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "m6_provider_transcript",
                    "strict": True,
                    "schema": PROVIDER_JSON_SCHEMA,
                }
            },
        }
        envelope, latency_ms = await post_provider_json(
            client=self._client,
            url="https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {self._api_key}"},
            body=body,
            timeout_seconds=self._timeout_seconds,
        )
        try:
            output = required_object(required_list(envelope.get("output"))[0])
            content = required_object(required_list(output.get("content"))[0])
            if content.get("type") != "output_text":
                raise ValueError("OpenAI output content is not text")
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
