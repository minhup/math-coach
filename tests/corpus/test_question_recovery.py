from __future__ import annotations

from pathlib import Path

from scripts.corpus.build_manifest import build_manifests
from scripts.corpus.core import ACQUISITION_FIELDS, SOURCE_FIELDS, read_csv, write_csv
from scripts.corpus.download_sources import paper_presence
from scripts.corpus.prepare_question_recovery import (
    RECOVERY_ITEMS,
    prepare,
    recovery_candidate_id,
    recovery_components,
)
from scripts.corpus.reconcile_sets import core_rows, finalize
from scripts.corpus.validate_manifests import validate_manifests


def test_prepare_question_recovery_is_deterministic_and_idempotent(tmp_path: Path) -> None:
    manifests = tmp_path / "manifests"
    write_csv(manifests / "sources.csv", SOURCE_FIELDS, [])
    write_csv(manifests / "acquisition_plan.csv", ACQUISITION_FIELDS, [])

    prepare(manifests, "2026-08-27")
    first_sources = (manifests / "sources.csv").read_bytes()
    first_plan = (manifests / "acquisition_plan.csv").read_bytes()
    prepare(manifests, "2026-08-27")

    assert (manifests / "sources.csv").read_bytes() == first_sources
    assert (manifests / "acquisition_plan.csv").read_bytes() == first_plan
    candidates = read_csv(manifests / "acquisition_plan.csv")
    assert len(candidates) == 7
    assert len({row["candidate_id"] for row in candidates}) == 7
    assert all(row["exam_variant"].startswith("question_recovery_") for row in candidates)


def test_recovery_mapping_stores_one_khtn_bundle_for_two_cycles() -> None:
    item = next(value for value in RECOVERY_ITEMS if len(value.components) == 2)
    file_id = recovery_candidate_id(item)

    assert recovery_components()[file_id] == ((2017, 20, 20), (2018, 22, 22))
    assert paper_presence("question_solution_bundle") == ("yes", "yes")


def test_mapped_bundle_builds_two_question_only_exam_sets() -> None:
    item = next(value for value in RECOVERY_ITEMS if len(value.components) == 2)
    file_id = recovery_candidate_id(item)
    candidate = {
        "candidate_id": file_id,
        "exam_family": "khtn",
        "calendar_year": "2017",
        "paper_type": "question_solution_bundle",
        "official_status": "third_party",
    }
    file_row = {
        "file_id": file_id,
        "exam_family": "khtn",
        "year": "2017",
        "academic_year": "2017-2018",
        "paper_type": "question_solution_bundle",
        "processing_status": "validated",
        "official_status": "third_party",
        "source_type": "commercial_tutoring",
        "notes": "fixture",
    }

    exams, _issues = build_manifests([candidate], [file_row], start_year=2017, end_year=2018)

    assert [row["calendar_year"] for row in exams] == [2017, 2018]
    assert {row["question_file_id"] for row in exams} == {file_id}
    assert all(row["answer_file_id"] == "" for row in exams)

    sets, components = core_rows(
        [{key: str(value) for key, value in row.items()} for row in exams],
        [file_row],
    )
    reconciled_sets, reconciled_components = finalize(sets, components)
    assert len(reconciled_sets) == 2
    assert all(row["question_available"] == "yes" for row in reconciled_sets)
    assert all(row["solution_available"] == "no" for row in reconciled_sets)
    assert {(row["page_start"], row["page_end"]) for row in reconciled_components} == {
        (20, 20),
        (22, 22),
    }
    assert {row["component_role"] for row in reconciled_components} == {"question"}


def test_manifest_validation_accepts_mapped_bundle_for_later_cycle() -> None:
    item = next(value for value in RECOVERY_ITEMS if len(value.components) == 2)
    file_id = recovery_candidate_id(item)
    source = {"source_id": "src_recovery", "source_url": item.landing_url}
    candidate = {
        "candidate_id": file_id,
        "source_id": "src_recovery",
        "source_url": item.direct_url,
        "selected": "yes",
    }
    file_row = {
        "file_id": file_id,
        "paper_type": "question_solution_bundle",
        "exam_family": "khtn",
        "year": "2017",
    }
    exams, _issues = build_manifests(
        [
            {
                **candidate,
                "exam_family": "khtn",
                "calendar_year": "2017",
                "paper_type": "question_solution_bundle",
                "official_status": "third_party",
            }
        ],
        [
            {
                **file_row,
                "processing_status": "validated",
                "official_status": "third_party",
            }
        ],
        start_year=2018,
        end_year=2018,
    )

    assert (
        validate_manifests(
            sources=[source],
            plan=[candidate],
            files=[file_row],
            exams=[{key: str(value) for key, value in exams[0].items()}],
        )
        == []
    )
