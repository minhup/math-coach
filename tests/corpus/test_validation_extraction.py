from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.corpus import validate_raw
from scripts.corpus.core import FILE_FIELDS, sha256_file
from scripts.corpus.extract_content import extract_rows, native_text_quality

PNG_BYTES = b"\x89PNG\r\n\x1a\nfixture"


def file_row(path: Path, file_id: str, *, detected_mime: str = "image/png") -> dict[str, str]:
    row = {field: "" for field in FILE_FIELDS}
    row.update(
        {
            "file_id": file_id,
            "exam_family": "ptnk",
            "year": "2024",
            "academic_year": "2024-2025",
            "exam_variant": "fixture",
            "subject": "mathematics",
            "paper_type": "question_paper",
            "source_id": "src_fixture",
            "source_url": f"https://example.test/{file_id}",
            "source_domain": "example.test",
            "source_name": "fixture",
            "source_type": "official_school",
            "official_status": "official",
            "retrieved_at": "2026-08-26T00:00:00+00:00",
            "http_status": "200",
            "final_url": f"https://example.test/{file_id}",
            "original_filename": path.name,
            "local_path": path.as_posix(),
            "mime_type": detected_mime,
            "detected_mime_type": detected_mime,
            "file_size": str(path.stat().st_size),
            "sha256": sha256_file(path),
            "language": "vi",
            "has_question_paper": "yes",
            "has_answer_key": "unknown",
            "rights_status": "unknown",
            "processing_status": "downloaded",
            "text_extractable": "unknown",
            "text_extraction_quality": "unassessed",
            "scan_quality": "unknown",
            "extraction_method": "none",
        }
    )
    return row


def source_rows() -> list[dict[str, str]]:
    return [{"source_id": "src_fixture"}]


def test_validation_detects_duplicate_bytes_and_preserves_provenance(
    tmp_path: Path,
) -> None:
    first = tmp_path / "raw" / "ptnk" / "2024" / "first.png"
    second = tmp_path / "raw" / "ptnk" / "2024" / "second.png"
    first.parent.mkdir(parents=True)
    first.write_bytes(PNG_BYTES)
    second.write_bytes(PNG_BYTES)

    rows, issues, errors = validate_raw.validate_rows(
        [file_row(first, "cand_first"), file_row(second, "cand_second")],
        sources=source_rows(),
        raw_root=tmp_path / "raw",
    )

    assert errors == 0
    assert [issue["issue_type"] for issue in issues] == ["duplicate_file_bytes"]
    by_id = {str(row["file_id"]): row for row in rows}
    assert by_id["cand_first"]["duplicate_of_file_id"] == ""
    assert by_id["cand_second"]["duplicate_of_file_id"] == "cand_first"
    assert len(rows) == 2


def test_validation_accepts_combined_question_solution_bundle(tmp_path: Path) -> None:
    path = tmp_path / "raw" / "ptnk" / "2024" / "bundle.png"
    path.parent.mkdir(parents=True)
    path.write_bytes(PNG_BYTES)
    row = file_row(path, "cand_bundle")
    row.update(
        {
            "paper_type": "question_solution_bundle",
            "has_question_paper": "yes",
            "has_answer_key": "yes",
        }
    )

    rows, issues, errors = validate_raw.validate_rows(
        [row], sources=source_rows(), raw_root=tmp_path / "raw"
    )

    assert errors == 0
    assert issues == []
    assert rows[0]["processing_status"] == "validated"


def test_validation_handles_malformed_files_mime_and_metadata(tmp_path: Path, monkeypatch) -> None:
    raw_root = tmp_path / "raw"
    bad_pdf = raw_root / "ptnk" / "2024" / "bad.pdf"
    bad_pdf.parent.mkdir(parents=True)
    bad_pdf.write_bytes(b"%PDF-1.4\nbroken")
    malformed = file_row(bad_pdf, "cand_bad", detected_mime="application/pdf")
    malformed["file_size"] = "not-an-integer"
    malformed["year"] = "20x4"
    malformed["paper_type"] = "solution"
    monkeypatch.setattr(validate_raw, "pdf_page_count", lambda _path: (None, "invalid PDF"))

    rows, issues, errors = validate_raw.validate_rows(
        [malformed], sources=source_rows(), raw_root=raw_root
    )

    issue_types = {str(issue["issue_type"]) for issue in issues}
    assert {"malformed_metadata", "malformed_pdf", "year_path_mismatch"} <= issue_types
    assert errors >= 3
    assert rows[0]["processing_status"] == "validation_failed"

    missing = file_row(bad_pdf, "cand_missing", detected_mime="application/pdf")
    missing.update(
        {
            "exam_family": "",
            "year": "",
            "paper_type": "",
            "source_id": "",
            "source_url": "",
            "local_path": "",
            "processing_status": "",
        }
    )
    _rows, missing_issues, missing_errors = validate_raw.validate_rows(
        [missing], sources=source_rows(), raw_root=tmp_path / "empty-raw"
    )
    missing_types = {str(issue["issue_type"]) for issue in missing_issues}
    assert "missing_required_metadata" in missing_types
    assert "missing_or_invalid_source_url" in missing_types
    assert "missing_source_record" in missing_types
    assert missing_errors >= 3


