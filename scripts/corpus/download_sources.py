from __future__ import annotations

import argparse
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

from scripts.corpus.core import (
    FILE_FIELDS,
    MISSING_DATA_FIELDS,
    CorpusError,
    deterministic_id,
    merge_rows,
    normalize_url,
    read_csv,
    sha256_file,
    write_csv,
)

DEFAULT_PLAN = Path("data/corpus/manifests/acquisition_plan.csv")
DEFAULT_FILES = Path("data/corpus/manifests/files.csv")
DEFAULT_MISSING = Path("data/corpus/manifests/missing_data.csv")
DEFAULT_RAW_ROOT = Path("data/corpus/raw")
USER_AGENT = "math-coach-corpus-research/1.0"
MAX_FILE_BYTES = 30 * 1024 * 1024
MIME_EXTENSIONS = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "text/html": ".html",
    "application/zip": ".zip",
}
QUESTION_PAPER_TYPES = {"question_paper", "question_solution_bundle"}


def paper_presence(paper_type: str) -> tuple[str, str]:
    return (
        "yes" if paper_type in QUESTION_PAPER_TYPES else "unknown",
        "yes" if paper_type in {"answer_key", "question_solution_bundle"} else "unknown",
    )


def detect_mime(prefix: bytes) -> str:
    stripped = prefix.lstrip()
    if prefix.startswith(b"%PDF-"):
        return "application/pdf"
    if prefix.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if prefix.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if prefix.startswith(b"PK\x03\x04"):
        return "application/zip"
    if stripped[:64].lower().startswith((b"<!doctype html", b"<html", b"<head", b"<body")):
        return "text/html"
    return "application/octet-stream"


def content_disposition_filename(value: str | None) -> str:
    if not value:
        return ""
    encoded = re.search(r"filename\*=UTF-8''([^;]+)", value, flags=re.IGNORECASE)
    if encoded:
        return Path(unquote(encoded.group(1))).name
    plain = re.search(r'filename="?([^";]+)"?', value, flags=re.IGNORECASE)
    return Path(plain.group(1).strip()).name if plain else ""


def download_candidate(
    candidate: dict[str, str],
    *,
    raw_root: Path,
    retrieved_at: str | None = None,
    max_file_bytes: int = MAX_FILE_BYTES,
) -> tuple[dict[str, object], dict[str, object] | None]:
    source_url = normalize_url(candidate["source_url"])
    destination_dir = raw_root / candidate["exam_family"] / candidate["calendar_year"]
    destination_dir.mkdir(parents=True, exist_ok=True)
    temporary_path = destination_dir / f".{candidate['candidate_id']}.part"
    if temporary_path.exists():
        temporary_path.unlink()

    declared_mime = ""
    detected_mime = ""
    final_url = source_url
    original_filename = Path(urlsplit(source_url).path).name
    http_status = ""
    file_size = 0
    digest = ""
    local_path = ""
    status = "download_failed"
    notes: list[str] = []
    issue: dict[str, object] | None = None

    try:
        request = Request(source_url, headers={"User-Agent": USER_AGENT})
        with (
            urlopen(request, timeout=45) as response,
            temporary_path.open("xb") as output,
        ):
            http_status = str(response.status)
            final_url = normalize_url(response.geturl())
            declared_mime = response.headers.get_content_type()
            header_size = response.headers.get("Content-Length")
            if header_size and int(header_size) > max_file_bytes:
                raise CorpusError(f"response exceeds {max_file_bytes} bytes")
            disposition_name = content_disposition_filename(
                response.headers.get("Content-Disposition")
            )
            if disposition_name:
                original_filename = disposition_name
            first_chunk = response.read(64 * 1024)
            if not first_chunk:
                raise CorpusError("zero-byte response")
            detected_mime = detect_mime(first_chunk)
            output.write(first_chunk)
            file_size = len(first_chunk)
            while chunk := response.read(1024 * 1024):
                file_size += len(chunk)
                if file_size > max_file_bytes:
                    raise CorpusError(f"response exceeds {max_file_bytes} bytes")
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())

        suffix = MIME_EXTENSIONS.get(detected_mime, Path(original_filename).suffix.casefold())
        if not suffix:
            suffix = ".bin"
        destination = destination_dir / f"{candidate['candidate_id']}{suffix}"
        digest = sha256_file(temporary_path)
        if destination.exists():
            if sha256_file(destination) != digest:
                raise CorpusError(
                    f"immutable raw path already exists with different bytes: {destination}"
                )
            temporary_path.unlink()
        else:
            temporary_path.replace(destination)
        local_path = destination.as_posix()
        expected_mime = candidate["expected_mime_type"]
        if detected_mime == "text/html" and expected_mime != "text/html":
            status = "invalid_html_response"
            notes.append("HTML response was returned for a file candidate.")
        elif expected_mime not in {"", "unknown", detected_mime}:
            status = "mime_mismatch"
            notes.append(f"Expected {expected_mime}; detected {detected_mime}.")
        elif declared_mime not in {
            "",
            "application/octet-stream",
            "binary/octet-stream",
            detected_mime,
        }:
            status = "mime_mismatch"
            notes.append(f"Declared {declared_mime}; detected {detected_mime}.")
        else:
            status = "downloaded"
        expected_size = candidate["expected_size"]
        if expected_size and int(expected_size) != file_size:
            notes.append(f"Expected {expected_size} bytes; received {file_size}.")
    except (
        CorpusError,
        HTTPError,
        URLError,
        TimeoutError,
        OSError,
        ValueError,
    ) as error:
        if temporary_path.exists():
            temporary_path.unlink()
        notes.append(str(error))
        issue = missing_row(candidate, "download_failure", "error", str(error))

    paper_type = candidate["paper_type"]
    has_question_paper, has_answer_key = paper_presence(paper_type)
    row: dict[str, object] = {
        "file_id": candidate["candidate_id"],
        "exam_family": candidate["exam_family"],
        "year": candidate["calendar_year"],
        "academic_year": candidate["academic_year"],
        "exam_variant": candidate["exam_variant"],
        "subject": candidate["subject"],
        "paper_type": paper_type,
        "source_id": candidate["source_id"],
        "source_url": candidate["source_url"],
        "source_domain": urlsplit(source_url).hostname or "",
        "source_name": candidate["source_name"],
        "source_type": candidate["source_type"],
        "official_status": candidate["official_status"],
        "retrieved_at": retrieved_at or datetime.now(UTC).isoformat(timespec="seconds"),
        "http_status": http_status,
        "final_url": final_url,
        "original_filename": original_filename or f"{candidate['candidate_id']}.bin",
        "local_path": local_path,
        "mime_type": declared_mime,
        "detected_mime_type": detected_mime,
        "file_size": file_size if local_path else "",
        "sha256": digest,
        "duplicate_of_file_id": "",
        "language": "vi",
        "has_question_paper": has_question_paper,
        "has_answer_key": has_answer_key,
        "rights_status": candidate["rights_status"],
        "processing_status": status,
        "page_count": "",
        "text_extractable": "unknown",
        "text_extraction_quality": "unassessed",
        "scan_quality": "unknown",
        "extraction_method": "none",
        "extracted_text_path": "",
        "notes": " ".join(notes) or candidate["notes"],
    }
    if issue is None and status != "downloaded":
        issue = missing_row(candidate, status, "error", " ".join(notes))
    return row, issue


