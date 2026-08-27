from __future__ import annotations

from pathlib import Path

import pytest

from scripts.corpus.core import (
    FILE_FIELDS,
    CorpusError,
    read_csv,
    sha256_file,
    write_csv,
)
from scripts.corpus.prepare_reconciliation_sources import (
    classify_core_files,
    prepare,
    recovery_candidates,
)
from scripts.corpus.reconcile_sets import finalize, validate_reconciliation
from scripts.corpus.reconciliation import (
    JBMO_RANGES,
    LAM_SON_SETS,
    MANUAL_IMPORT_FIELDS,
    canonical_set_id,
    component_id,
)
from scripts.corpus.registry import (
    REGISTRY_ACQUISITION_FIELDS,
    REGISTRY_FILE_FIELDS,
)


def test_reconciliation_ids_are_deterministic() -> None:
    set_id = canonical_set_id("jbmo", 2025, "contest")

    assert set_id == canonical_set_id("jbmo", "2025", "contest")
    assert component_id(set_id, "file", "question", 1, 2) == component_id(
        set_id, "file", "question", 1, 2
    )
    assert component_id(set_id, "file", "question", 1, 2) != component_id(
        set_id, "file", "solution", 1, 2
    )


def test_core_classification_is_idempotent_and_keeps_alternates_as_files() -> None:
    unknown = {field: "" for field in FILE_FIELDS}
    unknown.update(
        {
            "file_id": "alternate",
            "paper_type": "unknown",
            "notes": "Archive candidate.",
        }
    )

    first = classify_core_files([unknown])
    second = classify_core_files([{key: str(value) for key, value in first[0].items()}])

    assert first == second
    assert first[0]["paper_type"] == "question_paper"
    assert first[0]["has_question_paper"] == "yes"
    assert str(first[0]["notes"]).count("AI_SUGGESTED_LABEL") == 1


def test_recovery_candidates_have_separate_question_and_solution_roles() -> None:
    candidates = recovery_candidates()

    assert [(row["year"], row["artifact_type"]) for row in candidates] == [
        ("2025", "question"),
        ("2025", "solution"),
        ("2026", "question"),
    ]
    assert all(row["official_status"] == "official" for row in candidates)


def test_manual_import_rerun_preserves_bytes_and_manifest_rows(tmp_path: Path) -> None:
    manifests = tmp_path / "manifests"
    write_csv(
        manifests / "registry_acquisition_plan.csv",
        REGISTRY_ACQUISITION_FIELDS,
        [],
    )
    write_csv(manifests / "registry_files.csv", REGISTRY_FILE_FIELDS, [])
    write_csv(manifests / "files.csv", FILE_FIELDS, [])
    write_csv(manifests / "manual_imports.csv", MANUAL_IMPORT_FIELDS, [])
    source = tmp_path / "owner.pdf"
    source.write_bytes(b"%PDF-1.7\nowner fixture")
    raw_root = tmp_path / "raw"

    prepare(
        manifests=manifests,
        raw_root=raw_root,
        manual_source=source,
        retrieved_at="2026-08-27T00:00:00+09:00",
    )
    first = {path.name: path.read_bytes() for path in manifests.iterdir() if path.is_file()}
    prepare(
        manifests=manifests,
        raw_root=raw_root,
        manual_source=source,
        retrieved_at="2026-08-28T00:00:00+09:00",
    )

    assert {path.name: path.read_bytes() for path in manifests.iterdir() if path.is_file()} == first
    imported = read_csv(manifests / "manual_imports.csv")
    canonical = Path(imported[0]["canonical_raw_path"])
    assert canonical.read_bytes() == source.read_bytes()
    assert sha256_file(canonical) == imported[0]["sha256"]


def test_finalize_counts_alternates_as_components_not_sets() -> None:
    set_id = canonical_set_id("ptnk", 2024, "specialized_mathematics")
    sets = [{"set_id": set_id, "collection_ids": "V01", "notes": ""}]
    components = [
        {
            "component_id": f"component-{number}",
            "set_id": set_id,
            "component_role": role,
            "representation_role": "candidate",
            "official_status": official,
            "source_type": source_type,
        }
        for number, role, official, source_type in (
            (1, "question", "third_party", "community_archive"),
            (2, "question", "official", "official_school"),
            (3, "solution", "third_party", "community_archive"),
        )
    ]

    reconciled, reconciled_components = finalize(sets, components)

    assert len(reconciled) == 1
    assert reconciled[0]["question_available"] == "yes"
    assert reconciled[0]["solution_available"] == "yes"
    assert reconciled[0]["primary_question_component_id"] == "component-2"
    assert sum(row["representation_role"] == "alternate" for row in reconciled_components) == 1


def test_validate_reconciliation_rejects_partial_page_range() -> None:
    set_id = canonical_set_id("jbmo", 2025, "contest")
    sets = [{"set_id": set_id}]
    component = {
        "component_id": "component",
        "set_id": set_id,
        "file_id": "file",
        "page_start": "1",
        "page_end": "",
    }

    with pytest.raises(CorpusError, match="partial page range"):
        validate_reconciliation(
            sets,
            [component],
            {"file": {"file_id": "file", "page_count": "78"}},
        )


def test_bundle_segmentation_tables_are_complete_and_bounded() -> None:
    assert [year for year, _start, _end, _identity in JBMO_RANGES] == list(range(2012, 2026))
    assert [(start, end) for _year, start, end, _identity in JBMO_RANGES] == [
        (1, 5),
        (6, 10),
        (11, 17),
        (18, 21),
        (22, 27),
        (28, 31),
        (32, 35),
        (36, 41),
        (42, 46),
        (47, 51),
        (52, 59),
        (60, 64),
        (65, 72),
        (73, 78),
    ]
    assert [number for number, *_rest in LAM_SON_SETS] == list(range(1, 51))
    assert all(
        (solution_start is None) == (solution_end is None)
        for *_prefix, solution_start, solution_end in LAM_SON_SETS
    )
