from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from scripts.corpus.core import read_csv
from scripts.corpus.registry import LEGACY_COLLECTION_FAMILIES, USABLE_REGISTRY_STATUSES

DEFAULT_MANIFESTS = Path("data/corpus/manifests")
DEFAULT_REPORT = Path("data/corpus/reports/corpus_acquisition_status.md")
BEGIN_MARKER = "<!-- BEGIN GENERATED ACQUISITION SNAPSHOT -->"
END_MARKER = "<!-- END GENERATED ACQUISITION SNAPSHOT -->"
USABLE_LEGACY_STATUSES = {
    "downloaded",
    "downloaded_recovered",
    "validated",
    "extracted",
}


def optional_csv(path: Path) -> list[dict[str, str]]:
    return read_csv(path) if path.exists() else []


def escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def format_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{value:.2f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    raise AssertionError("unreachable")


def format_years(values: set[str]) -> str:
    years = sorted(int(value) for value in values if value.isdigit())
    if not years:
        return "—"
    groups: list[tuple[int, int]] = []
    start = previous = years[0]
    for year in years[1:]:
        if year == previous + 1:
            previous = year
            continue
        groups.append((start, previous))
        start = previous = year
    groups.append((start, previous))
    return ", ".join(str(start) if start == end else f"{start}-{end}" for start, end in groups)


def collection_status(
    collection: dict[str, str],
    *,
    candidates: list[dict[str, str]],
    files: list[dict[str, str]],
    issues: list[dict[str, str]],
) -> str:
    collection_id = collection["collection_id"]
    if collection_id in LEGACY_COLLECTION_FAMILIES:
        return "PARTIAL_LOCAL"
    usable = [row for row in files if row["processing_status"] in USABLE_REGISTRY_STATUSES]
    failures = [row for row in files if row["processing_status"] not in USABLE_REGISTRY_STATUSES]
    blocking_issues = [
        row
        for row in issues
        if row["issue_type"] in {"discovery_failure", "download_failure", "no_downloadable_assets"}
    ]
    if usable and all(row["artifact_type"] == "web_page" for row in usable):
        return "REFERENCE_SNAPSHOT_ONLY"
    if usable and blocking_issues:
        return "PARTIAL_BATCH"
    if usable and len(usable) == len(candidates) and not failures:
        return "BATCH_DOWNLOADED"
    if usable:
        return "PARTIAL_BATCH"
    if failures or any(
        row["issue_type"] in {"discovery_failure", "download_failure"} for row in issues
    ):
        return "BLOCKED_OR_FAILED"
    if candidates:
        return "DISCOVERED"
    if collection["selected_initial_wave"] == "no":
        return "QUEUED_LATER"
    if collection["agent_action"] in {
        "INDEX",
        "INDEX_AND_EXTRACT_METADATA",
        "MASTER_DISCOVERY",
    }:
        return "INDEX_PENDING"
    return "MANUAL_DISCOVERY_NEEDED"


def generated_snapshot(manifest_root: Path) -> str:
    collections = optional_csv(manifest_root / "registry_collections.csv")
    plan = optional_csv(manifest_root / "registry_acquisition_plan.csv")
    registry_files = optional_csv(manifest_root / "registry_files.csv")
    registry_missing = optional_csv(manifest_root / "registry_missing_data.csv")
    legacy_files = optional_csv(manifest_root / "files.csv")
    exams = optional_csv(manifest_root / "exams.csv")
    legacy_missing = optional_csv(manifest_root / "missing_data.csv")
    problem_sets = optional_csv(manifest_root / "problem_sets.csv")

    usable_legacy = [
        row for row in legacy_files if row["processing_status"] in USABLE_LEGACY_STATUSES
    ]
    usable_registry = [
        row for row in registry_files if row["processing_status"] in USABLE_REGISTRY_STATUSES
    ]
    all_rows = legacy_files + registry_files
    usable = usable_legacy + usable_registry
    unique_hashes = {row["sha256"] for row in usable if row.get("sha256")}
    unique_paths: dict[str, int] = {}
    for row in all_rows:
        path = row.get("local_path", "")
        if path:
            unique_paths.setdefault(path, int(row.get("file_size") or 0))
    registry_sets = {
        row["logical_set_id"]
        for row in usable_registry
        if row["collection_id"] not in LEGACY_COLLECTION_FAMILIES
        and row["year"]
        and row["artifact_type"] in {"question", "shortlist", "solution"}
    }
    legacy_sets = {row["exam_id"] for row in exams}
    eligible_sets = [
        row for row in problem_sets if row.get("corpus_eligibility") == "eligible_actual_exam"
    ]
    reconciled_core_sets = [
        row for row in eligible_sets if row.get("series_id") in LEGACY_COLLECTION_FAMILIES.values()
    ]
    reconciled_expanded_sets = [
        row
        for row in eligible_sets
        if row.get("series_id") not in LEGACY_COLLECTION_FAMILIES.values()
    ]
    pdfs = [row for row in usable if row["detected_mime_type"] == "application/pdf"]
    images = [row for row in usable if row["detected_mime_type"].startswith("image/")]
    native_text = [row for row in usable if row.get("text_extractable") == "true"]
    legacy_failures = [
        row for row in legacy_files if row["processing_status"] not in USABLE_LEGACY_STATUSES
    ]
    registry_failures = [
        row for row in registry_files if row["processing_status"] not in USABLE_REGISTRY_STATUSES
    ]
    failures = legacy_failures + registry_failures
    official = [row for row in usable if row["official_status"] == "official"]
    initial = [row for row in collections if row["selected_initial_wave"] == "yes"]
    selected_plan = [row for row in plan if row["selected"] == "yes"]
    deferred_plan = [row for row in plan if row["selected"] != "yes"]
    registry_unique_hashes = {row["sha256"] for row in usable_registry if row["sha256"]}
    scanned_pdfs = sum(row.get("text_extractable") == "false" for row in pdfs)

    lines = [
        BEGIN_MARKER,
        "",
        "### Overall (generated from manifests)",
        "",
        (
            "Counts below are regenerated by `python3 -m scripts.corpus.report_registry`. "
            "They separate logical sets from provenance rows and physical objects."
        ),
        "",
        "| Measure | Current value |",
        "|---|---:|",
        f"| Workbook collections registered | {len(collections)} |",
        f"| Initial P0/P0X batch collections | {len(initial)} |",
        f"| Expanded candidates inventoried | {len(plan)} |",
        f"| Expanded candidates selected | {len(selected_plan)} |",
        f"| Expanded candidates deferred by scope | {len(deferred_plan)} |",
        f"| Expanded provenance rows acquired | {len(usable_registry)} |",
        f"| Expanded unique SHA-256 objects acquired | {len(registry_unique_hashes)} |",
        f"| Expanded failed or invalid file rows | {len(registry_failures)} |",
        (
            f"| Distinct eligible actual sets | "
            f"{len(eligible_sets) if problem_sets else len(legacy_sets) + len(registry_sets)} |"
        ),
        (
            f"| Existing Vietnam core sets | "
            f"{len(reconciled_core_sets) if problem_sets else len(legacy_sets)} |"
        ),
        (
            f"| Expanded eligible actual sets | "
            f"{len(reconciled_expanded_sets) if problem_sets else len(registry_sets)} |"
        ),
        (
            f"| All reconciled set records (including adjacent/reference) | "
            f"{len(problem_sets) if problem_sets else 'not generated'} |"
        ),
        f"| Raw provenance/file rows | {len(all_rows)} |",
        f"| Usable provenance/file rows | {len(usable)} |",
        f"| Unique SHA-256 objects | {len(unique_hashes)} |",
        f"| Physical raw paths | {len(unique_paths)} |",
        f"| Byte-duplicate provenance rows | {len(usable) - len(unique_hashes)} |",
        f"| Failed or invalid file rows | {len(failures)} |",
        f"| Official-source usable rows | {len(official)} |",
        f"| PDFs | {len(pdfs)} |",
        f"| Scanned/non-extractable PDFs | {scanned_pdfs} |",
        f"| Images | {len(images)} |",
        f"| Text-extractable documents | {len(native_text)} |",
        f"| Physical raw storage | {format_bytes(sum(unique_paths.values()))} |",
        "",
        (
            "A duplicate provenance row records another source for already known bytes. It is not "
            "another problem set and does not create another physical raw object."
        ),
        "",
        "### Existing Vietnam core (logical-set counts)",
        "",
        "| Registry | Family | Sets | Years | Usable artifacts | Answers linked |",
        "|---|---|---:|---|---:|---:|",
    ]
    display = {
        "ptnk": "PTNK",
        "hcmc_so": "TP.HCM Sở Chuyên",
        "hanoi_so": "Hà Nội Sở Chuyên",
        "khtn": "KHTN",
        "hnue": "HNUE / Chuyên ĐHSP",
    }
    for collection_id, family in LEGACY_COLLECTION_FAMILIES.items():
        family_exams = [row for row in exams if row["exam_family"] == family]
        family_sets = [
            row
            for row in reconciled_core_sets
            if row.get("series_id") == family and row.get("question_available") == "yes"
        ]
        family_files = [row for row in usable_legacy if row["exam_family"] == family]
        lines.append(
            f"| `{collection_id}` | {display[family]} | "
            f"{len(family_sets) if problem_sets else len(family_exams)} | "
            f"{format_years({row['calendar_year'] for row in (family_sets or family_exams)})} | "
            f"{len(family_files)} | {sum(bool(row['answer_file_id']) for row in family_exams)} |"
        )

    candidates_by_collection: dict[str, list[dict[str, str]]] = defaultdict(list)
    files_by_collection: dict[str, list[dict[str, str]]] = defaultdict(list)
    issues_by_collection: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in plan:
        candidates_by_collection[row["collection_id"]].append(row)
    for row in registry_files:
        files_by_collection[row["collection_id"]].append(row)
    for row in registry_missing:
        issues_by_collection[row["collection_id"]].append(row)
    lines.extend(
        [
            "",
            "### Expanded registry progress (all 65 collections)",
            "",
            (
                "`BATCH_DOWNLOADED` means the currently selected batch downloaded successfully; "
                "it does not claim that the collection's full historical scope is complete."
            ),
            "",
            (
                "| ID | Priority | Collection | Inventoried | Selected | Usable rows | "
                "Unique bytes | Logical sets | Years | Status |"
            ),
            "|---|---|---|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for collection in collections:
        collection_id = collection["collection_id"]
        candidates = candidates_by_collection[collection_id]
        files = files_by_collection[collection_id]
        issues = issues_by_collection[collection_id]
        collection_usable = [
            row for row in files if row["processing_status"] in USABLE_REGISTRY_STATUSES
        ]
        hashes = {row["sha256"] for row in collection_usable if row["sha256"]}
        sets = {
            row["logical_set_id"]
            for row in collection_usable
            if row["year"] and row["artifact_type"] in {"question", "shortlist", "solution"}
        }
        years = {row["year"] for row in collection_usable}
        if collection_id in LEGACY_COLLECTION_FAMILIES:
            family = LEGACY_COLLECTION_FAMILIES[collection_id]
            sets = {row["exam_id"] for row in exams if row["exam_family"] == family}
            years = {row["calendar_year"] for row in exams if row["exam_family"] == family}
            collection_usable = [row for row in usable_legacy if row["exam_family"] == family]
            hashes = {row["sha256"] for row in collection_usable if row["sha256"]}
        elif problem_sets:
            collection_sets = [
                row
                for row in eligible_sets
                if collection_id in row.get("collection_ids", "").split(";")
            ]
            sets = {row["set_id"] for row in collection_sets}
            years = {row["calendar_year"] for row in collection_sets}
        status = collection_status(collection, candidates=candidates, files=files, issues=issues)
        name = escape(collection["source_name"])
        lines.append(
            f"| `{collection_id}` | {collection['priority']} | {name} | "
            f"{len(candidates)} | {sum(row['selected'] == 'yes' for row in candidates)} | "
            f"{len(collection_usable)} | {len(hashes)} | {len(sets)} | "
            f"{format_years(years)} | `{status}` |"
        )

    missing_cycles = [
        row
        for row in legacy_missing
        if row["issue_type"]
        in {
            "missing_cycle_assets",
            "no_exam_admission_by_records",
            "official_answer_not_acquired",
            "official_question_not_acquired",
            "round_designation_ambiguous",
        }
    ]
    open_registry = [row for row in registry_missing if row["status"] == "open"]
    lines.extend(
        [
            "",
            "### Missing, failed, and ambiguous items",
            "",
            "#### Core exam-cycle gaps",
            "",
            "| Family | Year | Issue | Details |",
            "|---|---:|---|---|",
        ]
    )
    for row in sorted(
        missing_cycles,
        key=lambda value: (value["exam_family"], value["year"], value["issue_type"]),
    ):
        lines.append(
            f"| {row['exam_family']} | {row['year'] or '—'} | `{row['issue_type']}` | "
            f"{escape(row['details'])} |"
        )
    lines.extend(
        [
            "",
            "#### Expanded-registry acquisition findings",
            "",
            "| Collection | Year | Issue | Related candidate/source | Details |",
            "|---|---:|---|---|---|",
        ]
    )
    if not open_registry:
        lines.append("| — | — | — | — | No open expanded-registry findings. |")
    for row in sorted(
        open_registry,
        key=lambda value: (value["collection_id"], value["year"], value["issue_type"]),
    ):
        lines.append(
            f"| `{row['collection_id']}` | {row['year'] or '—'} | `{row['issue_type']}` | "
            f"`{row['related_id']}` | {escape(row['details'])} |"
        )
    issue_counts = Counter(row["issue_type"] for row in open_registry)
    lines.extend(
        [
            "",
            "Open expanded-registry findings by type: "
            + (
                ", ".join(f"`{key}`={value}" for key, value in sorted(issue_counts.items()))
                or "none"
            ),
            "",
            END_MARKER,
        ]
    )
    return "\n".join(lines)


def update_report(report_path: Path, snapshot: str) -> None:
    content = report_path.read_text(encoding="utf-8")
    if BEGIN_MARKER in content and END_MARKER in content:
        prefix, remainder = content.split(BEGIN_MARKER, 1)
        _old, suffix = remainder.split(END_MARKER, 1)
        content = prefix.rstrip() + "\n\n" + snapshot + suffix
    else:
        start = content.index("## Current acquisition snapshot")
        end = content.index("### Official verification anchors for the existing core")
        heading = "## Current acquisition snapshot\n\n"
        content = content[:start] + heading + snapshot + "\n\n" + content[end:]
    temporary = report_path.with_suffix(".md.tmp")
    temporary.write_text(content.rstrip() + "\n", encoding="utf-8")
    temporary.replace(report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update the global corpus acquisition ledger.")
    parser.add_argument("--manifests", type=Path, default=DEFAULT_MANIFESTS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    update_report(args.report, generated_snapshot(args.manifests))
    print(f"Updated {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
