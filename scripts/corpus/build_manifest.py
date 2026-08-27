from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from scripts.corpus.core import (
    EXAM_FAMILIES,
    EXAM_FIELDS,
    MISSING_DATA_FIELDS,
    deterministic_id,
    merge_rows,
    read_csv,
    write_csv,
)
from scripts.corpus.download_sources import QUESTION_PAPER_TYPES
from scripts.corpus.prepare_question_recovery import (
    recovery_components,
    recovery_target_years,
)
from scripts.corpus.reconciliation import CORE_PRIMARY_QUESTIONS

DEFAULT_PLAN = Path("data/corpus/manifests/acquisition_plan.csv")
DEFAULT_FILES = Path("data/corpus/manifests/files.csv")
DEFAULT_EXAMS = Path("data/corpus/manifests/exams.csv")
DEFAULT_MISSING = Path("data/corpus/manifests/missing_data.csv")
USABLE_STATUSES = {"downloaded", "downloaded_recovered", "validated", "extracted"}
FAMILY_METADATA = {
    "ptnk": ("Truong Pho thong Nang khieu, DHQG-HCM", "Ho Chi Minh City", "unknown"),
    "hcmc_so": ("So Giao duc va Dao tao TP.HCM", "Ho Chi Minh City", "unknown"),
    "khtn": ("THPT Chuyen Khoa hoc Tu nhien, DHQGHN", "Hanoi", "unknown"),
    "hnue": ("THPT Chuyen Dai hoc Su pham Ha Noi", "Hanoi", "unknown"),
    "hanoi_so": ("So Giao duc va Dao tao Ha Noi", "Hanoi", "unknown"),
}
CYCLE_ISSUE_TYPES = {
    "all_downloads_failed",
    "answer_not_confirmed",
    "missing_cycle_assets",
    "no_exam_admission_by_records",
    "official_answer_not_acquired",
    "official_answer_not_located",
    "official_question_not_acquired",
    "official_question_not_located",
    "question_not_confirmed",
    "round_designation_ambiguous",
}
DOCUMENT_METADATA = {
    ("ptnk", 2017): ("150", "10"),
    ("ptnk", 2018): ("150", "10"),
    ("ptnk", 2019): ("150", "10"),
    ("ptnk", 2020): ("150", "10"),
    ("ptnk", 2021): ("150", "10"),
    ("ptnk", 2022): ("120", "10"),
    ("ptnk", 2023): ("120", "10"),
    ("ptnk", 2024): ("150", "10"),
    ("ptnk", 2025): ("150", "10"),
    ("ptnk", 2026): ("150", "10"),
    **{("hcmc_so", year): ("150", "10") for year in range(2017, 2027)},
    **{("hanoi_so", year): ("150", "10") for year in range(2017, 2027)},
    ("khtn", 2017): ("150", ""),
    ("khtn", 2018): ("150", ""),
    **{("khtn", year): ("150", "10") for year in range(2019, 2026)},
    ("khtn", 2026): ("150", "10"),
    **{("hnue", year): ("150", "10") for year in range(2017, 2021)},
    **{("hnue", year): ("120", "10") for year in range(2021, 2025)},
}
DOCUMENT_ROUNDS = {
    ("khtn", 2017): "2",
    ("khtn", 2018): "2",
    ("khtn", 2026): "2",
    ("hnue", 2026): "2",
}


