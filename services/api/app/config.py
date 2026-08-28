from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

APPROVED_TRANSCRIPTION_MODELS = {
    "fake": frozenset({"m6-transcription-fixture-v1"}),
    "gemini": frozenset({"gemini-3.5-flash-lite", "gemini-3.5-flash"}),
    "openai": frozenset({"gpt-5.4-2026-03-05"}),
    "anthropic": frozenset({"claude-sonnet-5"}),
}

APPROVED_EVALUATION_MODELS = {
    "fake": frozenset({"m7-evaluation-fixture-v1"}),
    "gemini": frozenset({"gemini-3.5-flash-lite", "gemini-3.5-flash"}),
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_prefix="MATH_COACH_",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    database_url: SecretStr = SecretStr(
        "postgresql+asyncpg://math_coach:math_coach_dev@localhost:5432/math_coach"
    )
    development_invite_code: SecretStr = SecretStr("MATH-COACH-LOCAL")
    session_cookie_name: str = "math_coach_session"
    session_cookie_secure: bool = False
    session_duration_hours: int = 12
    object_storage_endpoint: str = "localhost:9000"
    object_storage_public_endpoint: str = "localhost:9000"
    object_storage_access_key: SecretStr = SecretStr("math_coach_dev")
    object_storage_secret_key: SecretStr = SecretStr("local-object-storage-only")
    object_storage_bucket: str = "math-coach-dev"
    object_storage_secure: bool = False
    object_storage_public_secure: bool = False
    upload_url_expiry_seconds: int = 300
    upload_max_bytes: int = 10 * 1024 * 1024
    transcription_provider: Literal["fake", "gemini", "openai", "anthropic"] = "fake"
    transcription_model_snapshot: str = "m6-transcription-fixture-v1"
    transcription_timeout_seconds: int = Field(default=60, ge=5, le=180)
    evaluation_provider: Literal["fake", "gemini"] = "fake"
    evaluation_model_snapshot: str = "m7-evaluation-fixture-v1"
    evaluation_timeout_seconds: int = Field(default=60, ge=5, le=180)
    gemini_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None

    @model_validator(mode="after")
    def reject_development_defaults_in_production(self) -> "Settings":
        if (
            self.transcription_model_snapshot
            not in APPROVED_TRANSCRIPTION_MODELS[self.transcription_provider]
        ):
            raise ValueError("Transcription requires the exact model approved for its provider")
        if (
            self.evaluation_model_snapshot
            not in APPROVED_EVALUATION_MODELS[self.evaluation_provider]
        ):
            raise ValueError("Evaluation requires the exact model approved for its provider")
        selected_keys = {
            "gemini": self.gemini_api_key,
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
        }
        if self.transcription_provider != "fake":
            selected_key = selected_keys[self.transcription_provider]
            if selected_key is None or not selected_key.get_secret_value().strip():
                raise ValueError("The selected transcription provider requires a server API key")
        if self.evaluation_provider == "gemini" and (
            self.gemini_api_key is None or not self.gemini_api_key.get_secret_value().strip()
        ):
            raise ValueError("The selected evaluation provider requires a server API key")
        if self.environment == "production":
            if self.development_invite_code.get_secret_value() == "MATH-COACH-LOCAL":
                raise ValueError("Production requires a non-default invite bootstrap path")
            if self.object_storage_secret_key.get_secret_value() == "local-object-storage-only":
                raise ValueError("Production requires a non-default object-storage secret")
            if not self.session_cookie_secure:
                raise ValueError("Production requires secure session cookies")
            if self.transcription_provider == "fake":
                raise ValueError("Production requires an explicitly configured real provider")
            if self.evaluation_provider == "fake":
                raise ValueError("Production requires an explicitly configured evaluation provider")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
