from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.corpus import validate_registry
from scripts.corpus.core import deterministic_id, sha256_file
from scripts.corpus.extract_registry_content import extract_rows
from scripts.corpus.registry import REGISTRY_FILE_FIELDS


def file_row(path: Path, file_id: str) -> dict[str, str]:
    row = {field: "" for field in REGISTRY_FILE_FIELDS}
    row.update(
        {
            "file_id": file_id,
            "collection_id": "J01",
            "logical_set_id": deterministic_id("set", "J01", "2025", "contest"),
            "year": "2025",
            "artifact_type": "question",
            "source_url": f"https://example.test/{file_id}.pdf",
            "discovery_url": "https://example.test/",
            "source_domain": "example.test",
            "url_role": "official",
            "source_type": "official_organization",
            "official_status": "official",
            "retrieved_at": "2026-08-26T00:00:00+00:00",
            "http_status": "200",
            "final_url": f"https://example.test/{file_id}.pdf",
            "original_filename": f"{file_id}.pdf",
            "local_path": path.as_posix(),
            "mime_type": "application/pdf",
            "detected_mime_type": "application/pdf",
            "file_size": str(path.stat().st_size),
            "sha256": sha256_file(path),
            "language": "en",
            "rights_status": "unknown",
            "processing_status": "downloaded",
            "text_extractable": "unknown",
            "text_extraction_quality": "unassessed",
            "scan_quality": "unknown",
            "extraction_method": "none",
        }
    )
    return row


def test_registry_validation_preserves_duplicate_provenance_and_counts_pages(
    tmp_path: Path, monkeypatch
) -> None:
    first = tmp_path / "raw" / "registry" / "J01" / "2025" / "first.pdf"
    second = tmp_path / "raw" / "registry" / "J01" / "2025" / "second.pdf"
    first.parent.mkdir(parents=True)
    first.write_bytes(b"%PDF-1.7\nfixture")
    second.write_bytes(first.read_bytes())
    monkeypatch.setattr(validate_registry, "pdf_page_count", lambda _path: (2, None))

    rows, issues, errors = validate_registry.validate_rows(
        [file_row(first, "file_a"), file_row(second, "file_b")],
        raw_root=tmp_path / "raw" / "registry",
    )

    assert errors == 0
    assert rows[0]["page_count"] == 2
    assert rows[0]["processing_status"] == "validated"
    assert rows[1]["byte_duplicate_of_file_id"] == "file_a"
    assert [issue["issue_type"] for issue in issues] == ["duplicate_file_bytes"]


def test_registry_validation_reports_missing_metadata_and_orphan(
    tmp_path: Path,
) -> None:
    raw_root = tmp_path / "raw" / "registry"
    orphan = raw_root / "J01" / "2025" / "orphan.png"
    orphan.parent.mkdir(parents=True)
    orphan.write_bytes(b"\x89PNG\r\n\x1a\nfixture")
    malformed = {field: "" for field in REGISTRY_FILE_FIELDS}

    _rows, issues, errors = validate_registry.validate_rows([malformed], raw_root=raw_root)

    assert {issue["issue_type"] for issue in issues} >= {
        "duplicate_or_missing_file_id",
        "malformed_metadata",
        "missing_manifest_row",
        "missing_required_metadata",
    }
    assert errors >= 4


def test_registry_pdf_extraction_is_deterministic(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "raw" / "registry" / "J01" / "2025" / "fixture.pdf"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"%PDF-1.7\nfixture")
    row = file_row(path, "file_pdf")
    row["processing_status"] = "validated"
    row["page_count"] = "1"

    def fake_pdftotext(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        Path(command[-1]).write_text(
            "Junior Balkan Mathematical Olympiad Problem 1. Prove that an integer exists. "
            "Solution is not included in this question paper.",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("scripts.corpus.extract_registry_content.subprocess.run", fake_pdftotext)
    extracted_root = tmp_path / "extracted"
    normalized_root = tmp_path / "normalized"
    first, first_errors = extract_rows(
        [row], extracted_root=extracted_root, normalized_root=normalized_root
    )
    before = (normalized_root / "J01" / "2025" / "file_pdf.json").read_bytes()
    second, second_errors = extract_rows(
        [row], extracted_root=extracted_root, normalized_root=normalized_root
    )

    assert first_errors == second_errors == 0
    assert first == second
    assert first[0]["text_extractable"] == "true"
    assert first[0]["text_extraction_quality"] == "research_candidate"
    assert (normalized_root / "J01" / "2025" / "file_pdf.json").read_bytes() == before
    sidecar = json.loads(before)
    assert sidecar["machine_generated"] is True
    assert sidecar["mathematically_verified"] is False
