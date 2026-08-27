from __future__ import annotations

import argparse
import re
import subprocess
from collections import defaultdict
from pathlib import Path

from scripts.corpus.core import (
    EXAM_FAMILIES,
    FILE_FIELDS,
    MISSING_DATA_FIELDS,
    deterministic_id,
    merge_rows,
    normalize_url,
    read_csv,
    sha256_file,
    write_csv,
)
from scripts.corpus.download_sources import detect_mime

DEFAULT_FILES = Path("data/corpus/manifests/files.csv")
DEFAULT_MISSING = Path("data/corpus/manifests/missing_data.csv")
DEFAULT_SOURCES = Path("data/corpus/manifests/sources.csv")
DEFAULT_RAW_ROOT = Path("data/corpus/raw")
USABLE_STATUSES = {"downloaded", "downloaded_recovered", "extracted", "validated"}
VALIDATION_ISSUE_TYPES = {
    "ambiguous_paper_type",
    "checksum_mismatch",
    "detected_mime_mismatch",
    "duplicate_file_bytes",
    "duplicate_or_missing_file_id",
    "file_size_mismatch",
    "inaccessible_local_file",
    "malformed_exam_family",
    "malformed_metadata",
    "malformed_pdf",
    "missing_local_path",
    "missing_manifest_row",
    "missing_required_metadata",
    "missing_or_invalid_source_url",
    "missing_source_record",
    "question_answer_misclassification",
    "unexpected_html_file",
    "unexpected_non_pdf",
    "year_path_mismatch",
    "zero_byte_file",
}
REQUIRED_FILE_METADATA = (
    "file_id",
    "exam_family",
    "year",
    "paper_type",
    "source_id",
    "source_url",
    "processing_status",
)
VALID_PAPER_TYPES = {
    "adjacent_question",
    "answer_key",
    "question_paper",
    "question_solution_bundle",
    "unknown",
}


def pdf_page_count(path: Path) -> tuple[int | None, str | None]:
    result = subprocess.run(
        ["pdfinfo", str(path)],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        return None, (result.stderr.strip() or "pdfinfo rejected the file")
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.partition(":")[2].strip()), None
            except ValueError:
                break
    return None, "pdfinfo did not report a page count"


