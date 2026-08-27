from __future__ import annotations

from scripts.corpus.core import deterministic_id
from scripts.corpus.validate_manifests import validate_manifests


def test_cross_manifest_validation_accepts_consistent_references() -> None:
    source = {"source_id": "src_one", "source_url": "https://example.test/source"}
    candidate = {
        "candidate_id": "cand_one",
        "source_id": "src_one",
        "source_url": "https://example.test/question.pdf",
        "selected": "yes",
    }
    file_row = {
        "file_id": "cand_one",
        "paper_type": "question_paper",
        "exam_family": "ptnk",
        "year": "2024",
    }
    exam = {
        "exam_id": deterministic_id("exam", "ptnk", "2024", "specialized_mathematics"),
        "exam_family": "ptnk",
        "calendar_year": "2024",
        "duration_minutes": "150",
        "maximum_score": "10",
        "official_source_available": "yes",
        "question_file_id": "cand_one",
        "answer_file_id": "",
    }

    assert (
        validate_manifests(sources=[source], plan=[candidate], files=[file_row], exams=[exam]) == []
    )


def test_cross_manifest_validation_detects_duplicate_missing_and_malformed_data() -> None:
    bad_exam = {
        "exam_id": "exam_bad",
        "exam_family": "ptnk",
        "calendar_year": "2024",
        "duration_minutes": "two hours",
        "maximum_score": "unknown",
        "official_source_available": "maybe",
        "question_file_id": "cand_missing",
        "answer_file_id": "",
    }
    issues = validate_manifests(
        sources=[
            {"source_id": "src_duplicate", "source_url": ""},
            {"source_id": "src_duplicate", "source_url": "https://example.test/source"},
        ],
        plan=[
            {
                "candidate_id": "cand_one",
                "source_id": "src_missing",
                "source_url": "https://example.test/question.pdf",
                "selected": "yes",
            }
        ],
        files=[
            {
                "file_id": "cand_orphan",
                "paper_type": "answer_key",
                "exam_family": "hnue",
                "year": "2023",
            }
        ],
        exams=[bad_exam, dict(bad_exam)],
    )

    issue_types = {str(issue["issue_type"]) for issue in issues}
    assert {
        "duplicate_manifest_id",
        "malformed_exam_metadata",
        "missing_candidate_file_row",
        "missing_candidate_source",
        "missing_exam_file_row",
        "missing_file_candidate",
        "missing_source_url",
    } <= issue_types
