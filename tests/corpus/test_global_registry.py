from __future__ import annotations

from html import escape
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from scripts.corpus.build_global_registry import build_registry
from scripts.corpus.discover_registry_assets import (
    discover_html_assets,
    discover_readme_assets,
    discover_repository_files,
    drive_download_url,
    is_target_asset,
    within_initial_readme_scope,
)
from scripts.corpus.registry import (
    artifact_type,
    collection_wave,
    github_repository_path,
    infer_year,
    logical_set_id,
)
from tests.corpus.test_core import write_minimal_workbook


def test_expanded_registry_parses_master_rows(tmp_path: Path) -> None:
    workbook = tmp_path / "registry.xlsx"
    write_registry_workbook(workbook)

    collections, urls = build_registry(workbook, "2026-08-26")

    assert len(collections) == 2
    assert len(urls) == 4
    assert len({row["registry_url_id"] for row in urls}) == 4
    by_id = {row["collection_id"]: row for row in collections}
    assert by_id["V01"]["acquisition_wave"] == "wave_1_vietnam_core"
    assert by_id["J01"]["acquisition_wave"] == "wave_2_jbmo_core"
    v01_roles = {row["url_role"] for row in urls if row["collection_id"] == "V01"}
    assert v01_roles == {"official", "mirror_1"}


def test_registry_helpers_keep_logical_sets_separate_from_files() -> None:
    assert github_repository_path("https://github.com/owner/repository") == (
        "owner",
        "repository",
    )
    assert github_repository_path("https://gist.github.com/owner") is None
    assert infer_year("JBMO 2024 solutions.pdf") == "2024"
    assert artifact_type("JBMO-2024-solutions.pdf") == "solution"
    assert artifact_type("2024-shortlist.pdf") == "shortlist"
    assert logical_set_id("J01", "2024", "question") == logical_set_id("J01", "2024", "solution")
    assert logical_set_id("J01", "2024", "shortlist") != logical_set_id("J01", "2024", "question")
    assert collection_wave("V10", "P1") == "wave_1b_vietnam_expansion"


def test_existing_minimal_workbook_is_not_an_expanded_registry(tmp_path: Path) -> None:
    workbook = tmp_path / "minimal.xlsx"
    write_minimal_workbook(workbook)

    collections, urls = build_registry(workbook, "2026-08-26")

    assert collections == []
    assert urls == []


def test_registry_asset_discovery_normalizes_direct_links() -> None:
    html = """
    <a href="/files/JBMO-2024-problems.pdf"> Problems
       Download </a>
    <a href="https://drive.google.com/file/d/file_123/view?usp=sharing">Solutions</a>
    <a href="/about">About</a>
    """

    assets = discover_html_assets(html, "https://contest.example/problems")

    assert assets == [
        (
            "https://contest.example/files/JBMO-2024-problems.pdf",
            "Problems Download",
        ),
        (
            "https://drive.usercontent.google.com/download?authuser=0&confirm=t&export=download&id=file_123",
            "Solutions",
        ),
    ]
    assert drive_download_url("https://drive.google.com/file/d/file_123/view") is not None


def test_registry_asset_discovery_prefers_page_content_over_navigation() -> None:
    html = """
    <div class="post-body entry-content">
      <h2>JBMO 2024</h2>
      <a href="/files/problems.pdf">Problems</a>
    </div>
    <footer><a href="/unrelated.pdf">Unrelated archive</a></footer>
    """

    assets = discover_html_assets(html, "https://contest.example/problems")

    assert len(assets) == 1
    assert assets[0][0] == "https://contest.example/files/problems.pdf"
    assert "JBMO 2024" in assets[0][1]


def test_registry_readme_discovery_preserves_year_scope() -> None:
    readme = """
    ## 2024-2025:
    ![page 1](https://github.com/user-attachments/assets/fixture)
    """

    assert discover_readme_assets(readme) == [
        (
            "https://github.com/user-attachments/assets/fixture",
            "2024-2025 page 1",
        )
    ]
    assert within_initial_readme_scope("V08", "2024")
    assert not within_initial_readme_scope("V08", "2010")
    assert is_target_asset(
        "DOWNLOAD",
        "official",
        "https://contest.example/JBMO_2024_English.pdf",
        "English",
    )
    assert not is_target_asset(
        "DOWNLOAD",
        "official",
        "https://contest.example/regulations.pdf",
        "Regulations",
    )


def test_registry_github_tree_discovers_only_supported_documents() -> None:
    tree = [
        {"type": "blob", "path": "2024/questions.pdf", "size": 12},
        {"type": "blob", "path": "README.md", "size": 13},
        {"type": "tree", "path": "2023"},
    ]

    assert discover_repository_files(tree, owner="owner", repository="repo", branch="main") == [
        (
            "https://raw.githubusercontent.com/owner/repo/main/2024/questions.pdf",
            "2024/questions.pdf",
            "12",
        )
    ]


def write_registry_workbook(path: Path) -> None:
    workbook = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Master Download Queue" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
    relationships = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""
    rows = [
        {"A": "ID", "B": "Priority", "D": "Source"},
        {
            "A": "V01",
            "B": "P0",
            "C": "Vietnam",
            "D": "PTNK archive",
            "I": "https://ptnk.example.test/archive",
            "J": "https://github.com/example/ptnk",
            "N": "DOWNLOAD",
        },
        {
            "A": "J01",
            "B": "P0X",
            "C": "Balkans",
            "D": "JBMO archive",
            "I": "https://jbmo.example.test/problems",
            "K": "https://aops.example.test/jbmo",
            "N": "DOWNLOAD",
        },
    ]
    xml_rows = []
    for number, row in enumerate(rows, start=1):
        cells = "".join(
            f'<c r="{column}{number}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
            for column, value in row.items()
        )
        xml_rows.append(f'<row r="{number}">{cells}</row>')
    worksheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(xml_rows)}</sheetData></worksheet>"
    )
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", relationships)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)
