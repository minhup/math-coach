from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from scripts.corpus.core import FILE_FIELDS, read_csv, write_csv

DEFAULT_FILES = Path("data/corpus/manifests/files.csv")
DEFAULT_EXTRACTED = Path("data/corpus/extracted")
DEFAULT_NORMALIZED = Path("data/corpus/normalized")
USABLE_STATUSES = {"downloaded", "downloaded_recovered", "validated", "extracted"}
VIETNAMESE_EXAM_MARKERS = (
    "bài ",
    "chứng minh",
    "đáp án",
    "đề thi",
    "môn thi",
    "thời gian",
    "tuyển sinh",
)


def native_text_quality(text: str) -> str:
    if sum(character.isalnum() for character in text) < 40:
        return "empty_or_insufficient"
    folded = text.casefold()
    marker_count = sum(marker in folded for marker in VIETNAMESE_EXAM_MARKERS)
    return "research_useful" if marker_count >= 2 else "garbled_or_low_quality"


def extract_rows(
    files: list[dict[str, str]],
    *,
    extracted_root: Path,
    normalized_root: Path,
) -> tuple[list[dict[str, object]], int]:
    results: list[dict[str, object]] = []
    errors = 0
    for original in files:
        row: dict[str, object] = dict(original)
        if original["processing_status"] not in USABLE_STATUSES or not original["local_path"]:
            results.append(row)
            continue
        local_path = Path(original["local_path"])
        if original["detected_mime_type"] == "application/pdf":
            output_path = (
                extracted_root
                / original["exam_family"]
                / original["year"]
                / f"{original['file_id']}.txt"
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = output_path.with_suffix(".txt.tmp")
            result = subprocess.run(
                ["pdftotext", "-layout", str(local_path), str(temporary_path)],
                capture_output=True,
                check=False,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                text = temporary_path.read_text(encoding="utf-8", errors="replace")
                quality = native_text_quality(text)
                if quality != "empty_or_insufficient":
                    temporary_path.replace(output_path)
                    row["text_extractable"] = "true"
                    row["text_extraction_quality"] = quality
                    row["scan_quality"] = "not_applicable"
                    row["extraction_method"] = "native_pdftotext"
                    row["extracted_text_path"] = output_path.as_posix()
                else:
                    temporary_path.unlink(missing_ok=True)
                    row["text_extractable"] = "false"
                    row["text_extraction_quality"] = quality
                    row["scan_quality"] = "unassessed"
                    row["extraction_method"] = "native_pdftotext_empty"
            else:
                temporary_path.unlink(missing_ok=True)
                row["text_extractable"] = "false"
                row["text_extraction_quality"] = "extraction_failed"
                row["scan_quality"] = "unknown"
                row["extraction_method"] = "pdftotext_failed"
                row["notes"] = f"{row['notes']} pdftotext: {result.stderr.strip()}".strip()
                errors += 1
        else:
            row["text_extractable"] = "false"
            row["text_extraction_quality"] = "not_applicable"
            row["scan_quality"] = (
                "unassessed" if str(row["detected_mime_type"]).startswith("image/") else "unknown"
            )
            row["extraction_method"] = "none"

        sidecar_path = (
            normalized_root
            / original["exam_family"]
            / original["year"]
            / f"{original['file_id']}.json"
        )
        sidecar_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_sidecar = sidecar_path.with_suffix(".json.tmp")
        sidecar = {
            "file_id": row["file_id"],
            "source_sha256": row["sha256"],
            "detected_mime_type": row["detected_mime_type"],
            "page_count": row["page_count"] or None,
            "text_extractable": row["text_extractable"],
            "text_extraction_quality": row["text_extraction_quality"],
            "extraction_method": row["extraction_method"],
            "machine_generated": True,
            "mathematically_verified": False,
        }
        temporary_sidecar.write_text(
            json.dumps(sidecar, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary_sidecar.replace(sidecar_path)
        row["processing_status"] = "extracted"
        results.append(row)
    return results, errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract native text and normalized sidecars.")
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
    write_csv(args.files, FILE_FIELDS, rows)
    extracted = sum(row["extracted_text_path"] != "" for row in rows)
    print(f"Processed {len(rows)} files; {extracted} native-text artifacts; {errors} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
