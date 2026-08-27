from decimal import Decimal

from app.transcription.prompt import PROMPT_HASH, PROMPT_VERSION, PROVIDER_SCHEMA_VERSION
from app.transcription.provider import (
    ConfiguredProviderIdentity,
    ProviderCall,
    ProviderPermanentError,
    ProviderRequest,
    StrictTranscriptionProvider,
)

FAKE_MODEL = "m6-transcription-fixture-v1"


class DeterministicFakeTranscriptionProvider(StrictTranscriptionProvider):
    def __init__(self) -> None:
        super().__init__(
            ConfiguredProviderIdentity(
                provider="application-owned-deterministic-fake",
                model_snapshot=FAKE_MODEL,
                prompt_version=PROMPT_VERSION,
                prompt_hash=PROMPT_HASH,
                schema_version=PROVIDER_SCHEMA_VERSION,
                pricing_version="fake-zero-v1",
                input_usd_per_million=Decimal("0"),
                output_usd_per_million=Decimal("0"),
            )
        )

    async def _invoke(self, request: ProviderRequest, *, repair_schema: bool) -> ProviderCall:
        if not request.image_bytes:
            raise ProviderPermanentError("invalid_media")
        return ProviderCall(
            payload={
                "outcome": "ready",
                "blocks": [
                    {
                        "type": "text",
                        "text": "The synthetic draft gives the midpoint as ",
                        "sourceRegion": {"x": 0.08, "y": 0.12, "width": 0.62, "height": 0.1},
                    },
                    {
                        "type": "math",
                        "latex": "M=(2,0",
                        "sourceRegion": {"x": 0.12, "y": 0.28, "width": 0.32, "height": 0.12},
                    },
                    {
                        "type": "text",
                        "text": ". Review both the wording and mathematics before confirmation.",
                    },
                ],
                "warnings": [{"code": "low_confidence_math", "blockIndex": 1}],
            },
            latency_ms=0,
            input_tokens=0,
            output_tokens=0,
        )
