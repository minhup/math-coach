import asyncio

from sqlalchemy import select

from app.config import get_settings
from app.database import session_factory
from app.models import PilotInvite
from app.security import digest_secret


async def seed_development_invite() -> None:
    settings = get_settings()
    if settings.environment not in {"development", "test"}:
        raise RuntimeError("Development invite seeding is disabled outside development and test")
    digest = digest_secret(settings.development_invite_code.get_secret_value())
    async with session_factory() as database:
        invite = await database.scalar(select(PilotInvite).where(PilotInvite.code_digest == digest))
        if invite is None:
            database.add(
                PilotInvite(
                    code_digest=digest,
                    display_name="Internal learner",
                    max_uses=1,
                )
            )
            await database.commit()
            print("Development invite seeded.")
        else:
            print("Development invite already exists.")


if __name__ == "__main__":
    asyncio.run(seed_development_invite())
