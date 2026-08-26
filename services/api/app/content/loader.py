import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError
from yaml.constructor import ConstructorError

from app.content.schemas import ContentPackage


class ContentValidationError(ValueError):
    pass


def discover_content_packages(content_root: Path) -> list[Path]:
    packages_root = content_root / "packages"
    if not packages_root.is_dir():
        raise ContentValidationError(f"content packages directory is missing: {packages_root}")
    allowed_root_files = {content_root / "README.md"}
    unexpected_root = sorted(
        path
        for path in content_root.iterdir()
        if path not in allowed_root_files and path != packages_root
    )
    if unexpected_root:
        raise ContentValidationError(
            "unexpected files or directories at the content root: "
            + ", ".join(str(path.relative_to(content_root)) for path in unexpected_root)
        )
    package_paths: list[Path] = []
    for package_directory in sorted(packages_root.iterdir()):
        if not package_directory.is_dir():
            raise ContentValidationError(
                f"content/packages entries must be directories: {package_directory.name}"
            )
        candidates = sorted(
            path
            for path in package_directory.iterdir()
            if path.is_file() and path.name in {"package.json", "package.yaml", "package.yml"}
        )
        unexpected = sorted(path for path in package_directory.iterdir() if path not in candidates)
        if unexpected or len(candidates) != 1:
            raise ContentValidationError(
                f"{package_directory.name} must contain exactly one package.json, package.yaml, "
                "or package.yml and no other files"
            )
        package_paths.append(candidates[0])
    if not package_paths:
        raise ContentValidationError("at least one versioned content package is required")
    return package_paths


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: UniqueKeyLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict[object, object]:
    explicit_keys: set[object] = set()
    for key_node, _value_node in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            continue
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in explicit_keys
        except TypeError as error:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable key",
                key_node.start_mark,
            ) from error
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        explicit_keys.add(key)
    loader.flatten_mapping(node)
    result: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            hash(key)
        except TypeError as error:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable key",
                key_node.start_mark,
            ) from error
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContentValidationError(f"found duplicate key {key!r}")
        result[key] = value
    return result


def load_content_package(path: Path) -> ContentPackage:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ContentValidationError(f"could not read content package {path}") from error
    try:
        if path.suffix == ".json":
            raw = json.loads(source, object_pairs_hook=_unique_json_object)
        elif path.suffix in {".yaml", ".yml"}:
            raw = yaml.load(source, Loader=UniqueKeyLoader)
        else:
            raise ContentValidationError(
                f"unsupported content package extension {path.suffix or '<none>'}"
            )
    except (json.JSONDecodeError, yaml.YAMLError) as error:
        raise ContentValidationError(f"invalid content syntax in {path}: {error}") from error
    try:
        return ContentPackage.model_validate(raw)
    except ValidationError as error:
        raise ContentValidationError(f"invalid content package {path}: {error}") from error


def canonical_content_json(package: ContentPackage) -> str:
    return json.dumps(
        package.model_dump(mode="json", by_alias=True),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def canonical_content_hash(package: ContentPackage) -> str:
    return hashlib.sha256(canonical_content_json(package).encode("utf-8")).hexdigest()


def content_schema_json() -> str:
    return (
        json.dumps(
            ContentPackage.model_json_schema(by_alias=True, mode="validation"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
