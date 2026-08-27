from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from scripts.corpus.build_manifest import build_manifests
from scripts.corpus.build_source_inventory import (
    build_inventory,
    classify_source,
    family_from_exam_name,
)
from scripts.corpus.core import (
    CorpusError,
    deterministic_id,
    merge_rows,
    normalize_url,
    read_csv,
    sha256_file,
    write_csv,
)
from scripts.corpus.discover_github_archives import (
    classify_paper_type,
    github_repository_path,
)


def test_url_source_and_metadata_normalization() -> None:
    assert normalize_url("HTTPS://Example.COM:443/a?z=2&a=1#fragment") == (
        "https://example.com/a?a=1&z=2"
    )
    assert github_repository_path("https://github.com/owner/archive.git") == (
        "owner",
        "archive",
    )
    assert classify_paper_type("Đề-tuyển-sinh-2025.pdf") == "question_paper"
    assert classify_paper_type("DAP-AN_2025.pdf") == "answer_key"
    assert family_from_exam_name("Hà Nội Sở Chuyên") == "hanoi_so"
    assert classify_source("ptnk.edu.vn", "")[1:] == ("official", "authoritative")
    assert classify_source("github.com", "")[0] == "community_github_archive"
    assert classify_source("hoamatoan.edu.vn", "")[2] == "commercial_reference_only"
    with pytest.raises(CorpusError):
        normalize_url("ftp://example.com/file.pdf")


def test_deterministic_ids_checksums_and_idempotent_csv(tmp_path: Path) -> None:
    assert deterministic_id("exam", "ptnk", "2024") == "exam_58d7aa769acd6577c2f7"
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"math-coach-corpus")
    assert sha256_file(fixture) == (
        "16cd13706622b692d92be41c9cc5979c7d41d78a996891f0a31f9375e2e66a70"
    )

    rows = merge_rows(
        [{"id": "b", "value": "old"}],
        [{"id": "a", "value": "first"}, {"id": "b", "value": "new"}],
        key="id",
    )
    assert rows == [{"id": "a", "value": "first"}, {"id": "b", "value": "new"}]
    output = tmp_path / "manifest.csv"
    write_csv(output, ("id", "value"), rows)
    first_bytes = output.read_bytes()
    write_csv(output, ("id", "value"), rows)
    assert output.read_bytes() == first_bytes
    assert read_csv(output) == rows


def test_workbook_fixture_extracts_source_provenance(tmp_path: Path) -> None:
    workbook = tmp_path / "sources.xlsx"
    write_minimal_workbook(workbook)

    records = build_inventory(workbook, "2026-08-26")

    assert len(records) == 1
    record = records[0]
    assert record["source_url"] == "https://ptnk.edu.vn/de-thi/"
    assert record["source_type"] == "official_school"
    assert record["exam_families"] == "ptnk"
    assert record["workbook_locations"] == "Sources!C2"
    assert record["rights_status"] == "unknown"


def test_exam_manifest_distinguishes_located_official_files_from_acquired_files() -> None:
    plan = [
        {
            "exam_family": "hnue",
            "calendar_year": "2023",
            "academic_year": "2023-2024",
            "paper_type": paper_type,
            "official_status": "official",
        }
        for paper_type in ("question_paper", "answer_key")
    ]

    exams, issues = build_manifests(plan, [], start_year=2023, end_year=2023)

    assert len(exams) == 1
    assert exams[0]["official_source_available"] == "yes"
    assert exams[0]["question_file_id"] == ""
    assert exams[0]["answer_file_id"] == ""
    issue_types = {issue["issue_type"] for issue in issues}
    assert "official_question_not_acquired" in issue_types
    assert "official_answer_not_acquired" in issue_types
    assert "official_question_not_located" not in issue_types
    assert "official_answer_not_located" not in issue_types


def write_minimal_workbook(path: Path) -> None:
    workbook = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Sources" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
    relationships = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""
    worksheet = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1"><c r="A1" t="inlineStr"><is><t>Source</t></is></c></row>
    <row r="2">
      <c r="A2" t="inlineStr"><is><t>PTNK official exam</t></is></c>
      <c r="B2" t="inlineStr"><is><t>Official school</t></is></c>
      <c r="C2" t="inlineStr"><is><t>https://ptnk.edu.vn/de-thi/</t></is></c>
      <c r="D2" t="inlineStr"><is><t>2024</t></is></c>
      <c r="E2" t="inlineStr"><is><t>Official exam availability</t></is></c>
    </row>
  </sheetData>
</worksheet>"""
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", relationships)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)
