from datetime import timedelta

import httpx
import pytest
from app.database import session_factory
from app.main import app
from app.models import PilotInvite, SolutionUpload, User, UserSession
from app.security import digest_secret, utc_now
from app.storage import get_object_storage
from sqlalchemy import select

pytestmark = pytest.mark.integration


async def add_invite(code: str, display_name: str) -> None:
    async with session_factory() as database:
        database.add(
            PilotInvite(
                code_digest=digest_secret(code),
                display_name=display_name,
                max_uses=1,
                expires_at=utc_now() + timedelta(hours=1),
            )
        )
        await database.commit()


async def login(client: httpx.AsyncClient, code: str) -> httpx.Response:
    return await client.post("/api/v1/auth/pilot-login", json={"inviteCode": code})


async def create_signed_upload(
    client: httpx.AsyncClient,
    *,
    size_bytes: int,
    file_name: str = "synthetic-solution.png",
) -> httpx.Response:
    return await client.post(
        "/api/v1/uploads/presign",
        json={
            "contentType": "image/png",
            "fileName": file_name,
            "sizeBytes": size_bytes,
        },
    )


async def test_health_and_validation_errors_use_stable_contract(
    client: httpx.AsyncClient,
) -> None:
    health = await client.get("/api/v1/health")
    invalid = await client.post("/api/v1/auth/pilot-login", json={"inviteCode": "x"})

    assert health.json() == {"status": "ok"}
    assert health.headers["x-request-id"]
    assert invalid.status_code == 422
    assert invalid.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Check the submitted values and try again.",
            "requestId": invalid.headers["x-request-id"],
        }
    }


async def test_invite_login_reuses_user_hashes_secrets_and_logout_revokes_session(
    client: httpx.AsyncClient,
) -> None:
    raw_code = "VALID-INTERNAL-INVITE"
    await add_invite(raw_code, "Internal learner")

    first = await login(client, raw_code)
    current = await client.get("/api/v1/auth/me")
    second = await login(client, raw_code)

    assert first.status_code == 200
    assert current.json()["displayName"] == "Internal learner"
    assert second.json()["user"]["id"] == first.json()["user"]["id"]
    assert "HttpOnly" in first.headers["set-cookie"]
    assert "SameSite=lax" in first.headers["set-cookie"]

    async with session_factory() as database:
        invite = await database.scalar(select(PilotInvite))
        sessions = list(await database.scalars(select(UserSession)))
        users = list(await database.scalars(select(User)))
        assert invite is not None
        assert invite.code_digest == digest_secret(raw_code)
        assert raw_code not in invite.code_digest
        assert invite.use_count == 1
        assert len(users) == 1
        assert len(sessions) == 2
        assert all(raw_code not in session.token_digest for session in sessions)

    logout = await client.post("/api/v1/auth/logout")
    after_logout = await client.get("/api/v1/auth/me")
    assert logout.status_code == 204
    assert after_logout.status_code == 401
    assert after_logout.json()["error"]["code"] == "authentication_required"


async def test_invalid_invite_and_unauthenticated_upload_fail_safely(
    client: httpx.AsyncClient,
) -> None:
    invalid = await login(client, "NOT-A-REAL-INVITE")
    upload = await create_signed_upload(client, size_bytes=4)

    assert invalid.status_code == 401
    assert invalid.json()["error"]["code"] == "invalid_invite"
    assert upload.status_code == 401
    assert upload.json()["error"]["code"] == "authentication_required"


async def test_signed_upload_is_verified_in_object_storage(
    client: httpx.AsyncClient,
) -> None:
    await add_invite("UPLOAD-INVITE", "Upload learner")
    assert (await login(client, "UPLOAD-INVITE")).status_code == 200
    image_bytes = b"\x89PNG\r\n\x1a\nsynthetic-only"

    signed = await create_signed_upload(client, size_bytes=len(image_bytes))
    assert signed.status_code == 200
    signed_body = signed.json()
    async with httpx.AsyncClient() as storage_client:
        stored = await storage_client.put(
            signed_body["uploadUrl"],
            content=image_bytes,
            headers={"Content-Type": "image/png"},
        )
    completed = await client.post(f"/api/v1/uploads/{signed_body['uploadId']}/complete")
    fetched = await client.get(f"/api/v1/uploads/{signed_body['uploadId']}")

    assert stored.status_code == 200
    assert completed.status_code == 200
    assert completed.json()["status"] == "ready"
    assert completed.json()["sizeBytes"] == len(image_bytes)
    assert fetched.json() == completed.json()

    async with session_factory() as database:
        upload = await database.scalar(select(SolutionUpload))
        assert upload is not None
        assert upload.verified_content_type == "image/png"
        assert upload.verified_size_bytes == len(image_bytes)


async def test_upload_ownership_is_not_revealed_to_another_user(
    client: httpx.AsyncClient,
) -> None:
    await add_invite("OWNER-INVITE", "Owner")
    await add_invite("OTHER-INVITE", "Other learner")
    assert (await login(client, "OWNER-INVITE")).status_code == 200
    signed = await create_signed_upload(client, size_bytes=4)
    upload_id = signed.json()["uploadId"]

    other_client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    )
    try:
        assert (await login(other_client, "OTHER-INVITE")).status_code == 200
        fetched = await other_client.get(f"/api/v1/uploads/{upload_id}")
        completed = await other_client.post(f"/api/v1/uploads/{upload_id}/complete")
    finally:
        await other_client.aclose()

    assert fetched.status_code == 404
    assert fetched.json()["error"]["code"] == "upload_not_found"
    assert completed.status_code == 404


async def test_mismatched_object_is_rejected(
    client: httpx.AsyncClient,
) -> None:
    await add_invite("MISMATCH-INVITE", "Mismatch learner")
    assert (await login(client, "MISMATCH-INVITE")).status_code == 200
    signed = await create_signed_upload(client, size_bytes=10)
    body = signed.json()
    async with httpx.AsyncClient() as storage_client:
        stored = await storage_client.put(
            body["uploadUrl"],
            content=b"short",
            headers={"Content-Type": "image/png"},
        )

    completed = await client.post(f"/api/v1/uploads/{body['uploadId']}/complete")

    assert stored.status_code == 200
    assert completed.status_code == 422
    assert completed.json()["error"]["code"] == "upload_verification_failed"
    async with session_factory() as database:
        upload = await database.scalar(select(SolutionUpload))
        assert upload is not None
        assert upload.status == "rejected"


async def test_unexpected_backend_failure_uses_safe_error_envelope(
    client: httpx.AsyncClient,
) -> None:
    class UnavailableStorage:
        def presign_put(self, _object_key: str, _expires_seconds: int) -> str:
            raise RuntimeError("synthetic storage failure")

    await add_invite("FAILURE-INVITE", "Failure learner")
    assert (await login(client, "FAILURE-INVITE")).status_code == 200
    app.dependency_overrides[get_object_storage] = UnavailableStorage
    try:
        response = await create_signed_upload(client, size_bytes=4)
    finally:
        app.dependency_overrides.pop(get_object_storage, None)

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_error",
            "message": "Something went wrong. Try again.",
            "requestId": response.headers["x-request-id"],
        }
    }
