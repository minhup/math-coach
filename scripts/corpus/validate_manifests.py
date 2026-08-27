from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urlsplit

from scripts.corpus.core import (
    MISSING_DATA_FIELDS,
    deterministic_id,
    merge_rows,
    read_csv,
    write_csv,
)
from scripts.corpus.prepare_question_recovery import recovery_target_years

DEFAULT_MANIFESTS = Path("data/corpus/manifests")
MANIFEST_ISSUE_TYPES = {
    "duplicate_manifest_id",
    "exam_file_classification_mismatch",
    "exam_file_identity_mismatch",
    "malformed_exam_metadata",
    "missing_candidate_file_row",
    "missing_candidate_source",
    "missing_exam_file_row",
    "missing_file_candidate",
    "missing_source_url",
}


def validate_manifests(
    *,
    sources: list[dict[str, str]],
    plan: list[dict[str, str]],
    files: list[dict[str, str]],
    exams: list[dict[str, str]],
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for rows, id_field, kind in (
        (sources, "source_id", "source"),
        (plan, "candidate_id", "candidate"),
        (files, "file_id", "file"),
        (exams, "exam_id", "exam"),
    ):
        duplicate_ids = {
            value
            for value, count in Counter(row.get(id_field, "") for row in rows).items()
            if count > 1
        }
        for duplicate_id in duplicate_ids:
            issues.append(
                issue_row(
                    duplicate_id,
                    "duplicate_manifest_id",
                    "error",
                    f"Duplicate {kind} ID in manifest: {duplicate_id or '<empty>'}.",
                )
            )

    source_by_id = {row["source_id"]: row for row in sources}
    candidate_by_id = {row["candidate_id"]: row for row in plan}
    file_by_id = {row["file_id"]: row for row in files}

    for source in sources:
        parts = urlsplit(source.get("source_url", ""))
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            issues.append(
                issue_row(
                    source.get("source_id", ""),
                    "missing_source_url",
                    "error",
                    "Source row does not contain an absolute HTTP(S) URL.",
                    source=source,
                )
            )

    for candidate in plan:
        if candidate.get("source_id") not in source_by_id:
            issues.append(
                issue_row(
                    candidate.get("candidate_id", ""),
                    "missing_candidate_source",
                    "error",
                    "Acquisition candidate references a missing source row.",
                    source=candidate,
                )
            )
        if candidate.get("selected") == "yes" and candidate.get("candidate_id") not in file_by_id:
            issues.append(
                issue_row(
                    candidate.get("candidate_id", ""),
                    "missing_candidate_file_row",
                    "error",
                    "Selected acquisition candidate has no file/provenance row.",
                    source=candidate,
                )
            )

    for file_row in files:
        if file_row.get("file_id") not in candidate_by_id:
            issues.append(
                issue_row(
                    file_row.get("file_id", ""),
                    "missing_file_candidate",
                    "error",
                    "File/provenance row has no acquisition candidate.",
                    source=file_row,
                )
            )

    for exam in exams:
        validate_exam(exam, file_by_id, issues)
    return issues


def validate_exam(
    exam: dict[str, str],
    files: dict[str, dict[str, str]],
    issues: list[dict[str, object]],
) -> None:
    exam_id = exam.get("exam_id", "")
    expected_id = deterministic_id(
        "exam",
        exam.get("exam_family", ""),
        exam.get("calendar_year", ""),
        "specialized_mathematics",
    )
    metadata_errors: list[str] = []
    if exam_id != expected_id:
        metadata_errors.append("exam_id is not deterministic for family/year")
    if exam.get("official_source_available") not in {"yes", "no", "unknown"}:
        metadata_errors.append("official_source_available is not controlled")
    if exam.get("duration_minutes") and not exam["duration_minutes"].isdigit():
        metadata_errors.append("duration_minutes is not an integer")
    try:
        if exam.get("maximum_score") and float(exam["maximum_score"]) <= 0:
            metadata_errors.append("maximum_score must be positive")
    except ValueError:
        metadata_errors.append("maximum_score is not numeric")
    if metadata_errors:
        issues.append(
            issue_row(
                exam_id,
                "malformed_exam_metadata",
                "error",
                "; ".join(metadata_errors),
                source=exam,
            )
        )

    for reference_field, paper_types in (
        ("question_file_id", {"question_paper", "question_solution_bundle"}),
        ("answer_file_id", {"answer_key"}),
    ):
        file_id = exam.get(reference_field, "")
        if not file_id:
            continue
        file_row = files.get(file_id)
        if file_row is None:
            issues.append(
                issue_row(
                    exam_id,
                    "missing_exam_file_row",
                    "error",
                    f"{reference_field} references missing file {file_id}.",
                    source=exam,
                )
            )
            continue
        if file_row.get("paper_type") not in paper_types:
            issues.append(
                issue_row(
                    exam_id,
                    "exam_file_classification_mismatch",
                    "error",
                    f"{reference_field} points to {file_row.get('paper_type')!r}.",
                    source=exam,
                )
            )
        mapped_years = recovery_target_years(file_id)
        correct_year = file_row.get("year") == exam.get("calendar_year") or (
            exam.get("calendar_year", "").isdigit() and int(exam["calendar_year"]) in mapped_years
        )
        if file_row.get("exam_family") != exam.get("exam_family") or not correct_year:
            issues.append(
                issue_row(
                    exam_id,
                    "exam_file_identity_mismatch",
                    "error",
                    f"{reference_field} points to another family/year.",
                    source=exam,
                )
            )


def issue_row(
    related_id: str,
    issue_type: str,
    severity: str,
    details: str,
    *,
    source: dict[str, str] | None = None,
) -> dict[str, object]:
    source = source or {}
    return {
        "issue_id": deterministic_id("issue", related_id or "unknown", issue_type),
        "exam_family": source.get("exam_family", ""),
        "year": source.get("year", source.get("calendar_year", "")),
        "issue_type": issue_type,
        "severity": severity,
        "related_id": related_id,
        "source_url": source.get("source_url", ""),
        "status": "open",
        "details": details,
    }


def retain_non_manifest_issues(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row["issue_type"] not in MANIFEST_ISSUE_TYPES]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate cross-manifest corpus references.")
    parser.add_argument("--manifest-root", type=Path, default=DEFAULT_MANIFESTS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.manifest_root
    issues = validate_manifests(
        sources=read_csv(root / "sources.csv"),
        plan=read_csv(root / "acquisition_plan.csv"),
        files=read_csv(root / "files.csv"),
        exams=read_csv(root / "exams.csv"),
    )
    missing_path = root / "missing_data.csv"
    existing = read_csv(missing_path) if missing_path.exists() else []
    write_csv(
        missing_path,
        MISSING_DATA_FIELDS,
        merge_rows(retain_non_manifest_issues(existing), issues, key="issue_id"),
    )
    print(f"Validated cross-manifest references; {len(issues)} errors")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
