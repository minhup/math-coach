from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from scripts.corpus.core import read_csv
from scripts.corpus.report_registry import format_years

DEFAULT_MANIFESTS = Path("data/corpus/manifests")
DEFAULT_REPORT = Path("data/corpus/reports/set_reconciliation.md")
CORE_SCOPES = {
    "ptnk": ("PTNK", set(range(2017, 2027))),
    "hcmc_so": ("TP.HCM Sở Chuyên", set(range(2017, 2027)) - {2021}),
    "hanoi_so": ("Hà Nội Sở Chuyên", set(range(2017, 2027))),
    "khtn": ("KHTN", set(range(2017, 2027))),
    "hnue": ("HNUE / Chuyên ĐHSP", set(range(2017, 2027))),
}


def years_text(rows: list[dict[str, str]]) -> str:
    return format_years({row["calendar_year"] for row in rows})


def missing_text(expected: set[int], rows: list[dict[str, str]]) -> str:
    found = {int(row["calendar_year"]) for row in rows}
    missing = expected - found
    return format_years({str(year) for year in missing}) if missing else "None"


def solution_gaps(rows: list[dict[str, str]]) -> str:
    missing = {row["calendar_year"] for row in rows if row["solution_available"] != "yes"}
    return format_years(missing) if missing else "None"


