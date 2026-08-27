from __future__ import annotations

import argparse
import shutil
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from scripts.corpus.core import (
    FILE_FIELDS,
    deterministic_id,
    merge_rows,
    normalize_url,
    read_csv,
    sha256_file,
    write_csv,
)
from scripts.corpus.reconciliation import (
    CORE_ADJACENT_QUESTIONS,
    CORE_BLOCKED_HTML,
    CORE_SOLUTION_FILES,
    LAM_SON_MANUAL_PATH,
    LAM_SON_SOURCE_URL,
    MANUAL_IMPORT_FIELDS,
)
from scripts.corpus.registry import (
    REGISTRY_ACQUISITION_FIELDS,
    REGISTRY_FILE_FIELDS,
    candidate_row,
)

DEFAULT_MANIFESTS = Path("data/corpus/manifests")
DEFAULT_RAW_ROOT = Path("data/corpus/raw/registry")
JBMO_RECOVERY = (
    (
        "https://jbmo2025.1c.mk/sites/template/docs/0c27280bc9d65f05f7291770acb62786.pdf",
        "https://jbmo2025.1c.mk/problems",
        "2025",
        "question",
        "202185",
        "Organizer-site successor linked from the current JBMO host; host caveat documented.",
    ),
    (
        "https://jbmo2025.1c.mk/sites/template/docs/d2e0d1ddf6051a01a7bfebb637298874.pdf",
        "https://jbmo2025.1c.mk/problems",
        "2025",
        "solution",
        "496106",
        "Organizer page labels this Problems with solutions; host caveat documented.",
    ),
    (
        "https://jbmo2026.ssmr.ro/wp-content/uploads/2026/06/English_JBMO2026.pdf",
        "https://jbmo2026.ssmr.ro/problems/",
        "2026",
        "question",
        "89882",
        "Official JBMO 2026 English problem paper.",
    ),
)


def append_note_once(existing: object, note: str) -> str:
    current = str(existing).strip()
    if note in current:
        return current
    return f"{current} {note}".strip()


def recovery_candidates() -> list[dict[str, object]]:
    return [
        candidate_row(
            collection_id="J06",
            source_url=url,
            discovery_url=landing,
            url_role="official",
            source_type="official_organization",
            official_status="official",
            acquisition_method="official_direct_file",
            expected_size=size,
            year_hint=year,
            artifact_hint=kind,
            notes=notes,
        )
        for url, landing, year, kind, size, notes in JBMO_RECOVERY
    ]


