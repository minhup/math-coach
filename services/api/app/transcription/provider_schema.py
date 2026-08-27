from pydantic import TypeAdapter

from app.transcription.schemas import ProviderPayload

PROVIDER_JSON_SCHEMA = TypeAdapter(ProviderPayload).json_schema(by_alias=True)
