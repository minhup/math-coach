from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from scripts.corpus.core import (
    EXAM_FAMILIES,
    SOURCE_FIELDS,
    CorpusError,
    deterministic_id,
    extract_urls,
    iter_xlsx_rows,
    normalize_url,
    write_csv,
)

DEFAULT_WORKBOOK = Path("docs/research/vietnam_chuyen_toan_competitive_dataset.xlsx")
DEFAULT_OUTPUT = Path("data/corpus/manifests/sources.csv")

ORGANIZATIONS = {
    "ptnk.edu.vn": "Truong Pho thong Nang khieu, DHQG-HCM",
    "hus.vnu.edu.vn": "Truong Dai hoc Khoa hoc Tu nhien, DHQGHN",
    "hnue.edu.vn": "Truong Dai hoc Su pham Ha Noi",
    "sovhtt.hanoi.gov.vn": "Uy ban nhan dan Thanh pho Ha Noi",
    "github.com": "GitHub / repository owner",
    "vnexpress.net": "VnExpress",
    "epaper.plo.vn": "Bao Phap Luat TP.HCM",
    "tuyensinh.mathexpress.vn": "MathExpress",
    "thongtin.mathexpress.vn": "MathExpress",
    "hoamatoan.edu.vn": "Hoa Ma Toan",
    "star-education.net": "STAR Education",
    "khoabang.edu.vn": "Khoa Bang",
    "luongxuanvinh.com": "Luong Xuan Vinh",
    "vio.edu.vn": "VioEdu",
}


@dataclass
class SourceEvidence:
    url: str
    names: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    date_or_vintage: str = ""
    used_for: str = ""
    families: set[str] = field(default_factory=set)


def build_inventory(workbook: Path, inventory_date: str) -> list[dict[str, object]]:
    evidence_by_url: dict[str, SourceEvidence] = {}
    source_metadata: dict[str, tuple[str, str, str, str]] = {}
    family_urls: dict[str, set[str]] = defaultdict(set)

    rows = list(iter_xlsx_rows(workbook))
    for sheet, row_number, cells in rows:
        if sheet == "Exam Systems" and row_number > 1:
            family = family_from_exam_name(cells.get("A", ""))
            for column in ("J", "K", "L"):
                for url in extract_urls(cells.get(column, "")):
                    family_urls[normalize_url(url)].add(family)
        if sheet == "Sources" and row_number > 1:
            urls = extract_urls(cells.get("C", ""))
            for url in urls:
                source_metadata[normalize_url(url)] = (
                    cells.get("A", ""),
                    cells.get("B", ""),
                    cells.get("D", ""),
                    cells.get("E", ""),
                )

    for sheet, row_number, cells in rows:
        row_name = cells.get("A", "")
        for column, value in cells.items():
            for url in extract_urls(value):
                normalized = normalize_url(url)
                evidence = evidence_by_url.setdefault(normalized, SourceEvidence(url=url))
                evidence.locations.append(f"{sheet}!{column}{row_number}")
                if row_name and row_name not in evidence.names:
                    evidence.names.append(row_name)
                evidence.families.update(family_urls.get(normalized, set()))

    records: list[dict[str, object]] = []
    for normalized, evidence in sorted(evidence_by_url.items()):
        metadata = source_metadata.get(normalized)
        source_name = metadata[0] if metadata else evidence.names[0]
        workbook_type = metadata[1] if metadata else ""
        date_or_vintage = metadata[2] if metadata else ""
        used_for = metadata[3] if metadata else ""
        domain = urlsplit(normalized).hostname or ""
        source_type, official_status, quality_tier = classify_source(domain, workbook_type)
        families = evidence.families or infer_families(source_name, normalized, used_for)
        acquisition_role, corpus_candidate = classify_role(
            source_name, source_type, used_for, families
        )
        records.append(
            {
                "source_id": deterministic_id("src", normalized),
                "source_name": source_name,
                "source_url": evidence.url,
                "normalized_url": normalized,
                "source_domain": domain,
                "source_organization": ORGANIZATIONS.get(domain, domain),
                "source_type": source_type,
                "official_status": official_status,
                "quality_tier": quality_tier,
                "exam_families": "|".join(sorted(families)),
                "acquisition_role": acquisition_role,
                "corpus_candidate": corpus_candidate,
                "date_or_vintage": date_or_vintage,
                "used_for": used_for,
                "workbook_locations": "|".join(sorted(set(evidence.locations))),
                "inventory_date": inventory_date,
                "rights_status": "unknown",
                "safe_for_research_reference": "yes",
                "safe_for_internal_processing": "unknown",
                "safe_for_redistribution": "unknown",
                "safe_for_production_use": "unknown",
                "notes": "No explicit license or permission is stated in the workbook.",
            }
        )
    return records