def classify_core_files(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    classified: list[dict[str, object]] = []
    for source in rows:
        row: dict[str, object] = dict(source)
        file_id = source["file_id"]
        if file_id in CORE_SOLUTION_FILES:
            note = (
                "AI_SUGGESTED_LABEL: visual/content review classifies this third-party "
                "document as a worked solution."
            )
            row.update(
                paper_type="answer_key",
                has_question_paper="no",
                has_answer_key="yes",
                notes=append_note_once(source["notes"], note),
            )
        elif file_id in CORE_ADJACENT_QUESTIONS:
            note = (
                "AI_SUGGESTED_LABEL: visible header identifies a non-target Chuyên Tin "
                "paper; retained as an adjacent set."
            )
            row.update(
                paper_type="adjacent_question",
                has_question_paper="yes",
                has_answer_key="no",
                notes=append_note_once(source["notes"], note),
            )
        elif source["paper_type"] == "unknown":
            note = (
                "AI_SUGGESTED_LABEL: visual review classifies this as a question-paper "
                "representation; set reconciliation records alternates."
            )
            row.update(
                paper_type="question_paper",
                has_question_paper="yes",
                has_answer_key="no",
                notes=append_note_once(source["notes"], note),
            )
        if file_id in CORE_BLOCKED_HTML:
            note = (
                "SOURCE_FACT: saved bytes are a Google Drive permission/error page, not "
                "the intended document."
            )
            row["notes"] = append_note_once(row["notes"], note)
            row["processing_status"] = "blocked_access"
        classified.append(row)
    return classified


def manual_bundle_candidate(file_id: str) -> dict[str, object]:
    return {
        "candidate_id": file_id,
        "collection_id": "V06",
        "logical_set_id": deterministic_id("bundle", "V06", "lam_son_compilation"),
        "year": "",
        "artifact_type": "bundle",
        "source_url": LAM_SON_SOURCE_URL,
        "discovery_url": "",
        "url_role": "owner_provided",
        "source_type": "commercial_reference",
        "official_status": "third_party",
        "expected_mime_type": "application/pdf",
        "expected_size": "",
        "selected": "yes",
        "acquisition_method": "manual_owner_import",
        "language": "vi",
        "notes": (
            "Owner-provided local compilation. Embedded publisher homepage preserved; exact "
            "download URL is unknown."
        ),
    }


def import_manual_bundle(
    *, source: Path, raw_root: Path, retrieved_at: str
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    digest = sha256_file(source)
    file_id = deterministic_id("manual", "V06", digest)
    candidate = manual_bundle_candidate(file_id)
    destination = raw_root / "V06" / "unassigned" / f"{file_id}.pdf"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256_file(destination) != digest:
            raise ValueError(f"immutable destination has different bytes: {destination}")
    else:
        temporary = destination.with_suffix(".pdf.part")
        shutil.copyfile(source, temporary)
        if sha256_file(temporary) != digest:
            temporary.unlink(missing_ok=True)
            raise ValueError("manual import checksum changed during copy")
        temporary.replace(destination)
    file_row: dict[str, object] = {field: "" for field in REGISTRY_FILE_FIELDS}
    file_row.update(
        {
            "file_id": file_id,
            "collection_id": "V06",
            "logical_set_id": candidate["logical_set_id"],
            "artifact_type": "bundle",
            "source_url": LAM_SON_SOURCE_URL,
            "source_domain": urlsplit(normalize_url(LAM_SON_SOURCE_URL)).hostname or "",
            "url_role": "owner_provided",
            "source_type": "commercial_reference",
            "official_status": "third_party",
            "retrieved_at": retrieved_at,
            "http_status": "manual_import",
            "final_url": "",
            "original_filename": source.name,
            "local_path": destination.as_posix(),
            "mime_type": "application/pdf",
            "detected_mime_type": "application/pdf",
            "file_size": source.stat().st_size,
            "sha256": digest,
            "language": "vi",
            "rights_status": "unknown",
            "processing_status": "downloaded",
            "page_count": "181",
            "text_extractable": "true",
            "text_extraction_quality": "machine_generated_unverified",
            "scan_quality": "born_digital",
            "extraction_method": "native_pdf_text",
            "notes": candidate["notes"],
        }
    )
    import_row: dict[str, object] = {
        "manual_import_id": deterministic_id("mimport", digest),
        "collection_id": "V06",
        "original_local_path": source.as_posix(),
        "original_filename": source.name,
        "embedded_source_url": LAM_SON_SOURCE_URL,
        "exact_source_url": "",
        "provenance_status": "owner_provided_exact_download_url_unknown",
        "imported_file_id": file_id,
        "canonical_raw_path": destination.as_posix(),
        "sha256": digest,
        "file_size": source.stat().st_size,
        "imported_at": retrieved_at,
        "notes": (
            "Byte-identical immutable import. The PDF identifies tailieumontoan.com and Nguyễn "
            "Quốc Bảo; no exact download URL was supplied."
        ),
    }
    return candidate, file_row, import_row


def prepare(
    *, manifests: Path, raw_root: Path, manual_source: Path, retrieved_at: str
) -> tuple[int, bool]:
    plan_path = manifests / "registry_acquisition_plan.csv"
    registry_files_path = manifests / "registry_files.csv"
    core_files_path = manifests / "files.csv"
    manual_path = manifests / "manual_imports.csv"

    plan = read_csv(plan_path)
    incoming_plan: list[dict[str, object]] = recovery_candidates()
    registry_files = read_csv(registry_files_path)
    manual_rows = read_csv(manual_path) if manual_path.exists() else []
    output_registry_files: list[dict[str, object]] = [dict(row) for row in registry_files]
    output_manual_rows: list[dict[str, object]] = [dict(row) for row in manual_rows]
    imported = False
    if manual_source.is_file():
        prior_import = next(
            (row for row in manual_rows if row["original_local_path"] == manual_source.as_posix()),
            None,
        )
        stable_retrieved_at = (
            prior_import["imported_at"]
            if prior_import and prior_import.get("imported_at")
            else retrieved_at
        )
        candidate, file_row, import_row = import_manual_bundle(
            source=manual_source,
            raw_root=raw_root,
            retrieved_at=stable_retrieved_at,
        )
        prior_file = next(
            (row for row in registry_files if row["file_id"] == file_row["file_id"]),
            None,
        )
        if prior_file:
            file_row.clear()
            file_row.update(prior_file)
        incoming_plan.append(candidate)
        output_registry_files = merge_rows(registry_files, [file_row], key="file_id")
        output_manual_rows = merge_rows(manual_rows, [import_row], key="manual_import_id")
        imported = True

    write_csv(
        plan_path,
        REGISTRY_ACQUISITION_FIELDS,
        merge_rows(plan, incoming_plan, key="candidate_id"),
    )
    write_csv(registry_files_path, REGISTRY_FILE_FIELDS, output_registry_files)
    write_csv(manual_path, MANUAL_IMPORT_FIELDS, output_manual_rows)
    write_csv(core_files_path, FILE_FIELDS, classify_core_files(read_csv(core_files_path)))
    return len(incoming_plan), imported


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare verified recovery candidates and local manual corpus imports."
    )
    parser.add_argument("--manifests", type=Path, default=DEFAULT_MANIFESTS)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--manual-source", type=Path, default=LAM_SON_MANUAL_PATH)
    parser.add_argument(
        "--retrieved-at",
        default=datetime.now(UTC).isoformat(timespec="seconds"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates, imported = prepare(
        manifests=args.manifests,
        raw_root=args.raw_root,
        manual_source=args.manual_source,
        retrieved_at=args.retrieved_at,
    )
    print(
        f"Prepared {candidates} reconciliation candidates; "
        f"manual Lam Son bundle {'imported' if imported else 'not present'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
