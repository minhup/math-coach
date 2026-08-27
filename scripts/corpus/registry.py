from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlsplit

from scripts.corpus.core import deterministic_id, extract_urls, normalize_url

REGISTRY_COLLECTION_FIELDS = (
    "collection_id",
    "priority",
    "acquisition_wave",
    "country_region",
    "source_name",
    "category",
    "age_grade",
    "format",
    "years_volume",
    "agent_action",
    "recommended_scope",
    "why_useful",
    "rights_access_note",
    "fit",
    "notes",
    "selected_initial_wave",
    "workbook_sheet",
    "workbook_row",
    "inventory_date",
)

REGISTRY_URL_FIELDS = (
    "registry_url_id",
    "collection_id",
    "url_role",
    "source_url",
    "normalized_url",
    "source_domain",
    "source_type",
    "official_status",
    "quality_tier",
    "inventory_date",
    "rights_status",
    "notes",
)

REGISTRY_ACQUISITION_FIELDS = (
    "candidate_id",
    "collection_id",
    "logical_set_id",
    "year",
    "artifact_type",
    "source_url",
    "discovery_url",
    "url_role",
    "source_type",
    "official_status",
    "expected_mime_type",
    "expected_size",
    "selected",
    "acquisition_method",
    "language",
    "notes",
)

REGISTRY_FILE_FIELDS = (
    "file_id",
    "collection_id",
    "logical_set_id",
    "year",
    "artifact_type",
    "source_url",
    "discovery_url",
    "source_domain",
    "url_role",
    "source_type",
    "official_status",
    "retrieved_at",
    "http_status",
    "final_url",
    "original_filename",
    "local_path",
    "mime_type",
    "detected_mime_type",
    "file_size",
    "sha256",
    "byte_duplicate_of_file_id",
    "semantic_duplicate_of_file_id",
    "language",
    "rights_status",
    "processing_status",
    "page_count",
    "text_extractable",
    "text_extraction_quality",
    "scan_quality",
    "extraction_method",
    "extracted_text_path",
    "notes",
)

REGISTRY_MISSING_FIELDS = (
    "issue_id",
    "collection_id",
    "logical_set_id",
    "year",
    "issue_type",
    "severity",
    "related_id",
    "source_url",
    "status",
    "details",
)

USABLE_REGISTRY_STATUSES = {"downloaded", "downloaded_reused", "validated", "extracted"}
DOCUMENT_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx", ".zip"}
MIME_BY_SUFFIX = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".zip": "application/zip",
}

URL_COLUMNS = {"I": "official", "J": "mirror_1", "K": "mirror_2", "L": "direct_bundle"}
LEGACY_COLLECTION_FAMILIES = {
    "V01": "ptnk",
    "V02": "hcmc_so",
    "V03": "hanoi_so",
    "V04": "khtn",
    "V05": "hnue",
}


def collection_wave(collection_id: str, priority: str) -> str:
    if priority == "P0":
        return "wave_1_vietnam_core"
    if priority == "P0X":
        return "wave_2_jbmo_core"
    if collection_id.startswith("V"):
        return "wave_1b_vietnam_expansion"
    if priority.endswith("X"):
        return "wave_3_junior_national"
    if priority == "P1":
        return "wave_4_transfer"
    return "wave_5_curated_stretch"


def parse_master_row(
    cells: Mapping[str, str], *, row_number: int, inventory_date: str
) -> dict[str, object]:
    collection_id = cells.get("A", "").strip()
    priority = cells.get("B", "").strip()
    if not re.fullmatch(r"[VJG]\d{2}", collection_id):
        raise ValueError(f"invalid registry collection ID at row {row_number}: {collection_id!r}")
    return {
        "collection_id": collection_id,
        "priority": priority,
        "acquisition_wave": collection_wave(collection_id, priority),
        "country_region": cells.get("C", ""),
        "source_name": cells.get("D", ""),
        "category": cells.get("E", ""),
        "age_grade": cells.get("F", ""),
        "format": cells.get("G", ""),
        "years_volume": cells.get("H", ""),
        "agent_action": cells.get("N", ""),
        "recommended_scope": cells.get("O", ""),
        "why_useful": cells.get("P", ""),
        "rights_access_note": cells.get("Q", ""),
        "fit": cells.get("R", ""),
        "notes": cells.get("S", ""),
        "selected_initial_wave": "yes" if priority in {"P0", "P0X"} else "no",
        "workbook_sheet": "Master Download Queue",
        "workbook_row": row_number,
        "inventory_date": inventory_date,
    }


