import asyncio
import sys
from pathlib import Path

from app.config import get_settings
from app.content.importer import ContentImportError, import_content_package
from app.content.loader import (
    ContentValidationError,
    discover_content_packages,
    load_content_package,
)
from app.database import session_factory


async def seed_content(content_root: Path) -> None:
    settings = get_settings()
    if settings.environment not in {"development", "test"}:
        raise RuntimeError("Synthetic content seeding is disabled outside development and test")
    package_paths = discover_content_packages(content_root)
    for path in package_paths:
        package = load_content_package(path)
        async with session_factory() as database:
            result = await import_content_package(
                package,
                database,
                source_path=str(path.relative_to(content_root.parent)),
            )
        print(
            f"Content package {package.package_id} v{package.package_version}: "
            f"{result.status} ({result.content_hash})"
        )


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m app.scripts.seed_content <content-root>")
        return 2
    try:
        asyncio.run(seed_content(Path(sys.argv[1]).resolve()))
    except (ContentImportError, ContentValidationError, RuntimeError) as error:
        print(f"Content seed failed: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
