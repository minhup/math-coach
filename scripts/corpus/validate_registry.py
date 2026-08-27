from __future__ import annotations

import argparse
import re
import subprocess
from collections import defaultdict
from pathlib import Path

from scripts.corpus.core import (
    deterministic_id,
    merge_rows,
    normalize_url,
    read_csv,
    sha256_file,
    write_csv,
)
from scripts.corpus.download_sources import detect_mime
from scripts.corpus.registry import (
    REGISTRY_FILE_FIELDS,
    REGISTRY_MISSING_FIELDS,
    USABLE_REGISTRY_STATUSES,
)

DEFAULT_FILES = Path("data/corpus/manifests/registry_files.csv")
DEFAULT_MISSING = Path("data/corpus/manifests/registry_missing_data.csv")
DEFAULT_RAW_ROOT = Path("data/corpus/raw/registry")
VALIDATION_ISSUE_TYPES = {
    "checksum_mismatch",
    "duplicate_file_bytes",
    "duplicate_or_missing_file_id",
    "file_size_mismatch",
    "inaccessible_local_file",
    "malformed_metadata",
    "malformed_pdf",
    "missing_local_path",
    "missing_manifest_row",
    "missing_required_metadata",
    "mime_mismatch",
    "question_answer_misclassification",
    "unexpected_html_file",
    "unexpected_non_pdf",
    "year_path_mismatch",
    "zero_byte_file",
}
REQUIRED_FIELDS = (
    "file_id",
    "collection_id",
    "logical_set_id",
    "artifact_type",
    "source_url",
    "processing_status",
)
VALID_ARTIFACT_TYPES = {
    "bundle",
    "question",
    "shortlist",
    "solution",
    "unknown",
    "web_page",
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
        return None, result.stderr.strip() or "pdfinfo rejected the file"
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.partition(":")[2].strip()), None
            except ValueError:
                break
    return None, "pdfinfo did not report a page count"


def issue_row(
    row: dict[str, str], issue_type: str, severity: str, details: str = ""
) -> dict[str, object]:
    related_id = row.get("file_id", "unknown")
    return {
        "issue_id": deterministic_id("rissue", related_id, issue_type),
        "collection_id": row.get("collection_id", ""),
        "logical_set_id": row.get("logical_set_id", ""),
        "year": row.get("year", ""),
        "issue_type": issue_type,
        "severity": severity,
        "related_id": related_id,
        "source_url": row.get("source_url", ""),
        "status": "open",
        "details": details or issue_type.replace("_", " "),
    }


def _metadata_issues(row: dict[str, str]) -> list[str]:
    details: list[str] = []
    if row.get("year") and not re.fullmatch(r"(?:19|20)\d{2}", row["year"]):
        details.append("year must be blank or YYYY")
    if row.get("artifact_type") not in VALID_ARTIFACT_TYPES:
        details.append("artifact_type is not a controlled value")
    try:
        normalize_url(row.get("source_url", ""))
    except ValueError:
        details.append("source_url is missing or invalid")
    return details


