from __future__ import annotations

import argparse
import json
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from scripts.corpus.core import read_csv, write_csv
from scripts.corpus.registry import REGISTRY_FILE_FIELDS, USABLE_REGISTRY_STATUSES

DEFAULT_FILES = Path("data/corpus/manifests/registry_files.csv")
DEFAULT_EXTRACTED = Path("data/corpus/extracted/registry")
DEFAULT_NORMALIZED = Path("data/corpus/normalized/registry")
WORD_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


class HTMLTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text: list[str] = []
        self._ignored = 0

    def handle_starttag(self, tag: str, _attributes: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._ignored += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored:
            self._ignored -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored and data.strip():
            self.text.append(data.strip())


def text_quality(text: str) -> str:
    if sum(character.isalnum() for character in text) < 40:
        return "empty_or_insufficient"
    replacement_ratio = text.count("�") / max(len(text), 1)
    return "garbled_or_low_quality" if replacement_ratio > 0.01 else "research_candidate"


def extract_docx_text(path: Path) -> str:
    try:
        with ZipFile(path) as archive:
            root = ElementTree.fromstring(archive.read("word/document.xml"))
    except (BadZipFile, KeyError, ElementTree.ParseError) as error:
        raise ValueError(f"invalid DOCX: {error}") from error
    namespace = {"w": WORD_NAMESPACE}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        value = "".join(node.text or "" for node in paragraph.findall(".//w:t", namespace))
        if value:
            paragraphs.append(value)
    return "\n".join(paragraphs)


def extract_html_text(path: Path) -> str:
    parser = HTMLTextParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parser.text)


def extract_rows(
    files: list[dict[str, str]], *, extracted_root: Path, normalized_root: Path
) -> tuple[list[dict[str, object]], int]:
    rows: list[dict[str, object]] = []
    errors = 0
    for original in files:
        row: dict[str, object] = dict(original)
        if original["processing_status"] not in USABLE_REGISTRY_STATUSES:
            rows.append(row)
            continue
        path = Path(original["local_path"])
        output_dir = extracted_root / original["collection_id"] / (original["year"] or "unassigned")
        output_path = output_dir / f"{original['file_id']}.txt"
        temporary = output_path.with_suffix(".txt.tmp")
        text = ""
        method = "none"
        failed = ""
        detected = original["detected_mime_type"]
        if detected == "application/pdf":
            output_dir.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                ["pdftotext", "-layout", str(path), str(temporary)],
                capture_output=True,
                check=False,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                text = temporary.read_text(encoding="utf-8", errors="replace")
                method = "native_pdftotext"
            else:
                failed = result.stderr.strip() or "pdftotext failed"
        elif detected == "text/html":
            text = extract_html_text(path)
            method = "native_html"
        elif (
            detected == "application/zip"
            and Path(original["original_filename"]).suffix.casefold() == ".docx"
        ):
            try:
                text = extract_docx_text(path)
                method = "native_docx_xml"
            except ValueError as error:
                failed = str(error)

        quality = text_quality(text) if not failed and method != "none" else "not_applicable"
        if failed:
            temporary.unlink(missing_ok=True)
            row["text_extractable"] = "false"
            row["text_extraction_quality"] = "extraction_failed"
            row["extraction_method"] = f"{method or 'native'}_failed"
            row["notes"] = f"{row['notes']} Extraction: {failed}".strip()
            errors += 1
        elif method != "none" and quality != "empty_or_insufficient":
            output_dir.mkdir(parents=True, exist_ok=True)
            if not temporary.exists():
                temporary.write_text(text, encoding="utf-8")
            temporary.replace(output_path)
            row["text_extractable"] = "true"
            row["text_extraction_quality"] = quality
            row["scan_quality"] = "not_applicable"
            row["extraction_method"] = method
            row["extracted_text_path"] = output_path.as_posix()
        else:
            temporary.unlink(missing_ok=True)
            row["text_extractable"] = "false"
            row["text_extraction_quality"] = (
                quality if quality == "empty_or_insufficient" else "not_applicable"
            )
            row["scan_quality"] = "unassessed" if detected.startswith("image/") else "unknown"
            row["extraction_method"] = method

        normalized_dir = (
            normalized_root / original["collection_id"] / (original["year"] or "unassigned")
        )
        normalized_dir.mkdir(parents=True, exist_ok=True)
        sidecar_path = normalized_dir / f"{original['file_id']}.json"
        sidecar_temporary = sidecar_path.with_suffix(".json.tmp")
        sidecar = {
            "file_id": row["file_id"],
            "collection_id": row["collection_id"],
            "logical_set_id": row["logical_set_id"],
            "artifact_type": row["artifact_type"],
            "source_sha256": row["sha256"],
            "detected_mime_type": row["detected_mime_type"],
            "page_count": int(str(row["page_count"])) if str(row["page_count"]) else None,
            "text_extractable": row["text_extractable"],
            "text_extraction_quality": row["text_extraction_quality"],
            "extraction_method": row["extraction_method"],
            "machine_generated": True,
            "mathematically_verified": False,
        }
        sidecar_temporary.write_text(
            json.dumps(sidecar, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        sidecar_temporary.replace(sidecar_path)
        row["processing_status"] = "extracted"
        rows.append(row)
    return rows, errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract expanded registry content.")
    parser.add_argument("--files", type=Path, default=DEFAULT_FILES)
    parser.add_argument("--extracted-root", type=Path, default=DEFAULT_EXTRACTED)
    parser.add_argument("--normalized-root", type=Path, default=DEFAULT_NORMALIZED)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows, errors = extract_rows(
        read_csv(args.files),
        extracted_root=args.extracted_root,
        normalized_root=args.normalized_root,
    )
    write_csv(args.files, REGISTRY_FILE_FIELDS, rows)
    extracted = sum(bool(row["extracted_text_path"]) for row in rows)
    print(f"Processed {len(rows)} registry files; {extracted} text artifacts; {errors} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