def test_validation_detects_mime_verification_failure(tmp_path: Path) -> None:
    path = tmp_path / "raw" / "ptnk" / "2024" / "wrong.pdf"
    path.parent.mkdir(parents=True)
    path.write_bytes(PNG_BYTES)
    row = file_row(path, "cand_wrong", detected_mime="application/pdf")

    _rows, issues, errors = validate_raw.validate_rows(
        [row], sources=source_rows(), raw_root=tmp_path / "raw"
    )

    assert {issue["issue_type"] for issue in issues} >= {
        "detected_mime_mismatch",
        "unexpected_non_pdf",
    }
    assert errors >= 2


def test_validation_rejects_html_saved_for_a_document_candidate(
    tmp_path: Path,
) -> None:
    path = tmp_path / "raw" / "ptnk" / "2024" / "drive.html"
    path.parent.mkdir(parents=True)
    path.write_text("<html><title>Can't download file</title></html>", encoding="utf-8")
    row = file_row(path, "cand_html", detected_mime="text/html")

    rows, issues, errors = validate_raw.validate_rows(
        [row], sources=source_rows(), raw_root=tmp_path / "raw"
    )

    assert {issue["issue_type"] for issue in issues} == {"unexpected_html_file"}
    assert errors == 1
    assert rows[0]["processing_status"] == "validation_failed"


def test_validation_preserves_a_known_blocked_html_source(tmp_path: Path) -> None:
    path = tmp_path / "raw" / "ptnk" / "2024" / "blocked.html"
    path.parent.mkdir(parents=True)
    path.write_text("<html><title>Request access</title></html>", encoding="utf-8")
    row = file_row(path, "cand_blocked", detected_mime="text/html")
    row["processing_status"] = "blocked_access"

    rows, issues, errors = validate_raw.validate_rows(
        [row], sources=source_rows(), raw_root=tmp_path / "raw"
    )

    assert issues[0]["issue_type"] == "unexpected_html_file"
    assert issues[0]["severity"] == "warning"
    assert errors == 0
    assert rows[0]["processing_status"] == "blocked_access"


def test_legacy_validation_leaves_expanded_registry_objects_to_its_validator(
    tmp_path: Path,
) -> None:
    registry_object = tmp_path / "raw" / "registry" / "J01" / "2024" / "paper.pdf"
    registry_object.parent.mkdir(parents=True)
    registry_object.write_bytes(b"%PDF-1.7\nregistry fixture")

    rows, issues, errors = validate_raw.validate_rows([], sources=[], raw_root=tmp_path / "raw")

    assert rows == []
    assert issues == []
    assert errors == 0


def test_fixture_pdf_native_extraction_is_deterministic(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "raw" / "ptnk" / "2024" / "fixture.pdf"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"%PDF-1.4\nfixture")
    row = file_row(path, "cand_pdf", detected_mime="application/pdf")
    row["processing_status"] = "validated"
    row["page_count"] = "1"

    def fake_pdftotext(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        Path(command[-1]).write_text(
            "ĐỀ THI TUYỂN SINH\nMôn thi: Toán chuyên\nBài 1. Chứng minh mệnh đề.",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("scripts.corpus.extract_content.subprocess.run", fake_pdftotext)
    extracted_root = tmp_path / "extracted"
    normalized_root = tmp_path / "normalized"
    first, first_errors = extract_rows(
        [row], extracted_root=extracted_root, normalized_root=normalized_root
    )
    first_sidecar = Path(str(first[0]["extracted_text_path"])).with_suffix(".txt")
    assert first_sidecar.is_file()
    normalized_path = normalized_root / "ptnk" / "2024" / "cand_pdf.json"
    first_normalized = normalized_path.read_bytes()

    second, second_errors = extract_rows(
        [row], extracted_root=extracted_root, normalized_root=normalized_root
    )

    assert first_errors == second_errors == 0
    assert first == second
    assert normalized_path.read_bytes() == first_normalized
    assert first[0]["text_extractable"] == "true"
    assert first[0]["text_extraction_quality"] == "research_useful"
    sidecar = json.loads(first_normalized)
    assert sidecar["machine_generated"] is True
    assert sidecar["mathematically_verified"] is False


def test_fixture_pdf_extraction_failure_and_quality_detection(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "raw" / "ptnk" / "2024" / "fixture.pdf"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"%PDF-1.4\nfixture")
    row = file_row(path, "cand_pdf", detected_mime="application/pdf")

    monkeypatch.setattr(
        "scripts.corpus.extract_content.subprocess.run",
        lambda command, **_kwargs: subprocess.CompletedProcess(command, 1, "", "broken"),
    )
    rows, errors = extract_rows(
        [row],
        extracted_root=tmp_path / "extracted",
        normalized_root=tmp_path / "normalized",
    )

    assert errors == 1
    assert rows[0]["text_extractable"] == "false"
    assert rows[0]["text_extraction_quality"] == "extraction_failed"
    assert native_text_quality("DAI Hoc Quoc Gia M6n thi Toin chuy6n " * 3) == (
        "garbled_or_low_quality"
    )
