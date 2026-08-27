from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from scripts.corpus.core import (
    ACQUISITION_FIELDS,
    CorpusError,
    deterministic_id,
    extract_urls,
    normalize_url,
    read_csv,
    write_csv,
)

DEFAULT_SOURCES = Path("data/corpus/manifests/sources.csv")
DEFAULT_OUTPUT = Path("data/corpus/manifests/acquisition_plan.csv")
USER_AGENT = "math-coach-corpus-research/1.0"
YEAR_HEADING = re.compile(r"^##\s+(20\d{2})-(20\d{2})\s*:", re.MULTILINE)
DIRECT_ASSET_HOSTS = {
    "github.com",
    "user-images.githubusercontent.com",
    "raw.githubusercontent.com",
    "toanhocvietnam.vn",
    "icdn.dantri.com.vn",
}


def github_repository_path(url: str) -> tuple[str, str]:
    parts = urlsplit(normalize_url(url))
    path_parts = [part for part in parts.path.split("/") if part]
    if parts.hostname != "github.com" or len(path_parts) != 2:
        raise CorpusError(f"not a GitHub repository URL: {url}")
    return path_parts[0], path_parts[1].removesuffix(".git")


def discover(
    sources: list[dict[str, str]],
    *,
    start_year: int,
    end_year: int,
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for source in sources:
        if source["source_type"] != "community_github_archive":
            continue
        owner, repository = github_repository_path(source["source_url"])
        metadata = request_json(f"https://api.github.com/repos/{owner}/{repository}")
        branch = str(metadata["default_branch"])
        readme_url = f"https://raw.githubusercontent.com/{owner}/{repository}/{branch}/README.md"
        readme = request_bytes(readme_url).decode("utf-8")
        candidates.extend(
            discover_readme_assets(
                readme,
                source=source,
                discovery_url=source["source_url"],
                start_year=start_year,
                end_year=end_year,
            )
        )
        tree = request_json(
            f"https://api.github.com/repos/{owner}/{repository}/git/trees/{branch}?recursive=1"
        )
        if tree.get("truncated"):
            raise CorpusError(f"GitHub tree was truncated for {owner}/{repository}")
        candidates.extend(
            discover_repository_files(
                tree["tree"],
                source=source,
                owner=owner,
                repository=repository,
                branch=branch,
                start_year=start_year,
                end_year=end_year,
            )
        )

    deduplicated: dict[str, dict[str, object]] = {}
    for candidate in candidates:
        key = normalize_url(str(candidate["source_url"]))
        existing = deduplicated.get(key)
        if existing is None or str(candidate["paper_type"]) != "unknown":
            deduplicated[key] = candidate
    return sorted(
        deduplicated.values(),
        key=lambda row: (
            str(row["exam_family"]),
            int(str(row["calendar_year"])),
            str(row["source_url"]),
        ),
    )


def discover_readme_assets(
    readme: str,
    *,
    source: dict[str, str],
    discovery_url: str,
    start_year: int,
    end_year: int,
) -> list[dict[str, object]]:
    headings = list(YEAR_HEADING.finditer(readme))
    results: list[dict[str, object]] = []
    for index, heading in enumerate(headings):
        calendar_year = int(heading.group(1))
        academic_year = f"{heading.group(1)}-{heading.group(2)}"
        if not start_year <= calendar_year <= end_year:
            continue
        section_end = headings[index + 1].start() if index + 1 < len(headings) else len(readme)
        section = readme[heading.end() : section_end]
        asset_index = 0
        for url in extract_urls(section):
            normalized = normalize_url(url)
            domain = urlsplit(normalized).hostname or ""
            if domain not in DIRECT_ASSET_HOSTS:
                continue
            if domain == "github.com" and "/assets/" not in url:
                continue
            asset_index += 1
            paper_type = (
                "unknown"
                if domain in {"github.com", "user-images.githubusercontent.com"}
                else classify_paper_type(Path(urlsplit(url).path).name)
            )
            results.append(
                candidate_row(
                    source=source,
                    source_url=url,
                    discovery_url=discovery_url,
                    calendar_year=calendar_year,
                    academic_year=academic_year,
                    exam_variant=f"archive_asset_{asset_index:02d}",
                    paper_type=paper_type,
                    expected_size="",
                    notes="Discovered under a year heading in the community archive README.",
                )
            )
    return results


def discover_repository_files(
    tree: list[dict[str, Any]],
    *,
    source: dict[str, str],
    owner: str,
    repository: str,
    branch: str,
    start_year: int,
    end_year: int,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for item in tree:
        if item.get("type") != "blob":
            continue
        path = str(item["path"])
        if Path(path).suffix.casefold() not in {
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
            ".doc",
            ".docx",
        }:
            continue
        year_match = re.search(r"(?<!\d)(20\d{2})(?!\d)", path)
        if year_match is None:
            continue
        calendar_year = int(year_match.group(1))
        if not start_year <= calendar_year <= end_year:
            continue
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repository}/{branch}/{path}"
        results.append(
            candidate_row(
                source=source,
                source_url=raw_url,
                discovery_url=f"https://github.com/{owner}/{repository}/blob/{branch}/{path}",
                calendar_year=calendar_year,
                academic_year=f"{calendar_year}-{calendar_year + 1}",
                exam_variant="repository_file",
                paper_type=classify_paper_type(Path(path).name),
                expected_size=str(item.get("size", "")),
                notes=f"Git repository path: {path}",
            )
        )
    return results


def classify_paper_type(value: str) -> str:
    lowered = _ascii_fold(value.casefold())
    if any(
        marker in lowered
        for marker in ("dap-an", "dap_an", "dap an", "dapan", "answer", "solution")
    ):
        return "answer_key"
    if any(
        marker in lowered
        for marker in (
            "de-thi",
            "de_thi",
            "de thi",
            "de-tuyen-sinh",
            "de_tuyen_sinh",
            "question",
            "exam",
        )
    ):
        return "question_paper"
    return "unknown"


def _ascii_fold(value: str) -> str:
    import unicodedata

    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(character)
    ).replace("đ", "d")


