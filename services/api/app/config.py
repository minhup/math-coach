from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    @model_validator(mode="after")
    def reject_development_defaults_in_production(self) -> "Settings":
        if self.environment == "production":
            if self.development_invite_code.get_secret_value() == "MATH-COACH-LOCAL":
                raise ValueError("Production requires a non-default invite bootstrap path")
            if self.object_storage_secret_key.get_secret_value() == "local-object-storage-only":
                raise ValueError("Production requires a non-default object-storage secret")
            if not self.session_cookie_secure:
                raise ValueError("Production requires secure session cookies")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
