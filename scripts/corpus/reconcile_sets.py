from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from scripts.corpus.core import CorpusError, read_csv, write_csv
from scripts.corpus.prepare_question_recovery import recovery_components
from scripts.corpus.reconciliation import (
    CORE_ADJACENT_QUESTIONS,
    CORE_PRIMARY_QUESTIONS,
    JBMO_BUNDLE_FILE_ID,
    JBMO_RANGES,
    LAM_SON_SETS,
    PROBLEM_SET_FIELDS,
    SET_COMPONENT_FIELDS,
    canonical_set_id,
    component_id,
    merge_set_rows,
)
from scripts.corpus.registry import LEGACY_COLLECTION_FAMILIES, USABLE_REGISTRY_STATUSES

DEFAULT_MANIFESTS = Path("data/corpus/manifests")
USABLE_CORE_STATUSES = {"downloaded", "downloaded_recovered", "validated", "extracted"}
CORE_AUTHORITY = {
    "ptnk": ("PTNK — ĐHQG-HCM", "Vietnam"),
    "hcmc_so": ("Sở GDĐT TP.HCM", "Vietnam"),
    "hanoi_so": ("Sở GDĐT Hà Nội", "Vietnam"),
    "khtn": ("THPT Chuyên KHTN — ĐHQGHN", "Vietnam"),
    "hnue": ("THPT Chuyên ĐH Sư phạm Hà Nội", "Vietnam"),
}


def blank_set(**values: object) -> dict[str, object]:
    row: dict[str, object] = {field: "" for field in PROBLEM_SET_FIELDS}
    row.update(
        {
            "question_available": "no",
            "solution_available": "no",
            "official_question_available": "no",
            "official_solution_available": "no",
            "solution_source": "none",
            "expert_review_status": "not_reviewed",
        }
    )
    row.update(values)
    return row


def make_component(
    *,
    set_id: str,
    file_manifest: str,
    file_row: dict[str, str],
    role: str,
    representation: str,
    provenance: str,
    verified: str,
    page_start: int | str | None = None,
    page_end: int | str | None = None,
    sequence: int | str = 1,
    notes: str = "",
) -> dict[str, object]:
    return {
        "component_id": component_id(set_id, file_row["file_id"], role, page_start, page_end),
        "set_id": set_id,
        "file_manifest": file_manifest,
        "file_id": file_row["file_id"],
        "component_role": role,
        "representation_role": representation,
        "page_start": page_start or "",
        "page_end": page_end or "",
        "sequence": sequence,
        "source_type": file_row.get("source_type", "unknown"),
        "official_status": file_row.get("official_status", "unknown"),
        "classification_provenance": provenance,
        "verified": verified,
        "semantic_duplicate_of_component_id": "",
        "notes": notes,
    }


