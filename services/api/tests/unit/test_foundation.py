from datetime import UTC

import pytest
from app.config import Settings
from app.errors import AppError, error_body
from app.schemas import PresignUploadRequest
from app.security import digest_secret, generate_session_token, utc_now
from app.uploads import safe_file_name
from pydantic import ValidationError


def test_secret_digests_are_deterministic_without_preserving_raw_values() -> None:
    raw = "internal-invite"

    digest = digest_secret(raw)

    assert digest == digest_secret(raw)
    assert digest != raw
    assert len(digest) == 64


def test_session_tokens_are_opaque_and_unique() -> None:
    first = generate_session_token()
    second = generate_session_token()

    assert first != second
    assert len(first) >= 32
    assert len(second) >= 32


def test_utc_now_is_timezone_aware() -> None:
    assert utc_now().tzinfo is UTC


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("solution.png", "solution.png"),
        ("../../solution.png", "solution.png"),
        (r"C:\\fakepath\\solution.webp", "solution.webp"),
        ("  page 1.jpg  ", "page 1.jpg"),
    ],
)
def test_file_names_are_reduced_to_safe_base_names(value: str, expected: str) -> None:
    assert safe_file_name(value) == expected


@pytest.mark.parametrize("value", ["", ".", "..", "\x00.png"])
def test_invalid_file_names_are_rejected(value: str) -> None:
    with pytest.raises(AppError, match="valid file name") as caught:
        safe_file_name(value)

    assert caught.value.code == "invalid_file_name"


def test_upload_schema_rejects_unsupported_media_type() -> None:
    with pytest.raises(ValidationError):
        PresignUploadRequest(file_name="notes.txt", content_type="text/plain", size_bytes=5)


def test_error_body_uses_the_stable_public_shape() -> None:
    assert error_body(code="invalid_request", message="Try again.", request_id="request-1") == {
        "error": {
            "code": "invalid_request",
            "message": "Try again.",
            "requestId": "request-1",
        }
    }


def test_production_configuration_rejects_local_credentials() -> None:
    with pytest.raises(ValidationError, match="non-default invite"):
        Settings(environment="production", session_cookie_secure=True)