def validate_rows(
    files: list[dict[str, str]],
    *,
    sources: list[dict[str, str]],
    raw_root: Path,
) -> tuple[list[dict[str, object]], list[dict[str, object]], int]:
    source_ids = {row["source_id"] for row in sources}
    seen_ids: set[str] = set()
    manifested_paths: set[Path] = set()
    checksum_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    validated: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []
    unexpected_errors = 0

    for original in files:
        row: dict[str, object] = dict(original)
        file_id = original.get("file_id", "")
        missing_fields = [field for field in REQUIRED_FILE_METADATA if not original.get(field)]
        if missing_fields:
            issues.append(
                issue_row(
                    original,
                    "missing_required_metadata",
                    "error",
                    f"Missing required fields: {', '.join(missing_fields)}.",
                )
            )
            unexpected_errors += 1
        if not file_id or file_id in seen_ids:
            issues.append(issue_row(original, "duplicate_or_missing_file_id", "error"))
            unexpected_errors += 1
        seen_ids.add(file_id)
        if original.get("exam_family") not in EXAM_FAMILIES:
            issues.append(issue_row(original, "malformed_exam_family", "error"))
            unexpected_errors += 1
        if original.get("source_id") not in source_ids:
            issues.append(issue_row(original, "missing_source_record", "error"))
            unexpected_errors += 1
        source_url = original.get("source_url", "")
        try:
            normalize_url(source_url)
        except ValueError:
            issues.append(issue_row(original, "missing_or_invalid_source_url", "error"))
            unexpected_errors += 1
        metadata_errors: list[str] = []
        if original.get("year") and not re.fullmatch(r"\d{4}", original["year"]):
            metadata_errors.append("year must contain four digits")
        if original.get("paper_type") and original["paper_type"] not in VALID_PAPER_TYPES:
            metadata_errors.append("paper_type is not a controlled value")
        if metadata_errors:
            issues.append(
                issue_row(
                    original,
                    "malformed_metadata",
                    "error",
                    "; ".join(metadata_errors),
                )
            )
            unexpected_errors += 1

        local_value = original.get("local_path", "")
        if not local_value:
            if original.get("processing_status") in USABLE_STATUSES:
                issues.append(issue_row(original, "missing_local_path", "error"))
                unexpected_errors += 1
            validated.append(row)
            continue
        local_path = Path(local_value)
        manifested_paths.add(local_path.resolve())
        if not local_path.is_file():
            issues.append(issue_row(original, "inaccessible_local_file", "error"))
            row["processing_status"] = "validation_failed"
            unexpected_errors += 1
            validated.append(row)
            continue
        size = local_path.stat().st_size
        if size == 0:
            issues.append(issue_row(original, "zero_byte_file", "error"))
            row["processing_status"] = "validation_failed"
            unexpected_errors += 1
        if original.get("file_size"):
            try:
                expected_size = int(original["file_size"])
            except ValueError:
                issues.append(
                    issue_row(
                        original,
                        "malformed_metadata",
                        "error",
                        "file_size must be an integer",
                    )
                )
                row["processing_status"] = "validation_failed"
                unexpected_errors += 1
            else:
                if size != expected_size:
                    issues.append(issue_row(original, "file_size_mismatch", "error"))
                    row["processing_status"] = "validation_failed"
                    unexpected_errors += 1
        digest = sha256_file(local_path)
        if original.get("sha256") and digest != original["sha256"]:
            issues.append(issue_row(original, "checksum_mismatch", "error"))
            row["processing_status"] = "validation_failed"
            unexpected_errors += 1
        with local_path.open("rb") as handle:
            detected_mime = detect_mime(handle.read(64 * 1024))
        if detected_mime != original.get("detected_mime_type"):
            issues.append(issue_row(original, "detected_mime_mismatch", "error"))
            row["processing_status"] = "validation_failed"
            unexpected_errors += 1
        expected_year = original.get("year", "")
        if expected_year and expected_year not in local_path.parts:
            issues.append(issue_row(original, "year_path_mismatch", "error"))
            unexpected_errors += 1

        if detected_mime == "application/pdf":
            page_count, pdf_error = pdf_page_count(local_path)
            if pdf_error:
                issues.append(issue_row(original, "malformed_pdf", "error", pdf_error))
                row["processing_status"] = "validation_failed"
                unexpected_errors += 1
            else:
                row["page_count"] = page_count or ""
        elif local_path.suffix.casefold() == ".pdf":
            issues.append(issue_row(original, "unexpected_non_pdf", "error"))
            row["processing_status"] = "validation_failed"
            unexpected_errors += 1
        elif detected_mime == "text/html" and paper_candidate(original):
            known_blocked = original.get("processing_status") == "blocked_access"
            issues.append(
                issue_row(
                    original,
                    "unexpected_html_file",
                    "warning" if known_blocked else "error",
                    "HTML response was saved for a question/answer document candidate.",
                )
            )
            if not known_blocked:
                row["processing_status"] = "validation_failed"
                unexpected_errors += 1

        paper_type = original.get("paper_type", "")
        if paper_type == "unknown":
            issues.append(
                issue_row(
                    original,
                    "ambiguous_paper_type",
                    "warning",
                    "Archive asset is not reliably classified as question or answer.",
                )
            )
        if paper_type == "question_paper" and original.get("has_answer_key") == "yes":
            issues.append(issue_row(original, "question_answer_misclassification", "error"))
            unexpected_errors += 1
        if paper_type == "answer_key" and original.get("has_question_paper") == "yes":
            issues.append(issue_row(original, "question_answer_misclassification", "error"))
            unexpected_errors += 1

        if row["processing_status"] in USABLE_STATUSES:
            row["processing_status"] = "validated"
        checksum_groups[digest].append(row)
        validated.append(row)

    for rows in checksum_groups.values():
        if len(rows) < 2:
            continue
        canonical_id = str(min(rows, key=lambda item: str(item["file_id"]))["file_id"])
        for row in rows:
            if row["file_id"] == canonical_id:
                continue
            row["duplicate_of_file_id"] = canonical_id
            issues.append(
                issue_row(
                    {key: str(value) for key, value in row.items()},
                    "duplicate_file_bytes",
                    "info",
                    f"Identical SHA-256 to {canonical_id}; provenance row retained.",
                )
            )

    for path in sorted(raw_root.rglob("*")):
        if not path.is_file() or path.name == ".gitignore" or path.suffix == ".part":
            continue
        relative_path = path.relative_to(raw_root)
        if relative_path.parts and relative_path.parts[0] == "registry":
            continue
        if path.resolve() not in manifested_paths:
            pseudo = {
                "file_id": deterministic_id("orphan", path.as_posix()),
                "exam_family": path.parts[-3] if len(path.parts) >= 3 else "",
                "year": path.parts[-2] if len(path.parts) >= 2 else "",
                "source_url": "",
            }
            issues.append(
                issue_row(
                    pseudo,
                    "missing_manifest_row",
                    "error",
                    f"Untracked raw file: {path}",
                )
            )
            unexpected_errors += 1
    return validated, issues, unexpected_errors


def paper_candidate(row: dict[str, str]) -> bool:
    return row.get("paper_type") in {
        "answer_key",
        "question_paper",
        "question_solution_bundle",
    }


def issue_row(
    row: dict[str, str], issue_type: str, severity: str, details: str = ""
) -> dict[str, object]:
    related_id = row.get("file_id", "unknown")
    return {
        "issue_id": deterministic_id("issue", related_id, issue_type),
        "exam_family": row.get("exam_family", ""),
        "year": row.get("year", ""),
        "issue_type": issue_type,
        "severity": severity,
        "related_id": related_id,
        "source_url": row.get("source_url", ""),
        "status": "open",
        "details": details or issue_type.replace("_", " "),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate raw corpus objects and manifests.")
    parser.add_argument("--files", type=Path, default=DEFAULT_FILES)
    parser.add_argument("--missing", type=Path, default=DEFAULT_MISSING)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    existing_missing = read_csv(args.missing) if args.missing.exists() else []
    retained_missing = [
        row for row in existing_missing if row["issue_type"] not in VALIDATION_ISSUE_TYPES
    ]
    rows, issues, errors = validate_rows(
        read_csv(args.files), sources=read_csv(args.sources), raw_root=args.raw_root
    )
    write_csv(args.files, FILE_FIELDS, rows)
    write_csv(
        args.missing,
        MISSING_DATA_FIELDS,
        merge_rows(retained_missing, issues, key="issue_id"),
    )
    print(f"Validated {len(rows)} file rows; {len(issues)} findings; {errors} unexpected errors")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
