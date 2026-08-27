from __future__ import annotations

import argparse
import html
import json
import re
from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urljoin, urlsplit
from urllib.request import Request, urlopen

from scripts.corpus.core import (
    deterministic_id,
    merge_rows,
    normalize_url,
    read_csv,
    write_csv,
)
from scripts.corpus.registry import (
    DOCUMENT_SUFFIXES,
    LEGACY_COLLECTION_FAMILIES,
    REGISTRY_ACQUISITION_FIELDS,
    REGISTRY_MISSING_FIELDS,
    artifact_type,
    candidate_row,
    direct_document_url,
    github_repository_path,
    infer_year,
)

DEFAULT_COLLECTIONS = Path("data/corpus/manifests/registry_collections.csv")
DEFAULT_URLS = Path("data/corpus/manifests/registry_urls.csv")
DEFAULT_PLAN = Path("data/corpus/manifests/registry_acquisition_plan.csv")
DEFAULT_MISSING = Path("data/corpus/manifests/registry_missing_data.csv")
USER_AGENT = "math-coach-global-corpus-research/1.0"
MAX_DISCOVERY_BYTES = 15 * 1024 * 1024
MAX_ASSETS_PER_PAGE = 250
DRIVE_FILE = re.compile(r"https://drive\.google\.com/file/d/([A-Za-z0-9_-]+)")
MARKDOWN_IMAGE = re.compile(r"!\[([^]]*)\]\((https?://[^)]+)\)")


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str, bool]] = []
        self._href = ""
        self._text: list[str] = []
        self._tag_stack: list[tuple[str, bool]] = []
        self._context: list[str] = []
        self._link_scoped = False

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        values = dict(attributes)
        classes = str(values.get("class") or "").split()
        parent_scoped = self._tag_stack[-1][1] if self._tag_stack else False
        scoped = (
            parent_scoped
            or tag in {"article", "main"}
            or bool({"post-body", "entry-content"}.intersection(classes))
        )
        self._tag_stack.append((tag, scoped))
        if tag != "a":
            return
        self._href = str(values.get("href") or "")
        self._text = []
        self._link_scoped = scoped

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text.append(data)
        elif self._tag_stack and self._tag_stack[-1][1] and data.strip():
            self._context.append(data.strip())
            self._context = self._context[-12:]

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href:
            label = " ".join(" ".join(self._text).split())
            context = " ".join(" ".join(self._context[-4:]).split())
            scoped_label = f"{context} | {label}" if self._link_scoped and context else label
            self.links.append((self._href, scoped_label, self._link_scoped))
            self._href = ""
            self._text = []
            self._link_scoped = False
        while self._tag_stack:
            opened_tag, _scoped = self._tag_stack.pop()
            if opened_tag == tag:
                break


def drive_download_url(url: str) -> str | None:
    match = DRIVE_FILE.search(url)
    if match:
        return (
            "https://drive.usercontent.google.com/download"
            f"?authuser=0&confirm=t&export=download&id={match.group(1)}"
        )
    parts = urlsplit(url)
    if parts.hostname == "drive.usercontent.google.com" and parse_qs(parts.query).get("id"):
        return url
    return None


def discover_html_assets(html_text: str, base_url: str) -> list[tuple[str, str]]:
    parser = LinkParser()
    parser.feed(html_text)
    discovered: list[tuple[str, str, bool]] = []
    for href, label, scoped in parser.links:
        absolute = urljoin(base_url, html.unescape(href))
        if urlsplit(absolute).scheme not in {"http", "https"}:
            continue
        drive_url = drive_download_url(absolute)
        if drive_url:
            discovered.append(
                (
                    normalize_url(drive_url),
                    label or Path(urlsplit(absolute).path).name,
                    scoped,
                )
            )
            continue
        if direct_document_url(absolute):
            discovered.append(
                (
                    normalize_url(absolute),
                    label or Path(urlsplit(absolute).path).name,
                    scoped,
                )
            )
    if any(scoped for _url, _label, scoped in discovered):
        discovered = [item for item in discovered if item[2]]
    assets = {url: label for url, label, _scoped in discovered}
    return [(url, assets[url]) for url in sorted(assets)][:MAX_ASSETS_PER_PAGE]


def discover_readme_assets(readme: str) -> list[tuple[str, str]]:
    heading = ""
    assets: list[tuple[str, str]] = []
    for line in readme.splitlines():
        line = line.strip()
        if line.startswith("## "):
            heading = line.removeprefix("## ").strip(" :")
        for label, url in MARKDOWN_IMAGE.findall(line):
            assets.append((normalize_url(url), f"{heading} {label}".strip()))
    return assets


def within_initial_readme_scope(collection_id: str, year: str) -> bool:
    if collection_id not in {"V07", "V08"} or not year:
        return True
    return int(year) >= 2011


def is_target_asset(action: str, source_role: str, url: str, label: str) -> bool:
    if action != "DOWNLOAD" or source_role != "official":
        return True
    return artifact_type(f"{label} {url}") in {"question", "solution"}


