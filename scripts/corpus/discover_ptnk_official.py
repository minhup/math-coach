from __future__ import annotations

import argparse
import html
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

from scripts.corpus.core import (
    ACQUISITION_FIELDS,
    SOURCE_FIELDS,
    CorpusError,
    deterministic_id,
    merge_rows,
    normalize_url,
    read_csv,
    write_csv,
)
from scripts.corpus.discover_github_archives import candidate_row, classify_paper_type

DEFAULT_SOURCES = Path("data/corpus/manifests/sources.csv")
DEFAULT_PLAN = Path("data/corpus/manifests/acquisition_plan.csv")
ARCHIVE_PAGES = (
    "https://ptnk.edu.vn/tuyen-sinh-ptnk/de-thi-dap-an/",
    "https://ptnk.edu.vn/tuyen-sinh-ptnk/de-thi-dap-an/page/2/",
)
DRIVE_FOLDER = re.compile(r"https://drive\.google\.com/drive/folders/[A-Za-z0-9_-]+[^\"'<> ]*")
DRIVE_FILE = re.compile(r'data-id="([A-Za-z0-9_-]+)"[^>]{0,500}?data-tooltip="([^"]+)"', re.DOTALL)
USER_AGENT = "Mozilla/5.0 math-coach-corpus-research/1.0"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, _tag: str, attributes: list[tuple[str, str | None]]) -> None:
        values = dict(attributes)
        if values.get("href"):
            self.links.append(str(values["href"]))


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=45) as response:
        if response.headers.get_content_type() != "text/html":
            raise CorpusError(f"expected HTML from {url}")
        return bytes(response.read(5 * 1024 * 1024)).decode("utf-8", "replace")


def discover_landing_pages(start_year: int, end_year: int) -> list[tuple[int, str]]:
    results: set[tuple[int, str]] = set()
    for archive_url in ARCHIVE_PAGES:
        parser = LinkParser()
        parser.feed(fetch_text(archive_url))
        for link in parser.links:
            joined = urljoin(archive_url, link)
            if urlsplit(joined).scheme not in {"http", "https"}:
                continue
            url = normalize_url(joined)
            parts = urlsplit(url)
            if parts.hostname != "ptnk.edu.vn":
                continue
            folded = ascii_fold(parts.path.casefold())
            if not any(marker in folded for marker in ("de-thi", "dap-an", "huong-dan-cham")):
                continue
            if "/tuyen-sinh-ptnk/de-thi-dap-an" in parts.path:
                continue
            years = [int(value) for value in re.findall(r"20\d{2}", parts.path)]
            if not years:
                continue
            calendar_year = years[0]
            if start_year <= calendar_year <= end_year:
                results.add((calendar_year, url))
    return sorted(results)


def discover_official_assets(
    *,
    start_year: int,
    end_year: int,
    inventory_date: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    sources: list[dict[str, object]] = []
    candidates: list[dict[str, object]] = []
    for calendar_year, landing_url in discover_landing_pages(start_year, end_year):
        landing_html = fetch_text(landing_url)
        folders = sorted(set(DRIVE_FOLDER.findall(landing_html)))
        if not folders:
            continue
        source_id = deterministic_id("src", landing_url)
        page_type = classify_paper_type(landing_url)
        source_name = f"PTNK {calendar_year} official exam publication"
        source: dict[str, object] = {
            "source_id": source_id,
            "source_name": source_name,
            "source_url": landing_url,
            "normalized_url": landing_url,
            "source_domain": "ptnk.edu.vn",
            "source_organization": "Truong Pho thong Nang khieu, DHQG-HCM",
            "source_type": "official_school",
            "official_status": "official",
            "quality_tier": "authoritative",
            "exam_families": "ptnk",
            "acquisition_role": "exam_landing_page",
            "corpus_candidate": "yes",
            "date_or_vintage": str(calendar_year),
            "used_for": f"Official PTNK {page_type.replace('_', ' ')} availability",
            "workbook_locations": "discovered via official PTNK de thi/dap an archive",
            "inventory_date": inventory_date,
            "rights_status": "unknown",
            "safe_for_research_reference": "yes",
            "safe_for_internal_processing": "unknown",
            "safe_for_redistribution": "unknown",
            "safe_for_production_use": "unknown",
            "notes": "No explicit license or permission statement observed during discovery.",
        }
        source_dict = {key: str(value) for key, value in source.items()}
        matched = 0
        for folder_url in folders:
            for file_id, filename in iter_drive_files(folder_url, max_depth=2):
                folded_name = ascii_fold(filename.casefold())
                if (
                    "toan" not in folded_name
                    or "chuyen" not in folded_name
                    or "khong chuyen" in folded_name
                    or "toan kc" in folded_name
                ):
                    continue
                matched += 1
                paper_type = classify_paper_type(folded_name)
                if paper_type == "unknown":
                    paper_type = page_type
                download_url = (
                    "https://drive.usercontent.google.com/download"
                    f"?authuser=0&confirm=t&export=download&id={file_id}"
                )
                candidate = candidate_row(
                    source=source_dict,
                    source_url=download_url,
                    discovery_url=landing_url,
                    calendar_year=calendar_year,
                    academic_year=f"{calendar_year}-{calendar_year + 1}",
                    exam_variant="official_ptnk",
                    paper_type=paper_type,
                    expected_size="",
                    notes=f"Official PTNK Drive filename: {filename}",
                )
                candidates.append(candidate)
        if matched:
            sources.append(source)
    return sources, candidates


def iter_drive_files(folder_url: str, *, max_depth: int) -> list[tuple[str, str]]:
    pending = [(folder_url, 0)]
    visited: set[str] = set()
    files: dict[str, str] = {}
    while pending:
        current_url, depth = pending.pop(0)
        normalized = normalize_url(current_url)
        if normalized in visited:
            continue
        visited.add(normalized)
        folder_html = fetch_text(current_url)
        for file_id, encoded_name in DRIVE_FILE.findall(folder_html):
            filename = html.unescape(encoded_name)
            if filename.casefold().endswith("shared folder"):
                if depth < max_depth:
                    pending.append((f"https://drive.google.com/drive/folders/{file_id}", depth + 1))
                continue
            files[file_id] = filename
    return sorted(files.items())


def ascii_fold(value: str) -> str:
    import unicodedata

    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(character)
    ).replace("đ", "d")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover official PTNK exam assets.")
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--start-year", type=int, default=2017)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--inventory-date", default="2026-08-26")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sources, candidates = discover_official_assets(
        start_year=args.start_year,
        end_year=args.end_year,
        inventory_date=args.inventory_date,
    )
    existing_sources = read_csv(args.sources)
    existing_candidates = read_csv(args.plan) if args.plan.exists() else []
    write_csv(
        args.sources,
        SOURCE_FIELDS,
        merge_rows(existing_sources, sources, key="source_id"),
    )
    write_csv(
        args.plan,
        ACQUISITION_FIELDS,
        merge_rows(existing_candidates, candidates, key="candidate_id"),
    )
    print(f"Added {len(sources)} official source pages and {len(candidates)} PTNK assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
