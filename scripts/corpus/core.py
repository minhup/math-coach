from __future__ import annotations

import csv
import hashlib
import re
from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")
MAIN_XML_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOCUMENT_REL_NAMESPACE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/relationships"

SOURCE_FIELDS = (
    "source_id",
    "source_name",
    "source_url",
    "normalized_url",
    "source_domain",
    "source_organization",
    "source_type",
    "official_status",
    "quality_tier",
    "exam_families",
    "acquisition_role",
    "corpus_candidate",
    "date_or_vintage",
    "used_for",
    "workbook_locations",
    "inventory_date",
    "rights_status",
    "safe_for_research_reference",
    "safe_for_internal_processing",
    "safe_for_redistribution",
    "safe_for_production_use",
    "notes",
)

ACQUISITION_FIELDS = (
    "candidate_id",
    "exam_family",
    "academic_year",
    "calendar_year",
    "exam_variant",
    "subject",
    "paper_type",
    "source_id",
    "source_url",
    "discovery_url",
    "source_name",
    "source_type",
    "official_status",
    "expected_mime_type",
    "expected_size",
    "selected",
    "rights_status",
    "notes",
)

FILE_FIELDS = (
    "file_id",
    "exam_family",
    "year",
    "academic_year",
    "exam_variant",
    "subject",
    "paper_type",
    "source_id",
    "source_url",
    "source_domain",
    "source_name",
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
    "duplicate_of_file_id",
    "language",
    "has_question_paper",
    "has_answer_key",
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

MISSING_DATA_FIELDS = (
    "issue_id",
    "exam_family",
    "year",
    "issue_type",
    "severity",
    "related_id",
    "source_url",
    "status",
    "details",
)

EXAM_FIELDS = (
    "exam_id",
    "exam_family",
    "school_or_authority",
    "city",
    "academic_year",
    "calendar_year",
    "paper_type",
    "subject",
    "duration_minutes",
    "maximum_score",
    "specialized_or_common",
    "round",
    "official_source_available",
    "question_file_id",
    "answer_file_id",
    "notes",
)

EXAM_FAMILIES = ("ptnk", "hcmc_so", "khtn", "hnue", "hanoi_so")


class CorpusError(ValueError):
    """Raised when corpus input violates a deterministic boundary."""


def normalize_url(value: str) -> str:
    parts = urlsplit(value.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise CorpusError(f"unsupported source URL: {value!r}")
    host = parts.hostname.lower().encode("idna").decode("ascii")
    port = parts.port
    if port and not (
        (parts.scheme.lower() == "http" and port == 80)
        or (parts.scheme.lower() == "https" and port == 443)
    ):
        host = f"{host}:{port}"
    path = parts.path or "/"
    query = urlencode(sorted(parse_qsl(parts.query, keep_blank_values=True)))
    return urlunsplit((parts.scheme.lower(), host, path, query, ""))


def deterministic_id(prefix: str, *parts: str) -> str:
    canonical = "\x1f".join(part.strip() for part in parts)
    return f"{prefix}_{hashlib.sha256(canonical.encode()).hexdigest()[:20]}"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, fields: Sequence[str], rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, extrasaction="raise", lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    temporary.replace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def merge_rows(
    existing: Iterable[Mapping[str, str]],
    incoming: Iterable[Mapping[str, object]],
    *,
    key: str,
) -> list[dict[str, object]]:
    merged: dict[str, dict[str, object]] = {row[key]: dict(row) for row in existing}
    for row in incoming:
        merged[str(row[key])] = dict(row)
    return [merged[value] for value in sorted(merged)]


def iter_xlsx_rows(path: Path) -> Iterator[tuple[str, int, dict[str, str]]]:
    """Yield visible workbook rows using only stable XLSX XML structures."""
    try:
        archive = ZipFile(path)
    except (BadZipFile, OSError) as error:
        raise CorpusError(f"cannot read workbook {path}: {error}") from error

    with archive:
        names = set(archive.namelist())
        shared_strings = _read_shared_strings(archive, names)
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        relationships = _read_relationships(archive, "xl/_rels/workbook.xml.rels")
        namespace = {"main": MAIN_XML_NAMESPACE, "rel": DOCUMENT_REL_NAMESPACE}
        sheets = workbook.find("main:sheets", namespace)
        if sheets is None:
            raise CorpusError("workbook has no sheets")
        for sheet in sheets:
            if sheet.attrib.get("state", "visible") != "visible":
                continue
            relation_id = sheet.attrib[f"{{{DOCUMENT_REL_NAMESPACE}}}id"]
            target = relationships[relation_id]
            sheet_path = _workbook_target(target)
            yield from _iter_sheet_rows(
                archive,
                sheet.attrib["name"],
                sheet_path,
                shared_strings,
            )


def _read_shared_strings(archive: ZipFile, names: set[str]) -> list[str]:
    if "xl/sharedStrings.xml" not in names:
        return []
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    namespace = {"main": MAIN_XML_NAMESPACE}
    return [
        "".join(text.text or "" for text in item.iterfind(".//main:t", namespace))
        for item in root.findall("main:si", namespace)
    ]


def _read_relationships(archive: ZipFile, path: str) -> dict[str, str]:
    root = ElementTree.fromstring(archive.read(path))
    return {
        relation.attrib["Id"]: relation.attrib["Target"]
        for relation in root.findall(f"{{{PACKAGE_REL_NAMESPACE}}}Relationship")
    }


def _workbook_target(target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return str(PurePosixPath("xl") / target)


def _iter_sheet_rows(
    archive: ZipFile,
    title: str,
    sheet_path: str,
    shared_strings: Sequence[str],
) -> Iterator[tuple[str, int, dict[str, str]]]:
    root = ElementTree.fromstring(archive.read(sheet_path))
    namespace = {"main": MAIN_XML_NAMESPACE}
    for row in root.findall(".//main:sheetData/main:row", namespace):
        values: dict[str, str] = {}
        for cell in row.findall("main:c", namespace):
            coordinate = cell.attrib["r"]
            column = re.match(r"[A-Z]+", coordinate)
            if column is None:
                continue
            value = _cell_value(cell, shared_strings, namespace)
            if value != "":
                values[column.group()] = value
        if values:
            yield title, int(row.attrib["r"]), values


def _cell_value(
    cell: ElementTree.Element,
    shared_strings: Sequence[str],
    namespace: dict[str, str],
) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(text.text or "" for text in cell.iterfind(".//main:is//main:t", namespace))
    raw = cell.findtext("main:v", default="", namespaces=namespace)
    if cell_type == "s" and raw:
        return shared_strings[int(raw)]
    return raw


def extract_urls(value: str) -> list[str]:
    return [match.rstrip(".,);]") for match in URL_PATTERN.findall(value)]