def discover_repository_files(
    tree: list[dict[str, Any]], *, owner: str, repository: str, branch: str
) -> list[tuple[str, str, str]]:
    assets: list[tuple[str, str, str]] = []
    for item in tree:
        if item.get("type") != "blob":
            continue
        path = str(item.get("path", ""))
        if Path(path).suffix.casefold() not in DOCUMENT_SUFFIXES:
            continue
        assets.append(
            (
                f"https://raw.githubusercontent.com/{owner}/{repository}/{branch}/{path}",
                path,
                str(item.get("size", "")),
            )
        )
    return sorted(assets)


def request_bytes(url: str, *, accept: str = "*/*") -> bytes:
    request = Request(url, headers={"Accept": accept, "User-Agent": USER_AGENT})
    with urlopen(request, timeout=45) as response:
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_DISCOVERY_BYTES:
            raise ValueError(f"discovery response exceeds {MAX_DISCOVERY_BYTES} bytes")
        data = bytes(response.read(MAX_DISCOVERY_BYTES + 1))
    if len(data) > MAX_DISCOVERY_BYTES:
        raise ValueError(f"discovery response exceeds {MAX_DISCOVERY_BYTES} bytes")
    return data


def request_json(url: str) -> dict[str, Any]:
    value = json.loads(request_bytes(url, accept="application/vnd.github+json"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object from {url}")
    return {str(key): item for key, item in value.items()}


def discover_candidates(
    collections: list[dict[str, str]],
    urls: list[dict[str, str]],
    *,
    priorities: set[str],
    fetch_bytes: Callable[..., bytes] = request_bytes,
    fetch_json: Callable[[str], dict[str, Any]] = request_json,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    collection_by_id = {row["collection_id"]: row for row in collections}
    candidates: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []
    role_order = {"official": 0, "mirror_1": 1, "direct_bundle": 1, "mirror_2": 2}
    official_success: set[str] = set()
    for source in sorted(
        urls,
        key=lambda row: (
            row["collection_id"],
            role_order.get(row["url_role"], 9),
            row["source_url"],
        ),
    ):
        collection_id = source["collection_id"]
        collection = collection_by_id[collection_id]
        if collection["priority"] not in priorities:
            continue
        if collection_id in LEGACY_COLLECTION_FAMILIES:
            continue
        action = collection["agent_action"]
        if (
            action == "DOWNLOAD"
            and source["url_role"] != "official"
            and collection_id in official_success
        ):
            continue
        source_url = source["source_url"]
        repository = github_repository_path(source_url)
        try:
            if action == "GIT_CLONE" and repository:
                owner, name = repository
                metadata = fetch_json(f"https://api.github.com/repos/{owner}/{name}")
                branch = str(metadata["default_branch"])
                tree = fetch_json(
                    f"https://api.github.com/repos/{owner}/{name}/git/trees/{branch}?recursive=1"
                )
                if tree.get("truncated"):
                    raise ValueError("GitHub recursive tree is truncated")
                assets = discover_repository_files(
                    list(tree.get("tree", [])),
                    owner=owner,
                    repository=name,
                    branch=branch,
                )
                for asset_url, path, size in assets:
                    candidates.append(
                        candidate_row(
                            collection_id=collection_id,
                            source_url=asset_url,
                            discovery_url=source_url,
                            url_role=source["url_role"],
                            source_type=source["source_type"],
                            official_status=source["official_status"],
                            acquisition_method="github_raw",
                            expected_size=size,
                            year_hint=path,
                            artifact_hint=artifact_type(path),
                            notes=f"Git repository path: {path}",
                        )
                    )
                readme_url = f"https://raw.githubusercontent.com/{owner}/{name}/{branch}/README.md"
                readme_assets = discover_readme_assets(
                    fetch_bytes(readme_url).decode("utf-8", "replace")
                )
                for asset_url, label in readme_assets:
                    year = infer_year(label, asset_url)
                    candidates.append(
                        candidate_row(
                            collection_id=collection_id,
                            source_url=asset_url,
                            discovery_url=source_url,
                            url_role=source["url_role"],
                            source_type=source["source_type"],
                            official_status=source["official_status"],
                            acquisition_method="github_readme_asset",
                            year_hint=label,
                            artifact_hint="question",
                            selected=(
                                "yes" if within_initial_readme_scope(collection_id, year) else "no"
                            ),
                            notes=(
                                f"GitHub README image under heading: {label}. "
                                "Question classification comes from the archive's stated scope."
                            ),
                        )
                    )
                if not assets and not readme_assets:
                    issues.append(
                        issue_row(
                            source,
                            "no_downloadable_assets",
                            "warning",
                            "No document assets found in repository tree.",
                        )
                    )
                continue
            if action in {"MASTER_DISCOVERY", "INDEX", "INDEX_AND_EXTRACT_METADATA"}:
                continue
            drive_url = drive_download_url(source_url)
            if drive_url or direct_document_url(source_url):
                candidate_url = drive_url or source_url
                is_bundle = "BUNDLE" in action
                candidates.append(
                    candidate_row(
                        collection_id=collection_id,
                        source_url=candidate_url,
                        discovery_url=source_url,
                        url_role=source["url_role"],
                        source_type=source["source_type"],
                        official_status=source["official_status"],
                        acquisition_method="drive_file" if drive_url else "direct_file",
                        year_hint="" if is_bundle else collection["years_volume"],
                        artifact_hint="bundle" if is_bundle else "",
                        notes="Direct asset declared by expanded registry.",
                    )
                )
                if source["url_role"] == "official":
                    official_success.add(collection_id)
                continue
            if source["url_role"] == "mirror_2" and action not in {
                "DOWNLOAD_AND_MIRROR",
                "INDEX_AND_BUNDLE",
            }:
                continue
            body = fetch_bytes(source_url).decode("utf-8", "replace")
            html_assets = [
                (asset_url, label)
                for asset_url, label in discover_html_assets(body, source_url)
                if is_target_asset(action, source["url_role"], asset_url, label)
            ]
            for asset_url, label in html_assets:
                kind = artifact_type(f"{label} {asset_url}")
                if action == "INDEX_AND_BUNDLE" and "all " in label.casefold():
                    kind = "bundle"
                candidates.append(
                    candidate_row(
                        collection_id=collection_id,
                        source_url=asset_url,
                        discovery_url=source_url,
                        url_role=source["url_role"],
                        source_type=source["source_type"],
                        official_status=source["official_status"],
                        acquisition_method="html_link",
                        year_hint=label,
                        artifact_hint=kind,
                        notes=f"Link label: {label}" if label else "Discovered from landing page.",
                    )
                )
            if html_assets and source["url_role"] == "official":
                official_success.add(collection_id)
            if not html_assets and action == "DOWNLOAD":
                issues.append(
                    issue_row(
                        source,
                        "no_downloadable_assets",
                        "warning",
                        "No in-scope question or solution document found on the landing page.",
                    )
                )
            snapshot_action = action in {
                "MIRROR_DOWNLOAD",
                "INDEX_AND_BUNDLE",
                "BUNDLE_DOWNLOAD",
            } or (action == "DOWNLOAD" and source["url_role"] != "official")
            if not html_assets and snapshot_action:
                candidates.append(
                    candidate_row(
                        collection_id=collection_id,
                        source_url=source_url,
                        discovery_url=source_url,
                        url_role=source["url_role"],
                        source_type=source["source_type"],
                        official_status=source["official_status"],
                        acquisition_method="html_snapshot",
                        year_hint="",
                        artifact_hint="web_page",
                        notes=(
                            "No linked document found; preserve the public source page as raw HTML."
                        ),
                    )
                )
        except (
            HTTPError,
            URLError,
            TimeoutError,
            TypeError,
            ValueError,
            KeyError,
            json.JSONDecodeError,
        ) as error:
            issues.append(issue_row(source, "discovery_failure", "warning", str(error)))

    deduplicated = {str(row["candidate_id"]): row for row in candidates}
    return [deduplicated[key] for key in sorted(deduplicated)], issues


def issue_row(
    source: dict[str, str], issue_type: str, severity: str, details: str
) -> dict[str, object]:
    related_id = source["registry_url_id"]
    return {
        "issue_id": deterministic_id("rissue", related_id, issue_type),
        "collection_id": source["collection_id"],
        "logical_set_id": "",
        "year": "",
        "issue_type": issue_type,
        "severity": severity,
        "related_id": related_id,
        "source_url": source["source_url"],
        "status": "open",
        "details": details,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover assets for expanded registry collections."
    )
    parser.add_argument("--collections", type=Path, default=DEFAULT_COLLECTIONS)
    parser.add_argument("--urls", type=Path, default=DEFAULT_URLS)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--missing", type=Path, default=DEFAULT_MISSING)
    parser.add_argument("--priorities", default="P0,P0X")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    priorities = {value.strip() for value in args.priorities.split(",") if value.strip()}
    collections = read_csv(args.collections)
    candidates, issues = discover_candidates(
        collections, read_csv(args.urls), priorities=priorities
    )
    processed_collections = {
        row["collection_id"]
        for row in collections
        if row["priority"] in priorities and row["collection_id"] not in LEGACY_COLLECTION_FAMILIES
    }
    existing_plan = read_csv(args.plan) if args.plan.exists() else []
    existing_missing = read_csv(args.missing) if args.missing.exists() else []
    retained_plan = [
        row for row in existing_plan if row["collection_id"] not in processed_collections
    ]
    retained_missing = [
        row
        for row in existing_missing
        if not (
            row["collection_id"] in processed_collections
            and row["issue_type"] in {"discovery_failure", "no_downloadable_assets"}
        )
    ]
    write_csv(
        args.plan,
        REGISTRY_ACQUISITION_FIELDS,
        merge_rows(retained_plan, candidates, key="candidate_id"),
    )
    write_csv(
        args.missing,
        REGISTRY_MISSING_FIELDS,
        merge_rows(retained_missing, issues, key="issue_id"),
    )
    print(f"Discovered {len(candidates)} candidates with {len(issues)} source findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
