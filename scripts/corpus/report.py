from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from scripts.corpus.core import EXAM_FAMILIES, read_csv

DEFAULT_MANIFESTS = Path("data/corpus/manifests")
DEFAULT_REPORTS = Path("data/corpus/reports")
USABLE_STATUSES = {"downloaded", "downloaded_recovered", "validated", "extracted"}
DISPLAY_NAMES = {
    "ptnk": "PTNK",
    "hcmc_so": "TP.HCM So Chuyen",
    "khtn": "KHTN",
    "hnue": "HNUE / Chuyen DH Su pham",
    "hanoi_so": "Ha Noi So Chuyen",
}


def build_reports(manifest_root: Path, report_root: Path, *, report_date: str) -> None:
    sources = read_csv(manifest_root / "sources.csv")
    plan = read_csv(manifest_root / "acquisition_plan.csv")
    files = read_csv(manifest_root / "files.csv")
    exams = read_csv(manifest_root / "exams.csv")
    missing = read_csv(manifest_root / "missing_data.csv")
    report_root.mkdir(parents=True, exist_ok=True)
    write_report(
        report_root / "corpus_inventory.md",
        corpus_inventory(plan, files, exams, report_date),
    )
    write_report(report_root / "source_quality.md", source_quality(sources, report_date))
    write_report(report_root / "missing_years.md", missing_years(missing, report_date))
    write_report(
        report_root / "ingestion_report.md",
        ingestion_report(plan, files, exams, missing, report_date),
    )


def corpus_inventory(
    plan: list[dict[str, str]],
    files: list[dict[str, str]],
    exams: list[dict[str, str]],
    report_date: str,
) -> str:
    plan_by_cycle = group_rows(plan, "calendar_year")
    file_by_cycle = group_rows(files, "year")
    file_by_id = {row["file_id"]: row for row in files}
    exam_by_cycle = {(row["exam_family"], row["calendar_year"]): row for row in exams}
    lines = [
        "# Corpus inventory",
        "",
        f"Generated: **{report_date}**. Scope: calendar-year entrance cycles 2017-2026.",
        "",
        (
            "Question/answer availability below requires a reliable classification; "
            "unlabelled archive images do not count."
        ),
        "",
    ]
    for family in EXAM_FAMILIES:
        lines.extend(
            [
                f"## {DISPLAY_NAMES[family]}",
                "",
                (
                    "| Year | Files | Question | Official question | Answer | Official answer | "
                    "Formats | Source quality | Processing difficulty |"
                ),
                "|---:|---:|---|---|---|---|---|---|---|",
            ]
        )
        available_years: list[str] = []
        for year in range(2017, 2027):
            stored_cycle_files = [
                row
                for row in file_by_cycle.get((family, str(year)), [])
                if row["processing_status"] in USABLE_STATUSES
            ]
            exam = exam_by_cycle.get((family, str(year)))
            referenced_files = [
                file_by_id[file_id]
                for file_id in (
                    exam.get("question_file_id", "") if exam else "",
                    exam.get("answer_file_id", "") if exam else "",
                )
                if file_id in file_by_id
                and file_by_id[file_id]["processing_status"] in USABLE_STATUSES
            ]
            cycle_files = list(
                {row["file_id"]: row for row in stored_cycle_files + referenced_files}.values()
            )
            cycle_plan = plan_by_cycle.get((family, str(year)), [])
            questions = [
                row
                for row in cycle_files
                if row["paper_type"] in {"question_paper", "question_solution_bundle"}
            ]
            answers = [row for row in cycle_files if row["paper_type"] == "answer_key"]
            official_questions = [row for row in questions if row["official_status"] == "official"]
            official_answers = [row for row in answers if row["official_status"] == "official"]
            formats = sorted({format_label(row["detected_mime_type"]) for row in cycle_files})
            if cycle_files:
                available_years.append(str(year))
            quality = quality_label(cycle_files, cycle_plan)
            difficulty = processing_difficulty(cycle_files)
            lines.append(
                f"| {year} | {len(cycle_files)} | {yes_no(bool(questions))} | "
                f"{yes_no(bool(official_questions))} | {yes_no(bool(answers))} | "
                f"{yes_no(bool(official_answers))} | {', '.join(formats) or '-'} | "
                f"{quality} | {difficulty} |"
            )
        family_files = [
            row
            for row in files
            if row["exam_family"] == family and row["processing_status"] in USABLE_STATUSES
        ]
        unknown = sum(row["paper_type"] == "unknown" for row in family_files)
        exam_count = sum(row["exam_family"] == family for row in exams)
        lines.extend(
            [
                "",
                (
                    f"Available cycles: {', '.join(available_years) or 'none'}. "
                    f"{len(family_files)} usable files across {exam_count} exam records; "
                    f"{unknown} files require question/answer identity review."
                ),
                "",
            ]
        )
    lines.extend(
        [
            "## Cross-cycle format observations",
            "",
            (
                "- Reviewed PTNK question papers use 120 minutes in 2022-2023 and 150 minutes "
                "in 2024-2026; each reviewed paper totals 10 points."
            ),
            (
                "- TP.HCM specialized admission used record-based selection in 2021, so no "
                "specialized paper is expected for that cycle."
            ),
            (
                "- KHTN 2021 used multiple COVID-affected cohorts/rounds; archive assets remain "
                "unmapped to a round and are not treated as directly comparable."
            ),
            "- No other curriculum or format change is asserted without expert paper review.",
            "",
        ]
    )
    return "\n".join(lines)


