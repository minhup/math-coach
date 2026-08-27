from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
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

DEFAULT_MANIFESTS = Path("data/corpus/manifests")

# A raw bundle is stored once even when page ranges represent several examination cycles.
# Solutions embedded in these sources are preserved but deliberately not mapped as components.


@dataclass(frozen=True)
class RecoveryItem:
    family: str
    storage_year: int
    academic_year: str
    direct_url: str
    landing_url: str
    source_name: str
    source_organization: str
    source_type: str
    quality_tier: str
    paper_type: str
    expected_mime_type: str
    expected_size: str
    components: tuple[tuple[int, int | None, int | None], ...]
    notes: str


RECOVERY_ITEMS = (
    RecoveryItem(
        family="hcmc_so",
        storage_year=2026,
        academic_year="2026-2027",
        direct_url="https://thcs.toanmath.com/thcs-pdf/de-tuyen-sinh-lop-10-mon-toan-chuyen-nam-2026-2027-so-gddt-tp-hcm.pdf",
        landing_url="https://thcs.toanmath.com/2026/06/de-tuyen-sinh-lop-10-mon-toan-chuyen-nam-2026-2027-so-gddt-tp-hcm.html",
        source_name="TOANMATH mirror — TP.HCM Sở Chuyên 2026",
        source_organization="TOANMATH",
        source_type="public_mirror",
        quality_tier="secondary",
        paper_type="question_solution_bundle",
        expected_mime_type="application/pdf",
        expected_size="1822647",
        components=((2026, 1, 2),),
        notes=(
            "Pages 1-2 reproduce the complete question paper; later worked-solution pages "
            "are not processed in this question-only pass."
        ),
    ),
    RecoveryItem(
        family="hanoi_so",
        storage_year=2018,
        academic_year="2018-2019",
        direct_url="https://www.onthi123.vn/public/uploads/bo-de-thi-vao-10-chuyen-toan-tin-so-gddt-ha-noi.pdf",
        landing_url="https://www.onthi123.vn/public/uploads/bo-de-thi-vao-10-chuyen-toan-tin-so-gddt-ha-noi.pdf",
        source_name="OnThi123 Hà Nội Chuyên Toán-Tin compilation",
        source_organization="OnThi123",
        source_type="commercial_tutoring",
        quality_tier="commercial_reference_only",
        paper_type="question_solution_bundle",
        expected_mime_type="application/pdf",
        expected_size="16765663",
        components=((2018, 7, 7),),
        notes=(
            "Visible source header identifies page 7 as the official 2018-2019 Chuyên Toán "
            "paper; solution pages are not processed in this question-only pass."
        ),
    ),
    RecoveryItem(
        family="hanoi_so",
        storage_year=2025,
        academic_year="2025-2026",
        direct_url="https://thcs.toanmath.com/wp-content/uploads/2025/06/de-tuyen-sinh-lop-10-mon-toan-chuyen-nam-2025-2026-so-gddt-ha-noi.png",
        landing_url="https://thcs.toanmath.com/2025/06/de-tuyen-sinh-lop-10-mon-toan-chuyen-nam-2025-2026-so-gddt-ha-noi.html",
        source_name="TOANMATH mirror — Hà Nội Sở Chuyên 2025",
        source_organization="TOANMATH",
        source_type="public_mirror",
        quality_tier="secondary",
        paper_type="question_paper",
        expected_mime_type="image/png",
        expected_size="",
        components=((2025, None, None),),
        notes=(
            "Single image visibly identifies the official 2025-2026 Chuyên Toán paper; no "
            "solution artifact is selected."
        ),
    ),
    RecoveryItem(
        family="hanoi_so",
        storage_year=2026,
        academic_year="2026-2027",
        direct_url="https://thcs.toanmath.com/wp-content/uploads/2026/06/de-tuyen-sinh-lop-10-mon-toan-chuyen-nam-2026-2027-so-gddt-ha-noi.png",
        landing_url="https://thcs.toanmath.com/2026/06/de-tuyen-sinh-lop-10-mon-toan-chuyen-nam-2026-2027-so-gddt-ha-noi.html",
        source_name="TOANMATH mirror — Hà Nội Sở Chuyên 2026",
        source_organization="TOANMATH",
        source_type="public_mirror",
        quality_tier="secondary",
        paper_type="question_paper",
        expected_mime_type="image/png",
        expected_size="",
        components=((2026, None, None),),
        notes=(
            "Single image visibly identifies the official 2026-2027 Chuyên Toán paper; no "
            "solution artifact is selected."
        ),
    ),
    RecoveryItem(
        family="khtn",
        storage_year=2017,
        academic_year="2017-2018",
        direct_url="https://www.onthi123.vn/do-download-document?document=227&v=1774095015",
        landing_url="https://www.onthi123.vn/do-download-document?document=227&v=1774095015",
        source_name="OnThi123 KHTN multi-year compilation",
        source_organization="OnThi123",
        source_type="commercial_tutoring",
        quality_tier="commercial_reference_only",
        paper_type="question_solution_bundle",
        expected_mime_type="application/pdf",
        expected_size="18155837",
        components=((2017, 20, 20), (2018, 22, 22)),
        notes=(
            "Stored once: visible headers identify pages 20 and 22 as the 2017-2018 and "
            "2018-2019 KHTN round-2 question papers. Solution pages are deferred."
        ),
    ),
    RecoveryItem(
        family="khtn",
        storage_year=2026,
        academic_year="2026-2027",
        direct_url="https://thcs.toanmath.com/wp-content/uploads/2026/05/de-tuyen-sinh-lop-10-mon-toan-vong-2-nam-2026-truong-thpt-chuyen-khtn-ha-noi.png",
        landing_url="https://thcs.toanmath.com/2026/05/de-tuyen-sinh-lop-10-mon-toan-vong-2-nam-2026-truong-thpt-chuyen-khtn-ha-noi.html",
        source_name="TOANMATH mirror — KHTN round 2 2026",
        source_organization="TOANMATH",
        source_type="public_mirror",
        quality_tier="secondary",
        paper_type="question_paper",
        expected_mime_type="image/png",
        expected_size="",
        components=((2026, None, None),),
        notes=(
            "Single image visibly identifies the official 2026 KHTN round-2 paper; no "
            "solution artifact is selected."
        ),
    ),
    RecoveryItem(
        family="hnue",
        storage_year=2026,
        academic_year="2026-2027",
        direct_url="https://thcs.toanmath.com/thcs-pdf/bo-de-tuyen-sinh-lop-10-mon-toan-chuyen-nam-2026-2027-co-loi-giai-chi-tiet.pdf",
        landing_url="https://thcs.toanmath.com/2026/06/bo-de-tuyen-sinh-lop-10-mon-toan-chuyen-nam-2026-2027-co-loi-giai-chi-tiet.html",
        source_name="TOANMATH nationwide Chuyên 2026 bundle",
        source_organization="TOANMATH / Câu lạc bộ Toán A1",
        source_type="public_mirror",
        quality_tier="secondary",
        paper_type="question_solution_bundle",
        expected_mime_type="application/pdf",
        expected_size="935292",
        components=((2026, 24, 25),),
        notes=(
            "Pages 24-25 are explicitly headed Chuyên Sư phạm vòng 2 and contain the complete "
            "question set. Worked solutions are not processed in this pass."
        ),
    ),
)