def candidate_row(
    *,
    source: dict[str, str],
    source_url: str,
    discovery_url: str,
    calendar_year: int,
    academic_year: str,
    exam_variant: str,
    paper_type: str,
    expected_size: str,
    notes: str,
) -> dict[str, object]:
    normalized = normalize_url(source_url)
    family = source["exam_families"]
    if "|" in family or not family:
        raise CorpusError(
            f"archive source must map to exactly one exam family: {source['source_id']}"
        )
    suffix = Path(urlsplit(normalized).path).suffix.casefold()
    expected_mime = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }.get(suffix, "unknown")
    return {
        "candidate_id": deterministic_id("cand", family, str(calendar_year), normalized),
        "exam_family": family,
        "academic_year": academic_year,
        "calendar_year": calendar_year,
        "exam_variant": exam_variant,
        "subject": "mathematics",
        "paper_type": paper_type,
        "source_id": source["source_id"],
        "source_url": source_url,
        "discovery_url": discovery_url,
        "source_name": source["source_name"],
        "source_type": source["source_type"],
        "official_status": source["official_status"],
        "expected_mime_type": expected_mime,
        "expected_size": expected_size,
        "selected": "yes",
        "rights_status": source["rights_status"],
        "notes": notes,
    }


def request_bytes(url: str) -> bytes:
    request = Request(
        url, headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT}
    )
    try:
        with urlopen(request, timeout=30) as response:
            return bytes(response.read())
    except (HTTPError, URLError, TimeoutError) as error:
        raise CorpusError(f"request failed for {url}: {error}") from error


def request_json(url: str) -> dict[str, Any]:
    try:
        parsed = json.loads(request_bytes(url))
    except json.JSONDecodeError as error:
        raise CorpusError(f"invalid JSON from {url}: {error}") from error
    if not isinstance(parsed, dict):
        raise CorpusError(f"expected a JSON object from {url}")
    return {str(key): value for key, value in parsed.items()}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover recent files in GitHub exam archives.")
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--start-year", type=int, default=2017)
    parser.add_argument("--end-year", type=int, default=2026)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates = discover(
        read_csv(args.sources),
        start_year=args.start_year,
        end_year=args.end_year,
    )
    write_csv(args.output, ACQUISITION_FIELDS, candidates)
    total_size = sum(int(str(row["expected_size"]) or "0") for row in candidates)
    print(
        f"Wrote {len(candidates)} candidates to {args.output}; known repository bytes={total_size}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