def core_rows(
    exams: list[dict[str, str]], files: list[dict[str, str]]
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    sets: dict[str, dict[str, object]] = {}
    components: list[dict[str, object]] = []
    target_ids: dict[tuple[str, str], str] = {}
    recovery_ranges = recovery_components()
    for exam in exams:
        family = exam["exam_family"]
        year = exam["calendar_year"]
        set_id = canonical_set_id(family, year, "specialized_mathematics")
        target_ids[(family, year)] = set_id
        authority, country = CORE_AUTHORITY[family]
        sets[set_id] = blank_set(
            set_id=set_id,
            collection_ids=next(
                key for key, value in LEGACY_COLLECTION_FAMILIES.items() if value == family
            ),
            series_id=family,
            exam_family=family,
            school_or_authority=authority,
            country_region=country,
            calendar_year=year,
            academic_year=exam["academic_year"],
            set_variant="specialized_mathematics",
            set_kind="actual_exam",
            subject="mathematics",
            specialized_or_common="specialized",
            round=exam["round"],
            identity_status="archive_identity_supported",
            corpus_eligibility="eligible_actual_exam",
            notes="Core ten-cycle acquisition scope; alternate scans do not create more sets.",
        )

    for file_row in files:
        family = file_row["exam_family"]
        year = file_row["year"]
        if file_row["file_id"] in recovery_ranges:
            usable = file_row["processing_status"] in USABLE_CORE_STATUSES
            for target_year, page_start, page_end in recovery_ranges[file_row["file_id"]]:
                target_id = target_ids.get((family, str(target_year)))
                if target_id is None:
                    continue
                components.append(
                    make_component(
                        set_id=target_id,
                        file_manifest="files.csv",
                        file_row=file_row,
                        role="question" if usable else "blocked_question",
                        representation="primary" if usable else "blocked_source",
                        provenance="SOURCE_FACT",
                        verified="true",
                        page_start=page_start,
                        page_end=page_end,
                        notes=(
                            "Reviewed page/image reproduces the complete question paper. "
                            "Any solution pages elsewhere in the raw source are deliberately "
                            "not mapped in this question-only pass."
                        ),
                    )
                )
            continue
        target_id = target_ids.get((family, year))
        paper_type = file_row["paper_type"]
        if paper_type == "adjacent_question":
            variant = CORE_ADJACENT_QUESTIONS[file_row["file_id"]]
            target_id = canonical_set_id(family, year, variant)
            if target_id not in sets:
                authority, country = CORE_AUTHORITY[family]
                sets[target_id] = blank_set(
                    set_id=target_id,
                    collection_ids=next(
                        key for key, value in LEGACY_COLLECTION_FAMILIES.items() if value == family
                    ),
                    series_id=family,
                    exam_family=family,
                    school_or_authority=authority,
                    country_region=country,
                    calendar_year=year,
                    academic_year=file_row["academic_year"],
                    set_variant=variant,
                    set_kind="actual_exam",
                    subject="mathematics",
                    specialized_or_common="specialized_informatics",
                    round="unknown",
                    identity_status="visible_header_supported",
                    corpus_eligibility="adjacent_non_target_exam",
                    notes="Retained because the archive mixed this paper into the target family.",
                )
        if target_id is None or paper_type not in {
            "adjacent_question",
            "answer_key",
            "question_paper",
        }:
            continue
        usable = file_row["processing_status"] in USABLE_CORE_STATUSES
        if not usable:
            role = "blocked_solution" if paper_type == "answer_key" else "blocked_question"
            representation = "blocked_source"
        elif paper_type == "answer_key":
            role = "solution"
            representation = "candidate_solution"
        else:
            role = "question"
            representation = (
                "primary"
                if CORE_PRIMARY_QUESTIONS.get((family, year)) == file_row["file_id"]
                and paper_type != "adjacent_question"
                else "alternate"
            )
        ai_classified = "AI_SUGGESTED_LABEL" in file_row.get("notes", "")
        components.append(
            make_component(
                set_id=target_id,
                file_manifest="files.csv",
                file_row=file_row,
                role=role,
                representation=representation,
                provenance="AI_SUGGESTED_LABEL" if ai_classified else "SOURCE_FACT",
                verified="false" if ai_classified else "true",
                notes=(
                    "Visual classification is not expert verification."
                    if ai_classified
                    else "Classification was already supported by source metadata."
                ),
            )
        )
    return list(sets.values()), components


def registry_set_identity(
    row: dict[str, str], collection: dict[str, str]
) -> tuple[str, str, str, str, str]:
    collection_id = row["collection_id"]
    year = row["year"]
    kind = row["artifact_type"]
    if collection_id in {"J01", "J04", "J06"} and kind != "shortlist":
        return "jbmo", "contest", "actual_exam", "eligible_actual_exam", "mathematics"
    if collection_id == "V06" and year == "2017":
        return (
            "lam_son",
            "compilation_15",
            "actual_exam",
            "eligible_actual_exam",
            "mathematics",
        )
    if kind == "shortlist":
        return (
            collection_id.casefold(),
            "shortlist",
            "shortlist",
            "reference_only_partial",
            "mathematics",
        )
    return (
        collection_id.casefold(),
        "contest",
        "actual_exam",
        "eligible_actual_exam",
        "mathematics",
    )


def registry_rows(
    files: list[dict[str, str]], collections: list[dict[str, str]]
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    metadata = {row["collection_id"]: row for row in collections}
    sets: dict[str, dict[str, object]] = {}
    components: list[dict[str, object]] = []
    for file_row in files:
        if not file_row["year"] or file_row["artifact_type"] not in {
            "question",
            "shortlist",
            "solution",
        }:
            continue
        collection = metadata[file_row["collection_id"]]
        series, variant, set_kind, eligibility, subject = registry_set_identity(
            file_row, collection
        )
        set_id = canonical_set_id(series, file_row["year"], variant)
        sets.setdefault(
            set_id,
            blank_set(
                set_id=set_id,
                collection_ids=file_row["collection_id"],
                series_id=series,
                exam_family="",
                school_or_authority=collection["source_name"],
                country_region=collection["country_region"],
                calendar_year=file_row["year"],
                academic_year="",
                set_variant=variant,
                set_kind=set_kind,
                subject=subject,
                specialized_or_common="unknown",
                round="unknown",
                identity_status="registry_source_supported",
                corpus_eligibility=eligibility,
                notes="Annual identity comes from the expanded source registry.",
            ),
        )
        current = sets[set_id]
        current_collections = set(str(current["collection_ids"]).split(";"))
        current_collections.add(file_row["collection_id"])
        current["collection_ids"] = ";".join(sorted(current_collections))
        role = file_row["artifact_type"]
        usable = file_row["processing_status"] in USABLE_REGISTRY_STATUSES
        if not usable:
            role = f"blocked_{role}"
        components.append(
            make_component(
                set_id=set_id,
                file_manifest="registry_files.csv",
                file_row=file_row,
                role=role,
                representation="candidate" if usable else "blocked_source",
                provenance="SOURCE_FACT",
                verified="true",
                notes="Artifact role comes from the registry acquisition evidence.",
            )
        )
    return list(sets.values()), components


def jbmo_bundle_rows(
    registry_files: dict[str, dict[str, str]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    file_row = registry_files.get(JBMO_BUNDLE_FILE_ID)
    if file_row is None:
        return [], []
    sets: list[dict[str, object]] = []
    components: list[dict[str, object]] = []
    for year, start, end, identity in JBMO_RANGES:
        set_id = canonical_set_id("jbmo", year, "contest")
        sets.append(
            blank_set(
                set_id=set_id,
                collection_ids="J05;J06",
                series_id="jbmo",
                exam_family="",
                school_or_authority="Junior Balkan Mathematical Olympiad",
                country_region="Balkans",
                calendar_year=year,
                academic_year="",
                set_variant="contest",
                set_kind="actual_exam",
                subject="mathematics",
                specialized_or_common="junior_olympiad",
                round="contest",
                identity_status=identity,
                corpus_eligibility="eligible_actual_exam",
                notes="Annual page range reconciled from the 2012-2025 English bundle.",
            )
        )
        inferred = identity == "inferred_bundle_sequence"
        components.append(
            make_component(
                set_id=set_id,
                file_manifest="registry_files.csv",
                file_row=file_row,
                role="combined_question_solution",
                representation="supporting_bundle",
                provenance="AI_SUGGESTED_LABEL" if inferred else "SOURCE_FACT",
                verified="false" if inferred else "true",
                page_start=start,
                page_end=end,
                notes=(
                    "Year inferred from contiguous bundle sequence; expert cross-check pending."
                    if inferred
                    else "Visible annual heading/content supports this page range."
                ),
            )
        )
    return sets, components


def lam_son_rows(
    registry_files: dict[str, dict[str, str]], manual_imports: list[dict[str, str]]
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if not manual_imports:
        return [], []
    import_row = next((row for row in manual_imports if row["collection_id"] == "V06"), None)
    if import_row is None:
        return [], []
    file_row = registry_files[import_row["imported_file_id"]]
    sets: list[dict[str, object]] = []
    components: list[dict[str, object]] = []
    for number, year, track, kind, q_start, q_end, s_start, s_end in LAM_SON_SETS:
        variant = f"compilation_{number:02d}"
        set_id = canonical_set_id("lam_son", year, variant)
        eligibility = (
            "eligible_actual_exam"
            if kind == "actual_exam" and track == "specialized_mathematics"
            else "adjacent_non_target_exam"
            if kind == "actual_exam"
            else "reference_only_mock_or_survey"
        )
        sets.append(
            blank_set(
                set_id=set_id,
                collection_ids="V06",
                series_id="lam_son",
                exam_family="",
                school_or_authority="THPT Chuyên Lam Sơn — Thanh Hóa",
                country_region="Vietnam",
                calendar_year=year,
                academic_year=f"{year}-{year + 1}",
                set_variant=variant,
                set_kind=kind,
                subject="mathematics",
                specialized_or_common=track,
                round="unknown",
                identity_status="source_claimed_compilation",
                corpus_eligibility=eligibility,
                notes=(
                    f"Compilation set {number}; identity is publisher-claimed and not "
                    "expert-verified."
                ),
            )
        )
        components.append(
            make_component(
                set_id=set_id,
                file_manifest="registry_files.csv",
                file_row=file_row,
                role="question",
                representation="primary",
                provenance="SOURCE_FACT",
                verified="true",
                page_start=q_start,
                page_end=q_end,
                notes=f"Visible question heading: compilation set {number}.",
            )
        )
        if s_start is not None:
            components.append(
                make_component(
                    set_id=set_id,
                    file_manifest="registry_files.csv",
                    file_row=file_row,
                    role="solution",
                    representation="candidate_solution",
                    provenance="SOURCE_FACT",
                    verified="true",
                    page_start=s_start,
                    page_end=s_end,
                    sequence=2,
                    notes=("Publisher compilation solution/marking content; not expert-verified."),
                )
            )
    return sets, components


def _priority(component: dict[str, object], role: str) -> tuple[int, str]:
    official = component["official_status"] == "official"
    exact_role = component["component_role"] == role
    explicit_primary = component["representation_role"] == "primary"
    return (
        (0 if official else 4) + (0 if exact_role else 2) + (0 if explicit_primary else 1),
        str(component["component_id"]),
    )


def finalize(
    sets: list[dict[str, object]], components: list[dict[str, object]]
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    sets = merge_set_rows(sets)
    by_set: dict[str, list[dict[str, object]]] = defaultdict(list)
    for component in components:
        by_set[str(component["set_id"])].append(component)

    for row in sets:
        current = by_set[str(row["set_id"])]
        questions = [
            value
            for value in current
            if value["component_role"] in {"question", "combined_question_solution"}
        ]
        solutions = [
            value
            for value in current
            if value["component_role"] in {"solution", "combined_question_solution"}
        ]
        if questions:
            primary = min(questions, key=lambda value: _priority(value, "question"))
            row["primary_question_component_id"] = primary["component_id"]
            primary["representation_role"] = "primary"
            for value in questions:
                if value is primary or value["component_role"] == "combined_question_solution":
                    continue
                value["representation_role"] = "alternate"
                value["semantic_duplicate_of_component_id"] = primary["component_id"]
        if solutions:
            primary = min(solutions, key=lambda value: _priority(value, "solution"))
            row["primary_solution_component_id"] = primary["component_id"]
            if primary["component_role"] == "solution":
                primary["representation_role"] = "primary"
        row["question_available"] = "yes" if questions else "no"
        row["solution_available"] = "yes" if solutions else "no"
        row["official_question_available"] = (
            "yes" if any(value["official_status"] == "official" for value in questions) else "no"
        )
        row["official_solution_available"] = (
            "yes" if any(value["official_status"] == "official" for value in solutions) else "no"
        )
        if solutions:
            source_types = {str(value["source_type"]) for value in solutions}
            if row["official_solution_available"] == "yes":
                row["solution_source"] = "official"
            elif any("commercial" in value for value in source_types):
                row["solution_source"] = "commercial"
            elif any(
                marker in value
                for value in source_types
                for marker in ("community", "archive", "mirror")
            ):
                row["solution_source"] = "community"
            else:
                row["solution_source"] = "unknown"
        row["completeness_status"] = (
            "question_and_solution"
            if questions and solutions
            else "question_only"
            if questions
            else "solution_only"
            if solutions
            else "no_usable_artifact"
        )
    return sets, sorted(components, key=lambda row: str(row["component_id"]))


def validate_reconciliation(
    sets: list[dict[str, object]],
    components: list[dict[str, object]],
    all_files: dict[str, dict[str, str]],
) -> None:
    set_ids = [str(row["set_id"]) for row in sets]
    component_ids = [str(row["component_id"]) for row in components]
    if len(set_ids) != len(set(set_ids)):
        raise CorpusError("duplicate problem-set ID")
    if len(component_ids) != len(set(component_ids)):
        raise CorpusError("duplicate set-component ID")
    known_sets = set(set_ids)
    for component in components:
        if component["set_id"] not in known_sets:
            raise CorpusError(f"component references missing set: {component['component_id']}")
        file_row = all_files.get(str(component["file_id"]))
        if file_row is None:
            raise CorpusError(f"component references missing file: {component['file_id']}")
        start = str(component["page_start"])
        end = str(component["page_end"])
        if bool(start) != bool(end):
            raise CorpusError(f"partial page range: {component['component_id']}")
        if start:
            if int(start) < 1 or int(end) < int(start):
                raise CorpusError(f"invalid page range: {component['component_id']}")
            page_count = file_row.get("page_count", "")
            if page_count and int(end) > int(page_count):
                raise CorpusError(f"page range exceeds file: {component['component_id']}")


def build(manifests: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    core_files = read_csv(manifests / "files.csv")
    registry_files = read_csv(manifests / "registry_files.csv")
    registry_by_id = {row["file_id"]: row for row in registry_files}
    collections = read_csv(manifests / "registry_collections.csv")
    manual_path = manifests / "manual_imports.csv"
    manual_imports = read_csv(manual_path) if manual_path.exists() else []

    set_groups: list[dict[str, object]] = []
    component_groups: list[dict[str, object]] = []
    for sets, components in (
        core_rows(read_csv(manifests / "exams.csv"), core_files),
        registry_rows(registry_files, collections),
        jbmo_bundle_rows(registry_by_id),
        lam_son_rows(registry_by_id, manual_imports),
    ):
        set_groups.extend(sets)
        component_groups.extend(components)
    sets, components = finalize(set_groups, component_groups)
    all_files = {row["file_id"]: row for row in core_files + registry_files}
    validate_reconciliation(sets, components, all_files)
    return sets, components


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconcile raw artifacts into distinct examination/problem sets."
    )
    parser.add_argument("--manifests", type=Path, default=DEFAULT_MANIFESTS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sets, components = build(args.manifests)
    write_csv(args.manifests / "problem_sets.csv", PROBLEM_SET_FIELDS, sets)
    write_csv(args.manifests / "set_components.csv", SET_COMPONENT_FIELDS, components)
    eligible = sum(row["corpus_eligibility"] == "eligible_actual_exam" for row in sets)
    with_solutions = sum(
        row["corpus_eligibility"] == "eligible_actual_exam" and row["solution_available"] == "yes"
        for row in sets
    )
    print(
        f"Wrote {len(sets)} distinct sets and {len(components)} components; "
        f"{eligible} eligible actual sets, {with_solutions} with solutions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