def validate_rows(
    files: list[dict[str, str]], *, raw_root: Path
) -> tuple[list[dict[str, object]], list[dict[str, object]], int]:
    seen_ids: set[str] = set()
    manifested_paths: set[Path] = set()
    checksums: dict[str, list[dict[str, object]]] = defaultdict(list)
    rows: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []
    errors = 0

    for original in files:
        row: dict[str, object] = dict(original)
        file_id = original.get("file_id", "")
        missing = [field for field in REQUIRED_FIELDS if not original.get(field)]
        if missing:
            issues.append(
                issue_row(
                    original,
                    "missing_required_metadata",
                    "error",
                    f"Missing: {', '.join(missing)}",
                )
            )
            errors += 1
        if not file_id or file_id in seen_ids:
            issues.append(issue_row(original, "duplicate_or_missing_file_id", "error"))
            errors += 1
        seen_ids.add(file_id)
        malformed = _metadata_issues(original)
        if malformed:
            issues.append(issue_row(original, "malformed_metadata", "error", "; ".join(malformed)))
            errors += 1

        local_value = original.get("local_path", "")
        if not local_value:
            if original.get("processing_status") in USABLE_REGISTRY_STATUSES:
                issues.append(issue_row(original, "missing_local_path", "error"))
                errors += 1
            rows.append(row)
            continue
        path = Path(local_value)
        manifested_paths.add(path.resolve())
        if not path.is_file():
            issues.append(issue_row(original, "inaccessible_local_file", "error"))
            row["processing_status"] = "validation_failed"
            errors += 1
            rows.append(row)
            continue
        size = path.stat().st_size
        if size == 0:
            issues.append(issue_row(original, "zero_byte_file", "error"))
            row["processing_status"] = "validation_failed"
            errors += 1
        try:
            expected_size = int(original.get("file_size", ""))
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
            errors += 1
        else:
            if size != expected_size:
                issues.append(issue_row(original, "file_size_mismatch", "error"))
                row["processing_status"] = "validation_failed"
                errors += 1

        digest = sha256_file(path)
        if digest != original.get("sha256"):
            issues.append(issue_row(original, "checksum_mismatch", "error"))
            row["processing_status"] = "validation_failed"
            errors += 1
        with path.open("rb") as handle:
            detected = detect_mime(handle.read(64 * 1024))
        if detected != original.get("detected_mime_type"):
            issues.append(
                issue_row(
                    original,
                    "mime_mismatch",
                    "error",
                    f"Manifest {original.get('detected_mime_type')}; bytes {detected}.",
                )
            )
            row["processing_status"] = "validation_failed"
            errors += 1
        if detected == "application/pdf":
            pages, pdf_error = pdf_page_count(path)
            if pdf_error:
                issues.append(issue_row(original, "malformed_pdf", "error", pdf_error))
                row["processing_status"] = "validation_failed"
                errors += 1
            else:
                row["page_count"] = pages or ""
        elif path.suffix.casefold() == ".pdf":
            issue_type = "unexpected_html_file" if detected == "text/html" else "unexpected_non_pdf"
            issues.append(issue_row(original, issue_type, "error"))
            row["processing_status"] = "validation_failed"
            errors += 1

        if (
            original.get("year")
            and not original.get("byte_duplicate_of_file_id")
            and original["year"] not in path.parts
        ):
            issues.append(issue_row(original, "year_path_mismatch", "error"))
            errors += 1
        filename = original.get("original_filename", "").casefold()
        if original.get("artifact_type") == "question" and any(
            marker in filename for marker in ("solution", "answer", "dapan", "dap-an")
        ):
            issues.append(
                issue_row(
                    original,
                    "question_answer_misclassification",
                    "warning",
                    "Question classification conflicts with answer-like filename.",
                )
            )
        if row["processing_status"] in USABLE_REGISTRY_STATUSES:
            row["processing_status"] = "validated"
        checksums[digest].append(row)
        rows.append(row)

    for checksum_rows in checksums.values():
        if len(checksum_rows) < 2:
            continue
        canonical = min(checksum_rows, key=lambda item: str(item["file_id"]))
        for row in checksum_rows:
            if row["file_id"] == canonical["file_id"]:
                continue
            row["byte_duplicate_of_file_id"] = canonical["file_id"]
            issues.append(
                issue_row(
                    {key: str(value) for key, value in row.items()},
                    "duplicate_file_bytes",
                    "info",
                    f"Identical SHA-256 to {canonical['file_id']}; provenance retained.",
                )
            )

    if raw_root.exists():
        for path in sorted(raw_root.rglob("*")):
            if not path.is_file() or path.name == ".gitignore" or path.suffix == ".part":
                continue
            if path.resolve() in manifested_paths:
                continue
            pseudo = {
                "file_id": deterministic_id("orphan", path.as_posix()),
                "collection_id": path.parts[-3] if len(path.parts) >= 3 else "",
            }
            issues.append(
                issue_row(
                    pseudo,
                    "missing_manifest_row",
                    "error",
                    f"Untracked raw file: {path}",
                )
            )
            errors += 1
    return rows, issues, errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate expanded registry raw objects.")
    parser.add_argument("--files", type=Path, default=DEFAULT_FILES)
    parser.add_argument("--missing", type=Path, default=DEFAULT_MISSING)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    existing_missing = read_csv(args.missing) if args.missing.exists() else []
    retained = [row for row in existing_missing if row["issue_type"] not in VALIDATION_ISSUE_TYPES]
    rows, issues, errors = validate_rows(read_csv(args.files), raw_root=args.raw_root)
    write_csv(args.files, REGISTRY_FILE_FIELDS, rows)
    write_csv(
        args.missing,
        REGISTRY_MISSING_FIELDS,
        merge_rows(retained, issues, key="issue_id"),
    )
    print(f"Validated {len(rows)} registry rows; {len(issues)} findings; {errors} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