def build_manifests(
    plan: list[dict[str, str]],
    files: list[dict[str, str]],
    *,
    start_year: int,
    end_year: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    recovery_ranges = recovery_components()
    candidates_by_cycle: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    files_by_cycle: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in plan:
        years = recovery_target_years(row.get("candidate_id", "")) or {int(row["calendar_year"])}
        for year in years:
            candidates_by_cycle[(row["exam_family"], year)].append(row)
    for row in files:
        years = recovery_target_years(row.get("file_id", "")) or {int(row["year"])}
        for year in years:
            files_by_cycle[(row["exam_family"], year)].append(row)

    exams: list[dict[str, object]] = []
    missing: list[dict[str, object]] = []
    for family in EXAM_FAMILIES:
        authority, city, round_name = FAMILY_METADATA[family]
        for year in range(start_year, end_year + 1):
            key = (family, year)
            candidates = candidates_by_cycle.get(key, [])
            usable = [
                row
                for row in files_by_cycle.get(key, [])
                if row["processing_status"] in USABLE_STATUSES
            ]
            if family == "hcmc_so" and year == 2021:
                missing.append(
                    cycle_issue(
                        family,
                        year,
                        "no_exam_admission_by_records",
                        "info",
                        (
                            "Official-network evidence indicates admission by records; "
                            "no specialized paper expected."
                        ),
                    )
                )
                continue
            if family == "khtn" and year == 2021:
                missing.append(
                    cycle_issue(
                        family,
                        year,
                        "round_designation_ambiguous",
                        "warning",
                        (
                            "Official evidence describes multiple COVID-affected cohorts/rounds; "
                            "archive assets are not mapped to a round."
                        ),
                    )
                )
            if not candidates:
                missing.append(
                    cycle_issue(
                        family,
                        year,
                        "missing_cycle_assets",
                        "warning",
                        "No question or answer candidate located in the bounded inventory.",
                    )
                )
                continue
            if not usable:
                missing.append(
                    cycle_issue(
                        family,
                        year,
                        "all_downloads_failed",
                        "error",
                        "Candidates exist, but no usable local artifact was acquired.",
                    )
                )

            questions = [row for row in usable if row["paper_type"] in QUESTION_PAPER_TYPES]
            answers = [row for row in usable if row["paper_type"] == "answer_key"]
            official_questions = [row for row in questions if row["official_status"] == "official"]
            official_answers = [row for row in answers if row["official_status"] == "official"]
            official_question_candidates = [
                row
                for row in candidates
                if row["paper_type"] in QUESTION_PAPER_TYPES
                and row["official_status"] == "official"
            ]
            official_answer_candidates = [
                row
                for row in candidates
                if row["paper_type"] == "answer_key" and row["official_status"] == "official"
            ]
            unknown_count = sum(row["paper_type"] == "unknown" for row in usable)
            notes: list[str] = []
            if unknown_count:
                notes.append(f"{unknown_count} archive assets have ambiguous paper type.")
            if len(questions) > 1:
                notes.append(f"{len(questions)} question candidates require identity/page review.")
            if len(answers) > 1:
                notes.append(f"{len(answers)} answer candidates require identity review.")

            question_id = select_file_id(
                questions, preferred=CORE_PRIMARY_QUESTIONS.get((family, str(year)))
            )
            answer_id = select_file_id(answers)
            duration_minutes, maximum_score = DOCUMENT_METADATA.get((family, year), ("", ""))
            if duration_minutes and maximum_score:
                notes.append(
                    "Duration and maximum score were transcribed from the reviewed question paper."
                )
            elif duration_minutes:
                notes.append("Duration was transcribed from the reviewed question paper.")
            if question_id in recovery_ranges:
                _target_year, page_start, page_end = next(
                    component for component in recovery_ranges[question_id] if component[0] == year
                )
                location = (
                    f"pages {page_start}-{page_end}" if page_start is not None else "the image"
                )
                notes.append(
                    f"Question identity is mapped to {location} of a reviewed third-party mirror."
                )
            exams.append(
                {
                    "exam_id": deterministic_id(
                        "exam", family, str(year), "specialized_mathematics"
                    ),
                    "exam_family": family,
                    "school_or_authority": authority,
                    "city": city,
                    "academic_year": f"{year}-{year + 1}",
                    "calendar_year": year,
                    "paper_type": "entrance_exam",
                    "subject": "mathematics",
                    "duration_minutes": duration_minutes,
                    "maximum_score": maximum_score,
                    "specialized_or_common": "specialized",
                    "round": DOCUMENT_ROUNDS.get((family, year), round_name),
                    "official_source_available": (
                        "yes"
                        if official_question_candidates or official_answer_candidates
                        else "no"
                    ),
                    "question_file_id": question_id,
                    "answer_file_id": answer_id,
                    "notes": " ".join(notes),
                }
            )

            if not questions:
                missing.append(
                    cycle_issue(
                        family,
                        year,
                        "question_not_confirmed",
                        "warning",
                        "No acquired asset is reliably classified as the question paper.",
                    )
                )
            if not answers:
                missing.append(
                    cycle_issue(
                        family,
                        year,
                        "answer_not_confirmed",
                        "warning",
                        "No acquired asset is reliably classified as an answer key.",
                    )
                )
            if not official_questions and official_question_candidates:
                missing.append(
                    cycle_issue(
                        family,
                        year,
                        "official_question_not_acquired",
                        "warning",
                        (
                            "A first-party actual question was located, but no usable local "
                            "artifact was acquired."
                        ),
                    )
                )
            elif not official_questions:
                missing.append(
                    cycle_issue(
                        family,
                        year,
                        "official_question_not_located",
                        "warning",
                        "No first-party actual specialized-Mathematics question was located.",
                    )
                )
            if not official_answers and official_answer_candidates:
                missing.append(
                    cycle_issue(
                        family,
                        year,
                        "official_answer_not_acquired",
                        "warning",
                        (
                            "A first-party actual answer was located, but no usable local artifact "
                            "was acquired."
                        ),
                    )
                )
            elif not official_answers:
                missing.append(
                    cycle_issue(
                        family,
                        year,
                        "official_answer_not_located",
                        "warning",
                        "No first-party actual specialized-Mathematics answer was located.",
                    )
                )
    return exams, missing


def select_file_id(rows: list[dict[str, str]], *, preferred: str | None = None) -> str:
    if not rows:
        return ""
    if preferred and any(row["file_id"] == preferred for row in rows):
        return preferred
    official = [row for row in rows if row["official_status"] == "official"]
    choices = official or rows
    return choices[0]["file_id"] if len(choices) == 1 else ""


def cycle_issue(
    family: str,
    year: int,
    issue_type: str,
    severity: str,
    details: str,
) -> dict[str, object]:
    related_id = deterministic_id("cycle", family, str(year))
    return {
        "issue_id": deterministic_id("issue", related_id, issue_type),
        "exam_family": family,
        "year": year,
        "issue_type": issue_type,
        "severity": severity,
        "related_id": related_id,
        "source_url": "",
        "status": "open",
        "details": details,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build normalized exam and missing-data manifests."
    )
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--files", type=Path, default=DEFAULT_FILES)
    parser.add_argument("--exams", type=Path, default=DEFAULT_EXAMS)
    parser.add_argument("--missing", type=Path, default=DEFAULT_MISSING)
    parser.add_argument("--start-year", type=int, default=2017)
    parser.add_argument("--end-year", type=int, default=2026)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    exams, issues = build_manifests(
        read_csv(args.plan),
        read_csv(args.files),
        start_year=args.start_year,
        end_year=args.end_year,
    )
    existing_missing = read_csv(args.missing) if args.missing.exists() else []
    retained_missing = [
        row for row in existing_missing if row["issue_type"] not in CYCLE_ISSUE_TYPES
    ]
    write_csv(args.exams, EXAM_FIELDS, exams)
    write_csv(
        args.missing,
        MISSING_DATA_FIELDS,
        merge_rows(retained_missing, issues, key="issue_id"),
    )
    print(f"Wrote {len(exams)} exam records and merged {len(issues)} cycle findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
