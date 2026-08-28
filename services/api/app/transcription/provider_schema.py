from pydantic import TypeAdapter

from app.transcription.schemas import ProviderPayload

PROVIDER_JSON_SCHEMA = TypeAdapter(ProviderPayload).json_schema(by_alias=True)

_GEMINI_SOURCE_REGION_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "x": {"type": "number"},
        "y": {"type": "number"},
        "width": {"type": "number"},
        "height": {"type": "number"},
    },
    "required": ["x", "y", "width", "height"],
}

GEMINI_PROVIDER_JSON_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "outcome": {"type": "string", "enum": ["ready", "uncertain"]},
        "blocks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["text", "math"]},
                    "text": {"type": "string"},
                    "latex": {"type": "string"},
                    "sourceRegion": _GEMINI_SOURCE_REGION_SCHEMA,
                },
                "required": ["type"],
            },
        },
        "warnings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "enum": [
                            "low_confidence_text",
                            "low_confidence_math",
                            "ambiguous_cross_out",
                            "ambiguous_insertion",
                            "ordering_uncertain",
                            "source_region_unavailable",
                        ],
                    },
                    "blockIndex": {"type": "integer"},
                },
                "required": ["code"],
            },
        },
    },
    "required": ["outcome"],
}
