from __future__ import annotations

from pathlib import Path

from scripts.corpus.build_global_registry import build_registry
from scripts.corpus.core import write_csv
from scripts.corpus.registry import (
    REGISTRY_COLLECTION_FIELDS,
    REGISTRY_FILE_FIELDS,
    REGISTRY_URL_FIELDS,
)
from scripts.corpus.report_registry import generated_snapshot, update_report
from tests.corpus.test_global_registry import write_registry_workbook


def test_registry_report_lists_all_workbook_collections(tmp_path: Path) -> None:
    workbook = tmp_path / "registry.xlsx"
    write_registry_workbook(workbook)
    collections, urls = build_registry(workbook, "2026-08-26")
    manifests = tmp_path / "manifests"
    write_csv(manifests / "registry_collections.csv", REGISTRY_COLLECTION_FIELDS, collections)
    write_csv(manifests / "registry_urls.csv", REGISTRY_URL_FIELDS, urls)

    snapshot = generated_snapshot(manifests)

    assert "| Workbook collections registered | 2 |" in snapshot
    assert "| Initial P0/P0X batch collections | 2 |" in snapshot
    assert "`V01`" in snapshot
    assert "`J01`" in snapshot


def test_registry_report_separates_sets_provenance_and_physical_objects(
    tmp_path: Path,
) -> None:
    manifests = tmp_path / "manifests"
    raw = tmp_path / "raw" / "one.pdf"
    raw.parent.mkdir()
    raw.write_bytes(b"%PDF-1.7\nfixture")
    rows = []
    for file_id in ("first", "second"):
        row = {field: "" for field in REGISTRY_FILE_FIELDS}
        row.update(
            {
                "file_id": file_id,
                "collection_id": "J01",
                "logical_set_id": "set_j01_2025",
                "year": "2025",
                "artifact_type": "question" if file_id == "first" else "solution",
                "source_url": f"https://example.test/{file_id}",
                "local_path": raw.as_posix(),
                "detected_mime_type": "application/pdf",
                "file_size": str(raw.stat().st_size),
                "sha256": "same-checksum",
                "official_status": "official",
                "processing_status": "extracted",
                "text_extractable": "true",
            }
        )
        rows.append(row)
    write_csv(manifests / "registry_files.csv", REGISTRY_FILE_FIELDS, rows)

    snapshot = generated_snapshot(manifests)

    assert "| Distinct eligible actual sets | 1 |" in snapshot
    assert "| Raw provenance/file rows | 2 |" in snapshot
    assert "| Unique SHA-256 objects | 1 |" in snapshot
    assert "| Physical raw paths | 1 |" in snapshot
    assert "| Byte-duplicate provenance rows | 1 |" in snapshot


def test_registry_report_update_is_idempotent(tmp_path: Path) -> None:
    report = tmp_path / "status.md"
    report.write_text(
        "# Status\n\n## Current acquisition snapshot\n\nstale\n\n"
        "### Official verification anchors for the existing core\n\nkeep\n",
        encoding="utf-8",
    )
    snapshot = generated_snapshot(tmp_path / "manifests")

    update_report(report, snapshot)
    first = report.read_bytes()
    update_report(report, snapshot)

    assert report.read_bytes() == first
    assert b"stale" not in first
    assert b"keep" in first