def recovery_candidate_id(item: RecoveryItem) -> str:
    return deterministic_id(
        "cand",
        item.family,
        str(item.storage_year),
        normalize_url(item.direct_url),
    )


def recovery_components() -> dict[str, tuple[tuple[int, int | None, int | None], ...]]:
    return {recovery_candidate_id(item): item.components for item in RECOVERY_ITEMS}


def recovery_target_years(file_id: str) -> set[int]:
    return {year for year, _start, _end in recovery_components().get(file_id, ())}


def source_row(item: RecoveryItem, inventory_date: str) -> dict[str, object]:
    landing_url = item.landing_url
    normalized = normalize_url(landing_url)
    return {
        "source_id": deterministic_id("src", normalized),
        "source_name": item.source_name,
        "source_url": landing_url,
        "normalized_url": normalized,
        "source_domain": urlsplit(normalized).hostname or "",
        "source_organization": item.source_organization,
        "source_type": item.source_type,
        "official_status": "third_party",
        "quality_tier": item.quality_tier,
        "exam_families": item.family,
        "acquisition_role": "question_recovery",
        "corpus_candidate": "yes",
        "date_or_vintage": str(item.storage_year),
        "used_for": "Question-only recovery for missing core exam cycle",
        "workbook_locations": "Expanded registry acquisition lead",
        "inventory_date": inventory_date,
        "rights_status": "unknown",
        "safe_for_research_reference": "yes",
        "safe_for_internal_processing": "yes",
        "safe_for_redistribution": "unknown",
        "safe_for_production_use": "unknown",
        "notes": (
            "Third-party question mirror; identity is source-cross-checked, not "
            "mathematics-expert verified."
        ),
    }


def candidate_row(item: RecoveryItem, source_id: str) -> dict[str, object]:
    return {
        "candidate_id": recovery_candidate_id(item),
        "exam_family": item.family,
        "academic_year": item.academic_year,
        "calendar_year": item.storage_year,
        "exam_variant": "question_recovery_"
        + ("bundle" if item.paper_type == "question_solution_bundle" else "image"),
        "subject": "mathematics",
        "paper_type": item.paper_type,
        "source_id": source_id,
        "source_url": item.direct_url,
        "discovery_url": item.landing_url,
        "source_name": item.source_name,
        "source_type": item.source_type,
        "official_status": "third_party",
        "expected_mime_type": item.expected_mime_type,
        "expected_size": item.expected_size,
        "selected": "yes",
        "rights_status": "unknown",
        "notes": item.notes,
    }


def prepare(manifests: Path, inventory_date: str) -> None:
    sources_path = manifests / "sources.csv"
    plan_path = manifests / "acquisition_plan.csv"
    existing_sources = read_csv(sources_path)
    existing_plan = read_csv(plan_path)
    new_sources = [source_row(item, inventory_date) for item in RECOVERY_ITEMS]
    source_ids = {
        str(row["normalized_url"]): str(row["source_id"])
        for row in merge_rows(existing_sources, new_sources, key="source_id")
    }
    new_candidates = [
        candidate_row(item, source_ids[normalize_url(item.landing_url)]) for item in RECOVERY_ITEMS
    ]
    write_csv(
        sources_path,
        SOURCE_FIELDS,
        merge_rows(existing_sources, new_sources, key="source_id"),
    )
    write_csv(
        plan_path,
        ACQUISITION_FIELDS,
        merge_rows(existing_plan, new_candidates, key="candidate_id"),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add source-backed, question-only recovery candidates to the core plan."
    )
    parser.add_argument("--manifests", type=Path, default=DEFAULT_MANIFESTS)
    parser.add_argument("--inventory-date", default="2026-08-27")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prepare(args.manifests, args.inventory_date)
    print(f"Prepared {len(RECOVERY_ITEMS)} question-recovery source candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
