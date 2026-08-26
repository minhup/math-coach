import sys
from pathlib import Path

from app.content.loader import (
    ContentValidationError,
    canonical_content_hash,
    content_schema_json,
    discover_content_packages,
    load_content_package,
)


def validate(content_root: Path, schema_path: Path) -> list[tuple[Path, str]]:
    expected_schema = content_schema_json()
    try:
        committed_schema = schema_path.read_text(encoding="utf-8")
    except OSError as error:
        raise ContentValidationError(
            f"could not read generated content schema {schema_path}"
        ) from error
    if committed_schema != expected_schema:
        raise ContentValidationError(
            "generated content schema is stale; run make content-schema-generate"
        )
    results: list[tuple[Path, str]] = []
    seen_packages: set[tuple[object, int]] = set()
    for path in discover_content_packages(content_root):
        package = load_content_package(path)
        key = (package.package_id, package.package_version)
        if key in seen_packages:
            raise ContentValidationError("package ID and version combinations must be unique")
        seen_packages.add(key)
        results.append((path, canonical_content_hash(package)))
    return results


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "Usage: python -m app.scripts.validate_content <content-root> <generated-schema-path>"
        )
        return 2
    content_root = Path(sys.argv[1]).resolve()
    schema_path = Path(sys.argv[2]).resolve()
    try:
        results = validate(content_root, schema_path)
    except ContentValidationError as error:
        print(f"Content validation failed: {error}")
        return 1
    for path, content_hash in results:
        print(f"Validated {path.relative_to(content_root)} sha256:{content_hash}")
    print(f"Content validation passed: {len(results)} versioned package(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