def missing_row(
    candidate: dict[str, str], issue_type: str, severity: str, details: str
) -> dict[str, object]:
    return {
        "issue_id": deterministic_id("issue", candidate["candidate_id"], issue_type),
        "exam_family": candidate["exam_family"],
        "year": candidate["calendar_year"],
        "issue_type": issue_type,
        "severity": severity,
        "related_id": candidate["candidate_id"],
        "source_url": candidate["source_url"],
        "status": "open",
        "details": details,
    }


def existing_row_is_valid(row: dict[str, str]) -> bool:
    if row["processing_status"] not in {
        "downloaded",
        "downloaded_recovered",
        "extracted",
        "validated",
    }:
        return False
    path = Path(row["local_path"])
    return (
        path.is_file()
        and path.stat().st_size == int(row["file_size"])
        and sha256_file(path) == row["sha256"]
    )


def refresh_existing_row(row: dict[str, str], candidate: dict[str, str]) -> dict[str, object]:
    has_question_paper, has_answer_key = paper_presence(candidate["paper_type"])
    refreshed: dict[str, object] = dict(row)
    refreshed.update(
        {
            "exam_family": candidate["exam_family"],
            "year": candidate["calendar_year"],
            "academic_year": candidate["academic_year"],
            "exam_variant": candidate["exam_variant"],
            "subject": candidate["subject"],
            "paper_type": candidate["paper_type"],
            "source_id": candidate["source_id"],
            "source_url": candidate["source_url"],
            "source_name": candidate["source_name"],
            "source_type": candidate["source_type"],
            "official_status": candidate["official_status"],
            "has_question_paper": has_question_paper,
            "has_answer_key": has_answer_key,
            "rights_status": candidate["rights_status"],
        }
    )
    return refreshed


