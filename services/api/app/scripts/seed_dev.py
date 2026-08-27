import asyncio

from sqlalchemy import select

from app.config import get_settings
from app.database import session_factory
from app.models import PilotInvite
from app.security import digest_secret


def milestone_five_device_invites() -> tuple[tuple[str, str], ...]:
    return (
        ("MATH-COACH-M5-COMPACT", "Synthetic compact learner"),
        ("MATH-COACH-M5-PIXEL-7", "Synthetic Pixel 7 learner"),
        ("MATH-COACH-M5-IPHONE-13", "Synthetic iPhone 13 learner"),
        ("MATH-COACH-M5-IPAD-PORTRAIT", "Synthetic iPad portrait learner"),
        ("MATH-COACH-M5-IPAD-LANDSCAPE", "Synthetic iPad landscape learner"),
    )


async def seed_development_invite() -> None:
    settings = get_settings()
    if settings.environment not in {"development", "test"}:
        raise RuntimeError("Development invite seeding is disabled outside development and test")
    configured_invites = (
        (settings.development_invite_code.get_secret_value(), "Internal learner"),
        *milestone_five_device_invites(),
    )
    async with session_factory() as database:
        inserted = 0
        for code, display_name in configured_invites:
            digest = digest_secret(code)
            invite = await database.scalar(
                select(PilotInvite).where(PilotInvite.code_digest == digest)
            )
            if invite is not None:
                continue
            database.add(
                PilotInvite(
                    code_digest=digest,
                    display_name=display_name,
                    max_uses=1,
                )
            )
            inserted += 1
        await database.commit()
        print(f"Development invites ready ({inserted} newly seeded).")


if __name__ == "__main__":
    asyncio.run(seed_development_invite())
