from datetime import timedelta
from typing import Annotated, cast

from fastapi import Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_database_session
from app.errors import AppError
from app.models import PilotInvite, User, UserSession
from app.schemas import PilotLoginRequest, SessionResponse, UserResponse
from app.security import digest_secret, generate_session_token, utc_now


async def create_session_from_invite(
    payload: PilotLoginRequest,
    database: AsyncSession,
    settings: Settings,
) -> tuple[str, User, UserSession]:
    invite = await database.scalar(
        select(PilotInvite)
        .where(PilotInvite.code_digest == digest_secret(payload.invite_code))
        .with_for_update()
    )
    now = utc_now()
    if invite is None or invite.status != "active":
        raise AppError(status_code=401, code="invalid_invite", message="That invite is not valid.")
    if invite.expires_at is not None and invite.expires_at <= now:
        raise AppError(status_code=401, code="invalid_invite", message="That invite is not valid.")

    user: User | None = None
    if invite.user_id is not None:
        user = await database.get(User, invite.user_id)
    elif invite.use_count < invite.max_uses:
        user = User(display_name=invite.display_name)
        database.add(user)
        await database.flush()
        invite.user_id = user.id
        invite.use_count += 1

    if user is None or user.account_status != "active" or user.deleted_at is not None:
        raise AppError(status_code=401, code="invalid_invite", message="That invite is not valid.")

    raw_token = generate_session_token()
    session = UserSession(
        user_id=user.id,
        token_digest=digest_secret(raw_token),
        expires_at=now + timedelta(hours=settings.session_duration_hours),
    )
    database.add(session)
    await database.commit()
    return raw_token, user, session


def set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        max_age=settings.session_duration_hours * 60 * 60,
        samesite="lax",
        secure=settings.session_cookie_secure,
        path="/",
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        path="/",
    )


async def require_user(
    request: Request,
    database: Annotated[AsyncSession, Depends(get_database_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    math_coach_session = request.cookies.get(settings.session_cookie_name)
    if math_coach_session is None:
        raise AppError(status_code=401, code="authentication_required", message="Sign in again.")
    row = (
        await database.execute(
            select(UserSession, User)
            .join(User, User.id == UserSession.user_id)
            .where(UserSession.token_digest == digest_secret(math_coach_session))
        )
    ).one_or_none()
    now = utc_now()
    if row is None:
        raise AppError(status_code=401, code="authentication_required", message="Sign in again.")
    session = cast(UserSession, row[0])
    user = cast(User, row[1])
    if (
        session.revoked_at is not None
        or session.expires_at <= now
        or user.account_status != "active"
        or user.deleted_at is not None
    ):
        raise AppError(status_code=401, code="authentication_required", message="Sign in again.")
    return user


async def revoke_session(
    raw_token: str | None,
    database: AsyncSession,
) -> None:
    if raw_token is None:
        return
    session = await database.scalar(
        select(UserSession).where(UserSession.token_digest == digest_secret(raw_token))
    )
    if session is not None and session.revoked_at is None:
        session.revoked_at = utc_now()
        await database.commit()


def session_response(user: User, session: UserSession) -> SessionResponse:
    return SessionResponse(
        user=UserResponse(id=user.id, display_name=user.display_name),
        expires_at=session.expires_at,
    )


def user_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, display_name=user.display_name)


CurrentUser = Annotated[User, Depends(require_user)]
