import base64
from dataclasses import dataclass
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
from app.transcription.provider_schema import GEMINI_PROVIDER_JSON_SCHEMA


@dataclass(frozen=True)
class GeminiModelConfiguration:
    pricing_version: str
    input_usd_per_million: Decimal
    output_usd_per_million: Decimal


GEMINI_MODELS = {
    "gemini-3.5-flash-lite": GeminiModelConfiguration(
        pricing_version="gemini-3.5-flash-lite-2026-08-28",
        input_usd_per_million=Decimal("0.30"),
        output_usd_per_million=Decimal("2.50"),
    ),
    "gemini-3.5-flash": GeminiModelConfiguration(
        pricing_version="gemini-3.5-flash-2026-08-27",
        input_usd_per_million=Decimal("1.50"),
        output_usd_per_million=Decimal("9.00"),
    ),
}


class GeminiTranscriptionProvider(StrictTranscriptionProvider):
    def __init__(
        self,
        *,
        api_key: str,
        model_snapshot: str,
        client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 60,
    ) -> None:
        try:
            model = GEMINI_MODELS[model_snapshot]
        except KeyError as error:
            raise ValueError("Gemini transcription model is not approved") from error
        super().__init__(
            ConfiguredProviderIdentity(
                provider="google-gemini",
                model_snapshot=model_snapshot,
                prompt_version=PROMPT_VERSION,
                prompt_hash=PROMPT_HASH,
                schema_version=PROVIDER_SCHEMA_VERSION,
                pricing_version=model.pricing_version,
                input_usd_per_million=model.input_usd_per_million,
                output_usd_per_million=model.output_usd_per_million,
            )
        )
        self._api_key = api_key
        self._client = client
        self._timeout_seconds = timeout_seconds

    async def _invoke(self, request: ProviderRequest, *, repair_schema: bool) -> ProviderCall:
        body: dict[str, object] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": provider_instruction(
                                request.problem_context,
                                repair_schema=repair_schema,
                            )
                        },
                        {
                            "inlineData": {
                                "mimeType": request.content_type,
                                "data": base64.b64encode(request.image_bytes).decode("ascii"),
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 3_000,
                "responseMimeType": "application/json",
                "responseJsonSchema": GEMINI_PROVIDER_JSON_SCHEMA,
            },
        }
        envelope, latency_ms = await post_provider_json(
            client=self._client,
            url=(
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self.identity.model_snapshot}:generateContent"
            ),
            headers={"x-goog-api-key": self._api_key},
            body=body,
            timeout_seconds=self._timeout_seconds,
        )
        try:
            candidate = required_object(required_list(envelope.get("candidates"))[0])
            content = required_object(candidate.get("content"))
            part = required_object(required_list(content.get("parts"))[0])
            text = required_text(part.get("text"))
            usage = required_object(envelope.get("usageMetadata"))
            input_tokens = usage_integer(usage.get("promptTokenCount"))
            output_tokens = usage_integer(usage.get("candidatesTokenCount"))
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