def family_from_exam_name(value: str) -> str:
    lowered = value.casefold()
    if "ptnk" in lowered:
        return "ptnk"
    if "khtn" in lowered:
        return "khtn"
    if "hnue" in lowered or "su pham" in lowered:
        return "hnue"
    if "ha noi" in _without_diacritics(lowered):
        return "hanoi_so"
    if "tp.hcm" in lowered:
        return "hcmc_so"
    raise CorpusError(f"unrecognized exam family: {value!r}")


def _without_diacritics(value: str) -> str:
    import unicodedata

    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(character)
    ).replace("đ", "d")


def classify_source(domain: str, workbook_type: str) -> tuple[str, str, str]:
    type_hint = workbook_type.casefold()
    if domain == "ptnk.edu.vn" or "official school" in type_hint:
        return "official_school", "official", "authoritative"
    if domain in {"hus.vnu.edu.vn", "hnue.edu.vn"} or "official university" in type_hint:
        return "official_university", "official", "authoritative"
    if domain.endswith("hanoi.gov.vn") or "government" in type_hint:
        return "government", "official", "authoritative"
    if domain == "github.com":
        return "community_github_archive", "third_party", "strong_archive"
    if domain in {"vnexpress.net", "epaper.plo.vn"}:
        return "news_reporting", "third_party", "secondary"
    if domain in {
        "tuyensinh.mathexpress.vn",
        "thongtin.mathexpress.vn",
        "hoamatoan.edu.vn",
        "star-education.net",
        "khoabang.edu.vn",
    }:
        return "commercial_tutoring", "third_party", "commercial_reference_only"
    if domain == "luongxuanvinh.com":
        return "teacher_site", "third_party", "commercial_reference_only"
    if domain == "vio.edu.vn":
        return "commercial_platform", "third_party", "commercial_reference_only"
    return "unknown", "unknown", "uncertain"


def infer_families(source_name: str, normalized_url: str, used_for: str) -> set[str]:
    text = _without_diacritics(f"{source_name} {normalized_url} {used_for}".casefold())
    families: set[str] = set()
    if "ptnk" in text or "pho-thong-nang-khieu" in text:
        families.add("ptnk")
    if "khtn" in text or "khoa-hoc-tu-nhien" in text:
        families.add("khtn")
    if "hnue" in text or "sphn" in text or "su pham" in text:
        families.add("hnue")
    if "hanoi" in text or "ha noi" in text or "hoa ma" in text or "khoa bang" in text:
        families.add("hanoi_so")
    if "tp.hcm" in text or "hcmc" in text or "star" in text or "luong xuan vinh" in text:
        families.add("hcmc_so")
    if "mathexpress" in text:
        families.update({"khtn", "hnue", "hanoi_so"})
    return families.intersection(EXAM_FAMILIES)


def classify_role(
    source_name: str,
    source_type: str,
    used_for: str,
    families: set[str],
) -> tuple[str, str]:
    text = f"{source_name} {used_for}".casefold()
    if source_type == "community_github_archive":
        return "archive_discovery", "yes"
    if "official exam" in text:
        return "exam_landing_page", "yes"
    if "solution" in text or "dap an" in _without_diacritics(text):
        return "commercial_solution_reference", "yes"
    if source_type in {"official_school", "official_university", "government"}:
        return "exam_system_evidence", "yes" if families else "no"
    if source_type == "news_reporting":
        return "exam_system_evidence", "no"
    return "market_context", "no"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the workbook-derived source inventory.")
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--inventory-date", default=datetime.now(UTC).date().isoformat())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = build_inventory(args.workbook, args.inventory_date)
    write_csv(args.output, SOURCE_FIELDS, records)
    print(f"Wrote {len(records)} source records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