def recover_existing_candidate(
    candidate: dict[str, str], raw_root: Path
) -> tuple[dict[str, object], dict[str, object] | None] | None:
    destination_dir = raw_root / candidate["exam_family"] / candidate["calendar_year"]
    matches = [
        path
        for path in destination_dir.glob(f"{candidate['candidate_id']}.*")
        if path.is_file() and path.suffix != ".part"
    ]
    if not matches:
        return None
    if len(matches) != 1:
        raise CorpusError(
            f"multiple immutable raw objects found for {candidate['candidate_id']}: {matches}"
        )
    path = matches[0]
    with path.open("rb") as handle:
        detected_mime = detect_mime(handle.read(64 * 1024))
    expected_mime = candidate["expected_mime_type"]
    status = "downloaded_recovered"
    details = "Recovered immutable object after an interrupted manifest write."
    issue = None
    if detected_mime == "text/html" and expected_mime != "text/html":
        status = "invalid_html_response"
        details += " HTML was returned for a file candidate."
        issue = missing_row(candidate, status, "error", details)
    elif expected_mime not in {"", "unknown", detected_mime}:
        status = "mime_mismatch"
        details += f" Expected {expected_mime}; detected {detected_mime}."
        issue = missing_row(candidate, status, "error", details)
    paper_type = candidate["paper_type"]
    has_question_paper, has_answer_key = paper_presence(paper_type)
    row: dict[str, object] = {
        "file_id": candidate["candidate_id"],
        "exam_family": candidate["exam_family"],
        "year": candidate["calendar_year"],
        "academic_year": candidate["academic_year"],
        "exam_variant": candidate["exam_variant"],
        "subject": candidate["subject"],
        "paper_type": paper_type,
        "source_id": candidate["source_id"],
        "source_url": candidate["source_url"],
        "source_domain": urlsplit(normalize_url(candidate["source_url"])).hostname or "",
        "source_name": candidate["source_name"],
        "source_type": candidate["source_type"],
        "official_status": candidate["official_status"],
        "retrieved_at": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(
            timespec="seconds"
        ),
        "http_status": "unknown",
        "final_url": "unknown",
        "original_filename": Path(urlsplit(candidate["source_url"]).path).name
        or f"{candidate['candidate_id']}{path.suffix}",
        "local_path": path.as_posix(),
        "mime_type": "unknown",
        "detected_mime_type": detected_mime,
        "file_size": path.stat().st_size,
        "sha256": sha256_file(path),
        "duplicate_of_file_id": "",
        "language": "vi",
        "has_question_paper": has_question_paper,
        "has_answer_key": has_answer_key,
        "rights_status": candidate["rights_status"],
        "processing_status": status,
        "page_count": "",
        "text_extractable": "unknown",
        "text_extraction_quality": "unassessed",
        "scan_quality": "unknown",
        "extraction_method": "none",
        "extracted_text_path": "",
        "notes": details,
    }
    return row, issue


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download selected corpus candidates atomically.")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--files", type=Path, default=DEFAULT_FILES)
    parser.add_argument("--missing", type=Path, default=DEFAULT_MISSING)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--max-file-bytes", type=int, default=MAX_FILE_BYTES)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--exam-variant-prefix",
        help="Process only selected candidates whose exam_variant starts with this value.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates = [row for row in read_csv(args.plan) if row["selected"] == "yes"]
    if args.exam_variant_prefix:
        candidates = [
            row for row in candidates if row["exam_variant"].startswith(args.exam_variant_prefix)
        ]
    if args.limit is not None:
        candidates = candidates[: args.limit]
    existing_files = read_csv(args.files) if args.files.exists() else []
    files_by_id = {row["file_id"]: row for row in existing_files}
    existing_missing = read_csv(args.missing) if args.missing.exists() else []
    new_files: list[dict[str, object]] = []
    new_issues: list[dict[str, object]] = []
    skipped = 0
    network_downloads = 0
    for candidate in candidates:
        prior = files_by_id.get(candidate["candidate_id"])
        if prior and existing_row_is_valid(prior):
            new_files.append(refresh_existing_row(prior, candidate))
            skipped += 1
            continue
        recovered = recover_existing_candidate(candidate, args.raw_root)
        if recovered is None:
            row, issue = download_candidate(
                candidate,
                raw_root=args.raw_root,
                max_file_bytes=args.max_file_bytes,
            )
            if row["processing_status"] == "downloaded":
                network_downloads += 1
        else:
            row, issue = recovered
            skipped += 1
        new_files.append(row)
        if issue:
            new_issues.append(issue)

    merged_files = merge_rows(existing_files, new_files, key="file_id")
    processed_ids = {candidate["candidate_id"] for candidate in candidates}
    retained_missing = [
        row
        for row in existing_missing
        if not (
            row["related_id"] in processed_ids
            and row["issue_type"] in {"download_failure", "invalid_html_response", "mime_mismatch"}
        )
    ]
    merged_issues = merge_rows(retained_missing, new_issues, key="issue_id")
    write_csv(args.files, FILE_FIELDS, merged_files)
    write_csv(args.missing, MISSING_DATA_FIELDS, merged_issues)
    failures = sum(
        str(row["processing_status"])
        not in {"downloaded", "downloaded_recovered", "extracted", "validated"}
        for row in new_files
    )
    print(
        f"Processed {len(candidates)} candidates: {skipped} unchanged, "
        f"{network_downloads} downloaded, {failures} failed/invalid"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