def source_quality(sources: list[dict[str, str]], report_date: str) -> str:
    tiers = (
        "authoritative",
        "strong_archive",
        "secondary",
        "commercial_reference_only",
        "uncertain",
    )
    explanations = {
        "authoritative": "Issuing school, university, education authority, or government source.",
        "strong_archive": (
            "Useful historical discovery archive; artifact identity still needs first-party "
            "cross-checking."
        ),
        "secondary": "Reporting/context source; not authoritative for file identity.",
        "commercial_reference_only": (
            "Tutoring, teacher, or commercial reference; never promoted automatically."
        ),
        "uncertain": "Ownership or source role could not be established.",
    }
    lines = [
        "# Source quality",
        "",
        (
            f"Generated: **{report_date}**. Rights remain `unknown` unless an explicit licence "
            "is recorded."
        ),
        "",
    ]
    for tier in tiers:
        rows = [row for row in sources if row["quality_tier"] == tier]
        if not rows:
            continue
        lines.extend([f"## {tier.replace('_', ' ').title()}", "", explanations[tier], ""])
        lines.extend(
            [
                "| Source | Organization | Type | Families | Role | URL |",
                "|---|---|---|---|---|---|",
            ]
        )
        for row in sorted(rows, key=lambda item: (item["source_name"], item["source_url"])):
            lines.append(
                f"| {escape(row['source_name'])} | {escape(row['source_organization'])} | "
                f"{row['source_type']} | {row['exam_families'] or '-'} | "
                f"{row['acquisition_role']} | {markdown_link(row['source_url'])} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Use boundary",
            "",
            (
                "Public availability establishes discoverability, not permission. The current "
                "corpus is research-only; redistribution and production use remain unapproved."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def missing_years(missing: list[dict[str, str]], report_date: str) -> str:
    cycle_types = {
        "missing_cycle_assets",
        "no_exam_admission_by_records",
        "all_downloads_failed",
        "question_not_confirmed",
        "answer_not_confirmed",
        "official_question_not_acquired",
        "official_question_not_located",
        "official_answer_not_acquired",
        "official_answer_not_located",
        "round_designation_ambiguous",
    }
    ambiguous_count = sum(row["issue_type"] == "ambiguous_paper_type" for row in missing)
    acquisition_failure_count = sum(
        row["issue_type"] in {"download_failure", "invalid_html_response"} for row in missing
    )
    lines = [
        "# Missing and ambiguous examination data",
        "",
        (
            f"Generated: **{report_date}**. `Not located` is not evidence that an artifact "
            "never existed."
        ),
        "",
        "| Family | Year | Issue | Severity | Details |",
        "|---|---:|---|---|---|",
    ]
    rows = [row for row in missing if row["issue_type"] in cycle_types]
    for row in sorted(
        rows, key=lambda item: (item["exam_family"], item["year"], item["issue_type"])
    ):
        lines.append(
            f"| {row['exam_family']} | {row['year'] or '-'} | {row['issue_type']} | "
            f"{row['severity']} | {escape(row['details'])} |"
        )
    lines.extend(
        [
            "",
            "## Cross-cutting ambiguity",
            "",
            (
                f"- {ambiguous_count} acquired archive assets need manual question/answer "
                "classification."
            ),
            f"- {acquisition_failure_count} acquisition failures remain open.",
            (
                "- Community scans may combine question pages, answer pages, or commentary; "
                "filename and image order are not treated as proof."
            ),
            (
                "- Curriculum/reform comparisons require expert review after paper identity "
                "is confirmed."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def ingestion_report(
    plan: list[dict[str, str]],
    files: list[dict[str, str]],
    exams: list[dict[str, str]],
    missing: list[dict[str, str]],
    report_date: str,
) -> str:
    usable = [row for row in files if row["processing_status"] in USABLE_STATUSES]
    hashes = [row["sha256"] for row in usable if row["sha256"]]
    unique_hashes = set(hashes)
    pdfs = [row for row in usable if row["detected_mime_type"] == "application/pdf"]
    images = [row for row in usable if row["detected_mime_type"].startswith("image/")]
    official = [row for row in usable if row["official_status"] == "official"]
    exams_with_answers = [row for row in exams if row["answer_file_id"]]
    failures = [row for row in files if row["processing_status"] not in USABLE_STATUSES]
    native_text_count = sum(row["text_extractable"] == "true" for row in pdfs)
    useful_text_count = sum(row["text_extraction_quality"] == "research_useful" for row in pdfs)
    garbled_text_count = sum(
        row["text_extraction_quality"] == "garbled_or_low_quality" for row in pdfs
    )
    scanned_pdf_count = sum(row["text_extractable"] == "false" for row in pdfs)
    open_findings = sum(row["status"] == "open" for row in missing)
    local_bytes = sum(int(row["file_size"] or 0) for row in files)
    lines = [
        "# Ingestion report",
        "",
        f"Generated: **{report_date}**.",
        "",
        "## Counts",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| Selected acquisition candidates | {sum(row['selected'] == 'yes' for row in plan)} |",
        f"| Manifest file/provenance records | {len(files)} |",
        f"| Usable downloaded files | {len(usable)} |",
        f"| Unique SHA-256 objects | {len(unique_hashes)} |",
        f"| Duplicate provenance records | {len(hashes) - len(unique_hashes)} |",
        f"| Failed or invalid downloads | {len(failures)} |",
        f"| Official-source usable files | {len(official)} |",
        f"| Official-source percentage | {percentage(len(official), len(usable))} |",
        f"| Exam records | {len(exams)} |",
        f"| Exam records with classified answers | {len(exams_with_answers)} |",
        f"| PDFs | {len(pdfs)} |",
        f"| PDFs with native text | {native_text_count} |",
        f"| Research-useful native-text PDFs | {useful_text_count} |",
        f"| Garbled/low-quality native-text PDFs | {garbled_text_count} |",
        f"| Scanned/non-extractable PDFs | {scanned_pdf_count} |",
        f"| Images | {len(images)} |",
        f"| Open missing/ambiguity findings | {open_findings} |",
        "",
        "## Storage",
        "",
        (
            f"The local raw cache contains {local_bytes:,} bytes. Raw, normalized, and extracted "
            "artifacts are ignored by Git; the repository commits manifests and reproducible "
            "tooling only."
        ),
        "",
        "## Failed downloads",
        "",
    ]
    if failures:
        lines.extend(["| File ID | Family | Year | Status | Source |", "|---|---|---:|---|---|"])
        for row in failures:
            lines.append(
                f"| {row['file_id']} | {row['exam_family']} | {row['year']} | "
                f"{row['processing_status']} | {markdown_link(row['source_url'])} |"
            )
    else:
        lines.append("None.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "Archive image counts are not paper counts: a single paper may span several "
                "images, and some images may be answers or commentary. Only confirmed "
                "classifications populate exam question/answer IDs."
            ),
            (
                "Some immutable raw compilations contain later worked-solution pages. During "
                "the question-only recovery pass, only reviewed question page ranges are mapped; "
                "embedded solutions do not populate answer IDs or solution counts."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def group_rows(
    rows: list[dict[str, str]], year_field: str
) -> dict[tuple[str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["exam_family"], row[year_field])].append(row)
    return grouped


def quality_label(files: list[dict[str, str]], plan: list[dict[str, str]]) -> str:
    rows = files or plan
    if any(row["official_status"] == "official" for row in rows):
        return "authoritative"
    source_types = {row.get("source_type", "") for row in rows}
    if any(
        marker in source_type
        for source_type in source_types
        for marker in ("archive", "community", "github")
    ):
        return "strong archive"
    if any(marker in source_types for marker in ("public_mirror", "news_reporting")):
        return "secondary"
    if any("commercial" in source_type for source_type in source_types):
        return "commercial/reference-only"
    if rows:
        return "uncertain"
    return "not located"


def processing_difficulty(files: list[dict[str, str]]) -> str:
    if not files:
        return "unavailable"
    if any(row["detected_mime_type"].startswith("image/") for row in files):
        return "high (image review/OCR)"
    if any(row["text_extractable"] == "false" for row in files):
        return "medium (scanned PDF)"
    return "low (native PDF text)"


def format_label(mime: str) -> str:
    return {
        "application/pdf": "PDF",
        "image/jpeg": "JPEG",
        "image/png": "PNG",
    }.get(mime, mime or "unknown")


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def percentage(numerator: int, denominator: int) -> str:
    return f"{(100 * numerator / denominator):.1f}%" if denominator else "0.0%"


def escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def markdown_link(url: str) -> str:
    return f"[source]({url})"


def write_report(path: Path, content: str) -> None:
    temporary = path.with_suffix(".md.tmp")
    temporary.write_text(content.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build deterministic corpus reports.")
    parser.add_argument("--manifest-root", type=Path, default=DEFAULT_MANIFESTS)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORTS)
    parser.add_argument("--report-date", default="2026-08-26")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build_reports(args.manifest_root, args.report_root, report_date=args.report_date)
    print(f"Wrote corpus reports to {args.report_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