def render(manifests: Path) -> str:
    sets = read_csv(manifests / "problem_sets.csv")
    components = read_csv(manifests / "set_components.csv")
    core_files = read_csv(manifests / "files.csv")
    registry_files = read_csv(manifests / "registry_files.csv")
    eligible = [row for row in sets if row["corpus_eligibility"] == "eligible_actual_exam"]
    with_solutions = [row for row in eligible if row["solution_available"] == "yes"]
    official_questions = [row for row in eligible if row["official_question_available"] == "yes"]
    alternate_components = [row for row in components if row["representation_role"] == "alternate"]
    blocked_components = [
        row for row in components if row["representation_role"] == "blocked_source"
    ]
    files = core_files + registry_files
    usable = {
        "downloaded",
        "downloaded_recovered",
        "downloaded_reused",
        "validated",
        "extracted",
    }
    usable_files = [row for row in files if row["processing_status"] in usable]
    unique_hashes = {row["sha256"] for row in usable_files if row["sha256"]}
    core_question_rows = [
        row
        for row in eligible
        if row["series_id"] in CORE_SCOPES and row["question_available"] == "yes"
    ]
    core_missing: list[str] = []
    for series, (label, expected) in CORE_SCOPES.items():
        family_rows = [row for row in core_question_rows if row["series_id"] == series]
        missing = missing_text(expected, family_rows)
        if missing != "None":
            core_missing.append(f"{label}: {missing}")

    lines = [
        "# Distinct problem-set reconciliation",
        "",
        (
            "Generated from `problem_sets.csv` and `set_components.csv`. A set is one actual "
            "exam/contest instance; alternate scans, mirrors, page segments, and answer documents "
            "are components and never increase the set count."
        ),
        "",
        "## Reconciled totals",
        "",
        "| Measure | Count |",
        "|---|---:|",
        f"| Distinct eligible actual sets | {len(eligible)} |",
        f"| Eligible sets with a source-linked solution | {len(with_solutions)} |",
        f"| Eligible sets with an official-source question file | {len(official_questions)} |",
        f"| All set records, including adjacent/mock/reference | {len(sets)} |",
        f"| Set components | {len(components)} |",
        f"| Semantic alternate representations | {len(alternate_components)} |",
        f"| Blocked/error-page components | {len(blocked_components)} |",
        f"| Usable provenance/file rows | {len(usable_files)} |",
        f"| Unique SHA-256 objects | {len(unique_hashes)} |",
        "",
        (
            "A source-linked solution may be official, community, or commercial. It is not an "
            "expert-verified production solution unless separately reviewed."
        ),
        "",
        "## Original five-family plan",
        "",
        (
            "The initial plan covers 2017-2026. TP.HCM 2021 is excluded from expected papers "
            "because the documented admission route did not administer this specialist paper."
        ),
        "",
        (
            "| Family | Downloaded distinct sets | Years represented | With solutions | "
            "Missing actual papers from plan | Downloaded sets missing solutions |"
        ),
        "|---|---:|---|---:|---|---|",
    ]
    for series, (label, expected) in CORE_SCOPES.items():
        rows = [
            row
            for row in eligible
            if row["series_id"] == series and row["question_available"] == "yes"
        ]
        lines.append(
            f"| {label} | {len(rows)} | {years_text(rows)} | "
            f"{sum(row['solution_available'] == 'yes' for row in rows)} | "
            f"{missing_text(expected, rows)} | {solution_gaps(rows)} |"
        )
    core_rows = [row for row in eligible if row["series_id"] in CORE_SCOPES]
    core_expected = sum(len(scope) for _label, scope in CORE_SCOPES.values())
    lines.append(
        f"| **Total** | **{len(core_rows)}** | — | "
        f"**{sum(row['solution_available'] == 'yes' for row in core_rows)}** | "
        f"**{core_expected - len(core_rows)} missing** | — |"
    )

    expanded_specs: tuple[tuple[str, str, set[int] | None, str], ...] = (
        ("jbmo", "JBMO", set(range(2012, 2027)), "2012-2025 bundle + 2026 recovery"),
        (
            "lam_son",
            "Lam Sơn Chuyên Toán",
            set(range(2017, 2027)),
            "recent decade first",
        ),
        ("v07", "Vietnam Grade-9 HSG archive V07", None, "registry-discovered scope"),
        ("v08", "Vietnam Grade-9 HSG archive V08", None, "registry-discovered scope"),
        (
            "v09",
            "Vietnam historical archive V09",
            None,
            "single located historical set",
        ),
    )
    lines.extend(
        [
            "",
            "## Expanded registry sets processed in this pass",
            "",
            (
                "| Series | Distinct eligible sets | Years represented | With solutions | "
                "Bounded missing papers | Scope note |"
            ),
            "|---|---:|---|---:|---|---|",
        ]
    )
    for series, label, expanded_expected, note in expanded_specs:
        rows = [
            row
            for row in eligible
            if row["series_id"] == series and row["question_available"] == "yes"
        ]
        missing = (
            missing_text(expanded_expected, rows)
            if expanded_expected is not None
            else "Not quantifiable"
        )
        lines.append(
            f"| {label} | {len(rows)} | {years_text(rows)} | "
            f"{sum(row['solution_available'] == 'yes' for row in rows)} | {missing} | {note} |"
        )

    eligibility = Counter(row["corpus_eligibility"] for row in sets)
    source_counts = Counter(row["solution_source"] for row in with_solutions)
    lines.extend(
        [
            "",
            "## Excluded but preserved sets",
            "",
            (
                "These records are real source material but are not included in the eligible "
                "actual-set total: Chuyên Tin/common-language papers, the Lam Sơn mock and "
                "surveys, and partial JBMO shortlist artifacts."
            ),
            "",
            "| Eligibility class | Sets |",
            "|---|---:|",
        ]
    )
    for key, count in sorted(eligibility.items()):
        lines.append(f"| `{key}` | {count} |")
    lines.extend(
        [
            "",
            "## Solution provenance",
            "",
            "| Source class | Eligible sets |",
            "|---|---:|",
        ]
    )
    for key, count in sorted(source_counts.items()):
        lines.append(f"| `{key}` | {count} |")
    lines.extend(
        [
            "",
            "## Remaining acquisition and review work",
            "",
            "- Core actual-paper gaps: " + ("; ".join(core_missing) or "none") + ".",
            (
                "- PTNK 2025 answer and HNUE 2023 question/answer links currently return Google "
                "Drive permission pages; third-party question representations may exist, but the "
                "official files remain blocked provenance."
            ),
            (
                "- Solution seeking was explicitly deferred for this pass. Combined raw source "
                "files were preserved unchanged, but their solution pages were not mapped as "
                "solution components and do not increase solution counts."
            ),
            "- JBMO 2026 has an official problem paper but no official solution located.",
            (
                "- Lam Sơn recent-decade actual Chuyên Toán paper for 2023 was not located in "
                "the owner-provided compilation or current registry artifacts."
            ),
            (
                "- JBMO 2013 and 2020 bundle page-range identities are now cross-checked against "
                "first-party annual publications; mathematical solution review is still pending."
            ),
            (
                "- All visual classifications, community/commercial solutions, mathematical "
                "content, and problem transcriptions still require expert review before "
                "production use."
            ),
            "",
            "## Reproducible commands",
            "",
            "```bash",
            "python3 -m scripts.corpus.prepare_question_recovery --inventory-date <YYYY-MM-DD>",
            ("python3 -m scripts.corpus.download_sources --exam-variant-prefix question_recovery_"),
            "python3 -m scripts.corpus.prepare_reconciliation_sources --retrieved-at <ISO-8601>",
            "python3 -m scripts.corpus.download_registry_sources",
            "python3 -m scripts.corpus.validate_raw",
            "python3 -m scripts.corpus.validate_registry",
            "python3 -m scripts.corpus.extract_registry_content",
            "python3 -m scripts.corpus.build_manifest --start-year 2017 --end-year 2026",
            "python3 -m scripts.corpus.reconcile_sets",
            "python3 -m scripts.corpus.report_sets",
            "python3 -m scripts.corpus.report_registry",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report distinct reconciled corpus sets.")
    parser.add_argument("--manifests", type=Path, default=DEFAULT_MANIFESTS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    content = render(args.manifests)
    temporary = args.report.with_suffix(".md.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(args.report)
    print(f"Updated {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
