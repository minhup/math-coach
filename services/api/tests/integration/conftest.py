import subprocess
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
from app.database import session_factory
from app.main import app
from app.models import SolutionUpload
from app.storage import get_object_storage
from httpx import ASGITransport, AsyncClient
from minio.error import S3Error
from sqlalchemy import select, text

API_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session", autouse=True)
def migrated_infrastructure() -> Iterator[None]:
    subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=API_ROOT,
        check=True,
    )
    get_object_storage().ensure_bucket()
    yield


async def clear_persisted_test_data() -> None:
    storage = get_object_storage()
    async with session_factory() as database:
        object_keys = list(await database.scalars(select(SolutionUpload.object_key)))
        for object_key in object_keys:
            try:
                storage.remove(object_key)
            except S3Error as error:
                if error.code not in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
                    raise
        await database.execute(
            text(
                "TRUNCATE content_imports, exams, skills, geometry_scenes, concepts, problems, "
                "study_profiles, solution_uploads, user_sessions, pilot_invites, users "
                "RESTART IDENTITY CASCADE"
            )
        )
        await database.commit()


@pytest_asyncio.fixture(autouse=True)
async def isolated_database() -> AsyncIterator[None]:
    await clear_persisted_test_data()
    yield
    await clear_persisted_test_data()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as test_client:
        yield test_client
