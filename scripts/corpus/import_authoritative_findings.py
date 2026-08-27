from __future__ import annotations

import argparse
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlsplit

from scripts.corpus.core import (
    ACQUISITION_FIELDS,
    SOURCE_FIELDS,
    deterministic_id,
    merge_rows,
    normalize_url,
    read_csv,
    write_csv,
)
from scripts.corpus.discover_github_archives import candidate_row

DEFAULT_SOURCES = Path("data/corpus/manifests/sources.csv")
DEFAULT_PLAN = Path("data/corpus/manifests/acquisition_plan.csv")


class Evidence(TypedDict):
    family: str
    year: int
    organization: str
    source_type: str
    landing_url: str
    assets: tuple[tuple[str, str], ...]


EVIDENCE: tuple[Evidence, ...] = (
    {
        "family": "ptnk",
        "year": 2022,
        "organization": "Truong Pho thong Nang khieu, DHQG-HCM",
        "source_type": "official_school",
        "landing_url": "https://ptnk.edu.vn/de-thi-tuyen-sinh-lop-10-truong-ptnk-nam-hoc-2022-2023/",
        "assets": (
            (
                "question_paper",
                "https://ptnk.edu.vn/wp-content/uploads/2022/06/TOA%CC%81N-Chuye%CC%82n.pdf",
            ),
        ),
    },
    {
        "family": "ptnk",
        "year": 2023,
        "organization": "Truong Pho thong Nang khieu, DHQG-HCM",
        "source_type": "official_school",
        "landing_url": "https://ptnk.edu.vn/ky-thi-tuyen-sinh-10-nam-hoc-2023-2024-dap-an-cac-mon-chuyen/",
        "assets": (
            (
                "question_paper",
                "https://ptnk.edu.vn/wp-content/uploads/2023/06/De-thi-Toan-chuyen-2023-2024.pdf",
            ),
            (
                "answer_key",
                "https://ptnk.edu.vn/wp-content/uploads/2023/06/Dapan-Toan-Chuyen-2023-2024.pdf",
            ),
        ),
    },
    {
        "family": "hnue",
        "year": 2023,
        "organization": "Truong Dai hoc Su pham Ha Noi",
        "source_type": "official_university",
        "landing_url": "https://hnue.edu.vn/tin-tuc/9297/de-thi-va-dap-an-cac-mon-thi-tuyen-sinh-lop-10-truong-thpt-chuyen-dhsp-nam-2023.html",
        "assets": (
            (
                "question_paper",
                "https://drive.usercontent.google.com/download?authuser=0&confirm=t&export=download&id=1jceuwDMihi0bovw_VxbIJcKS61BpHafV",
            ),
            (
                "answer_key",
                "https://drive.usercontent.google.com/download?authuser=0&confirm=t&export=download&id=1WmCVNBXEo9p4ehkCOoY94S-Mm-sXUgCN",
            ),
        ),
    },
)


def build_rows(
    inventory_date: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    sources: list[dict[str, object]] = []
    candidates: list[dict[str, object]] = []
    for evidence in EVIDENCE:
        landing_url = normalize_url(str(evidence["landing_url"]))
        source_id = deterministic_id("src", landing_url)
        year = int(evidence["year"])
        family = str(evidence["family"])
        source_type = str(evidence["source_type"])
        source_name = f"{family.upper()} {year} official question/answer publication"
        source: dict[str, object] = {
            "source_id": source_id,
            "source_name": source_name,
            "source_url": landing_url,
            "normalized_url": landing_url,
            "source_domain": urlsplit(landing_url).hostname or "",
            "source_organization": str(evidence["organization"]),
            "source_type": source_type,
            "official_status": "official",
            "quality_tier": "authoritative",
            "exam_families": family,
            "acquisition_role": "exam_landing_page",
            "corpus_candidate": "yes",
            "date_or_vintage": str(year),
            "used_for": "Official actual specialized-Mathematics paper availability",
            "workbook_locations": "authoritative_source_findings.md",
            "inventory_date": inventory_date,
            "rights_status": "unknown",
            "safe_for_research_reference": "yes",
            "safe_for_internal_processing": "unknown",
            "safe_for_redistribution": "unknown",
            "safe_for_production_use": "unknown",
            "notes": "First-party publication; no explicit reuse licence found.",
        }
        sources.append(source)
        source_dict = {key: str(value) for key, value in source.items()}
        for paper_type, asset_url in evidence["assets"]:
            candidates.append(
                candidate_row(
                    source=source_dict,
                    source_url=str(asset_url),
                    discovery_url=landing_url,
                    calendar_year=year,
                    academic_year=f"{year}-{year + 1}",
                    exam_variant="official_actual",
                    paper_type=str(paper_type),
                    expected_size="",
                    notes="Direct asset linked from the first-party landing page.",
                )
            )
    return sources, candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import reviewed authoritative source findings.")
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--inventory-date", default="2026-08-26")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sources, candidates = build_rows(args.inventory_date)
    write_csv(
        args.sources,
        SOURCE_FIELDS,
        merge_rows(read_csv(args.sources), sources, key="source_id"),
    )
    write_csv(
        args.plan,
        ACQUISITION_FIELDS,
        merge_rows(read_csv(args.plan), candidates, key="candidate_id"),
    )
    print(f"Merged {len(sources)} authoritative pages and {len(candidates)} direct assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