def url_rows(
    cells: Mapping[str, str], *, collection_id: str, inventory_date: str
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for column, role in URL_COLUMNS.items():
        for url in extract_urls(cells.get(column, "")):
            normalized = normalize_url(url)
            domain = urlsplit(normalized).hostname or ""
            source_type, official_status, quality = classify_registry_url(domain, role)
            rows.append(
                {
                    "registry_url_id": deterministic_id("rurl", collection_id, role, normalized),
                    "collection_id": collection_id,
                    "url_role": role,
                    "source_url": url,
                    "normalized_url": normalized,
                    "source_domain": domain,
                    "source_type": source_type,
                    "official_status": official_status,
                    "quality_tier": quality,
                    "inventory_date": inventory_date,
                    "rights_status": "unknown",
                    "notes": f"Workbook role {role}; no rights conclusion inferred.",
                }
            )
    return rows


def classify_registry_url(domain: str, role: str) -> tuple[str, str, str]:
    if domain == "github.com":
        return "community_github_archive", "third_party", "strong_archive"
    if domain in {"drive.google.com", "docs.google.com"}:
        return "public_bundle_mirror", "third_party", "strong_archive"
    if domain in {"artofproblemsolving.com", "imomath.com", "www.imomath.com"}:
        return "community_archive", "third_party", "strong_archive"
    if domain.endswith(("blogspot.com", "ucoz.org")):
        return "community_archive", "third_party", "strong_archive"
    if role == "official":
        return "official_organization", "official", "authoritative"
    if domain.endswith((".gov.vn", ".gov.hk")):
        return "government", "official", "authoritative"
    if ".edu." in domain or domain.endswith((".edu", ".ac.jp")):
        return "educational_organization", "unknown", "secondary"
    return "public_mirror", "third_party", "secondary"


def github_repository_path(url: str) -> tuple[str, str] | None:
    parts = urlsplit(normalize_url(url))
    path = [piece for piece in parts.path.split("/") if piece]
    if parts.hostname != "github.com" or len(path) != 2:
        return None
    return path[0], path[1].removesuffix(".git")


def direct_document_url(url: str) -> bool:
    return Path(urlsplit(normalize_url(url)).path).suffix.casefold() in DOCUMENT_SUFFIXES


def expected_mime(url: str) -> str:
    return MIME_BY_SUFFIX.get(Path(urlsplit(url).path).suffix.casefold(), "unknown")


def fold(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(character)
    ).replace("đ", "d")


def infer_year(*values: str) -> str:
    for value in values:
        match = re.search(r"(?<!\d)((?:19|20)\d{2})(?!\d)", value)
        if match:
            return match.group(1)
    return ""


def artifact_type(value: str) -> str:
    text = fold(value)
    words = re.sub(r"[^a-z0-9]+", " ", text)
    if "shortlist" in text or re.search(r"\bshl\b", words):
        return "shortlist"
    if re.search(r"\b(?:solutions?|answers?|dap an|dapan|barem)\b", words):
        return "solution"
    if re.search(
        r"\b(?:problems?|questions?|de thi|exams?|papers?|official version|english)\b",
        words,
    ):
        return "question"
    if re.search(r"\.zip(?:\b|$)", text):
        return "bundle"
    return "unknown"


def logical_set_id(collection_id: str, year: str, kind: str) -> str:
    set_kind = "shortlist" if kind == "shortlist" else "contest"
    return deterministic_id("set", collection_id, year or "unassigned", set_kind)


def candidate_row(
    *,
    collection_id: str,
    source_url: str,
    discovery_url: str,
    url_role: str,
    source_type: str,
    official_status: str,
    acquisition_method: str,
    expected_size: str = "",
    year_hint: str = "",
    artifact_hint: str = "",
    selected: str = "yes",
    notes: str = "",
) -> dict[str, object]:
    normalized = normalize_url(source_url)
    year = infer_year(year_hint, source_url, discovery_url)
    kind = artifact_hint or artifact_type(source_url)
    return {
        "candidate_id": deterministic_id("gcand", collection_id, normalized),
        "collection_id": collection_id,
        "logical_set_id": logical_set_id(collection_id, year, kind),
        "year": year,
        "artifact_type": kind,
        "source_url": source_url,
        "discovery_url": discovery_url,
        "url_role": url_role,
        "source_type": source_type,
        "official_status": official_status,
        "expected_mime_type": expected_mime(normalized),
        "expected_size": expected_size,
        "selected": selected,
        "acquisition_method": acquisition_method,
        "language": "unknown",
        "notes": notes,
    }
