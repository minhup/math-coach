from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

from scripts.corpus.core import (
    CorpusError,
    merge_rows,
    normalize_url,
    read_csv,
    sha256_file,
    write_csv,
)
from scripts.corpus.download_sources import (
    MIME_EXTENSIONS,
    content_disposition_filename,
    detect_mime,
)
from scripts.corpus.registry import (
    REGISTRY_FILE_FIELDS,
    REGISTRY_MISSING_FIELDS,
    USABLE_REGISTRY_STATUSES,
)

DEFAULT_PLAN = Path("data/corpus/manifests/registry_acquisition_plan.csv")
DEFAULT_FILES = Path("data/corpus/manifests/registry_files.csv")
DEFAULT_LEGACY_FILES = Path("data/corpus/manifests/files.csv")
DEFAULT_MISSING = Path("data/corpus/manifests/registry_missing_data.csv")
DEFAULT_RAW_ROOT = Path("data/corpus/raw/registry")
USER_AGENT = "math-coach-global-corpus-research/1.0"
MAX_FILE_BYTES = 100 * 1024 * 1024


def existing_row_is_valid(row: dict[str, str]) -> bool:
    if row.get("processing_status") not in USABLE_REGISTRY_STATUSES:
        return False
    path = Path(row.get("local_path", ""))
    try:
        expected_size = int(row.get("file_size", ""))
    except ValueError:
        return False
    return (
        path.is_file()
        and path.stat().st_size == expected_size
        and sha256_file(path) == row.get("sha256")
    )


def refresh_existing_row(row: dict[str, str], candidate: dict[str, str]) -> dict[str, object]:
    refreshed: dict[str, object] = dict(row)
    refreshed.update(
        {
            "collection_id": candidate["collection_id"],
            "logical_set_id": candidate["logical_set_id"],
            "year": candidate["year"],
            "artifact_type": candidate["artifact_type"],
            "source_url": candidate["source_url"],
            "discovery_url": candidate["discovery_url"],
            "url_role": candidate["url_role"],
            "source_type": candidate["source_type"],
            "official_status": candidate["official_status"],
            "language": candidate["language"],
            "rights_status": "unknown",
            "notes": candidate["notes"],
        }
    )
    return refreshed


def canonical_objects(*file_groups: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    objects: dict[str, dict[str, str]] = {}
    for rows in file_groups:
        for row in rows:
            digest = row.get("sha256", "")
            path = Path(row.get("local_path", ""))
            if not digest or not path.is_file() or sha256_file(path) != digest:
                continue
            current = objects.get(digest)
            if current is None or row.get("file_id", "") < current.get("file_id", ""):
                objects[digest] = row
    return objects


def _destination_dir(raw_root: Path, candidate: dict[str, str]) -> Path:
    year = candidate.get("year") or "unassigned"
    return raw_root / candidate["collection_id"] / year


def recover_existing_candidate(
    candidate: dict[str, str], raw_root: Path
) -> tuple[dict[str, object], dict[str, object] | None] | None:
    directory = _destination_dir(raw_root, candidate)
    matches = [
        path
        for path in directory.glob(f"{candidate['candidate_id']}.*")
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
        detected = detect_mime(handle.read(64 * 1024))
    row = base_file_row(candidate)
    row.update(
        {
            "retrieved_at": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(
                timespec="seconds"
            ),
            "http_status": "unknown",
            "final_url": "unknown",
            "original_filename": path.name,
            "local_path": path.as_posix(),
            "mime_type": "unknown",
            "detected_mime_type": detected,
            "file_size": path.stat().st_size,
            "sha256": sha256_file(path),
            "processing_status": "downloaded",
            "notes": "Recovered immutable object after an interrupted manifest write.",
        }
    )
    issue = classify_download(candidate, row)
    return row, issue


def base_file_row(candidate: dict[str, str]) -> dict[str, object]:
    source_url = normalize_url(candidate["source_url"])
    return {
        "file_id": candidate["candidate_id"],
        "collection_id": candidate["collection_id"],
        "logical_set_id": candidate["logical_set_id"],
        "year": candidate["year"],
        "artifact_type": candidate["artifact_type"],
        "source_url": candidate["source_url"],
        "discovery_url": candidate["discovery_url"],
        "source_domain": urlsplit(source_url).hostname or "",
        "url_role": candidate["url_role"],
        "source_type": candidate["source_type"],
        "official_status": candidate["official_status"],
        "retrieved_at": "",
        "http_status": "",
        "final_url": source_url,
        "original_filename": Path(unquote(urlsplit(source_url).path)).name,
        "local_path": "",
        "mime_type": "",
        "detected_mime_type": "",
        "file_size": "",
        "sha256": "",
        "byte_duplicate_of_file_id": "",
        "semantic_duplicate_of_file_id": "",
        "language": candidate["language"],
        "rights_status": "unknown",
        "processing_status": "download_failed",
        "page_count": "",
        "text_extractable": "unknown",
        "text_extraction_quality": "unassessed",
        "scan_quality": "unknown",
        "extraction_method": "none",
        "extracted_text_path": "",
        "notes": candidate["notes"],
    }


def classify_download(
    candidate: dict[str, str], row: dict[str, object]
) -> dict[str, object] | None:
    expected = candidate["expected_mime_type"]
    declared = str(row["mime_type"])
    detected = str(row["detected_mime_type"])
    method = candidate["acquisition_method"]
    problem = ""
    if detected == "text/html" and method != "html_snapshot":
        problem = "invalid_html_response"
        detail = "HTML response was returned for a document candidate."
    elif method == "html_snapshot" and detected != "text/html":
        problem = "mime_mismatch"
        detail = f"HTML snapshot expected; detected {detected}."
    elif expected not in {"", "unknown", detected}:
        compatible_docx = (
            expected.endswith("wordprocessingml.document") and detected == "application/zip"
        )
        if not compatible_docx:
            problem = "mime_mismatch"
            detail = f"Expected {expected}; detected {detected}."
    if not problem and declared not in {
        "",
        "application/octet-stream",
        "binary/octet-stream",
        detected,
    }:
        compatible_declared = detected == "application/zip" and declared.endswith(
            "wordprocessingml.document"
        )
        if not compatible_declared:
            problem = "mime_mismatch"
            detail = f"Declared {declared}; detected {detected}."
    if not problem:
        row["processing_status"] = "downloaded"
        return None
    row["processing_status"] = problem
    row["notes"] = f"{row['notes']} {detail}".strip()
    return missing_row(candidate, problem, "error", detail)


def download_candidate(
    candidate: dict[str, str],
    *,
    raw_root: Path,
    known_objects: dict[str, dict[str, str]] | None = None,
    retrieved_at: str | None = None,
    max_file_bytes: int = MAX_FILE_BYTES,
) -> tuple[dict[str, object], dict[str, object] | None]:
    known_objects = known_objects if known_objects is not None else {}
    source_url = normalize_url(candidate["source_url"])
    destination_dir = _destination_dir(raw_root, candidate)
    destination_dir.mkdir(parents=True, exist_ok=True)
    temporary_path = destination_dir / f".{candidate['candidate_id']}.part"
    temporary_path.unlink(missing_ok=True)
    row = base_file_row(candidate)
    row["retrieved_at"] = retrieved_at or datetime.now(UTC).isoformat(timespec="seconds")

    try:
        request = Request(source_url, headers={"User-Agent": USER_AGENT})
        with (
            urlopen(request, timeout=60) as response,
            temporary_path.open("xb") as output,
        ):
            row["http_status"] = str(response.status)
            row["final_url"] = normalize_url(response.geturl())
            row["mime_type"] = response.headers.get_content_type()
            header_size = response.headers.get("Content-Length")
            if header_size and int(header_size) > max_file_bytes:
                raise CorpusError(f"response exceeds {max_file_bytes} bytes")
            disposition = content_disposition_filename(response.headers.get("Content-Disposition"))
            if disposition:
                row["original_filename"] = disposition
            first_chunk = response.read(64 * 1024)
            if not first_chunk:
                raise CorpusError("zero-byte response")
            row["detected_mime_type"] = detect_mime(first_chunk)
            output.write(first_chunk)
            file_size = len(first_chunk)
            while chunk := response.read(1024 * 1024):
                file_size += len(chunk)
                if file_size > max_file_bytes:
                    raise CorpusError(f"response exceeds {max_file_bytes} bytes")
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())

        row["file_size"] = temporary_path.stat().st_size
        row["sha256"] = sha256_file(temporary_path)
        issue = classify_download(candidate, row)
        suffix = MIME_EXTENSIONS.get(
            str(row["detected_mime_type"]),
            Path(str(row["original_filename"])).suffix.casefold(),
        )
        suffix = suffix or ".bin"
        existing = known_objects.get(str(row["sha256"]))
        if existing and Path(existing["local_path"]).is_file():
            temporary_path.unlink()
            row["local_path"] = existing["local_path"]
            row["byte_duplicate_of_file_id"] = existing["file_id"]
            if row["processing_status"] == "downloaded":
                row["processing_status"] = "downloaded_reused"
        else:
            destination = destination_dir / f"{candidate['candidate_id']}{suffix}"
            if destination.exists():
                if sha256_file(destination) != row["sha256"]:
                    raise CorpusError(
                        f"immutable raw path already exists with different bytes: {destination}"
                    )
                temporary_path.unlink()
            else:
                temporary_path.replace(destination)
            row["local_path"] = destination.as_posix()
            known_objects[str(row["sha256"])] = {
                "file_id": str(row["file_id"]),
                "local_path": str(row["local_path"]),
                "sha256": str(row["sha256"]),
            }
        expected_size = candidate.get("expected_size", "")
        if expected_size and int(expected_size) != row["file_size"]:
            row["notes"] = (
                f"{row['notes']} Expected {expected_size} bytes; received {row['file_size']}."
            ).strip()
        return row, issue
    except (
        CorpusError,
        HTTPError,
        URLError,
        TimeoutError,
        OSError,
        ValueError,
    ) as error:
        temporary_path.unlink(missing_ok=True)
        row["notes"] = f"{row['notes']} {error}".strip()
        return row, missing_row(candidate, "download_failure", "error", str(error))


def missing_row(
    candidate: dict[str, str], issue_type: str, severity: str, details: str
) -> dict[str, object]:
    from scripts.corpus.core import deterministic_id

    return {
        "issue_id": deterministic_id("rissue", candidate["candidate_id"], issue_type),
        "collection_id": candidate["collection_id"],
        "logical_set_id": candidate["logical_set_id"],
        "year": candidate["year"],
        "issue_type": issue_type,
        "severity": severity,
        "related_id": candidate["candidate_id"],
        "source_url": candidate["source_url"],
        "status": "open",
        "details": details,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download expanded registry assets atomically.")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--files", type=Path, default=DEFAULT_FILES)
    parser.add_argument("--legacy-files", type=Path, default=DEFAULT_LEGACY_FILES)
    parser.add_argument("--missing", type=Path, default=DEFAULT_MISSING)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--max-file-bytes", type=int, default=MAX_FILE_BYTES)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates = [row for row in read_csv(args.plan) if row["selected"] == "yes"]
    if args.limit is not None:
        candidates = candidates[: args.limit]
    existing = read_csv(args.files) if args.files.exists() else []
    legacy = read_csv(args.legacy_files) if args.legacy_files.exists() else []
    existing_by_id = {row["file_id"]: row for row in existing}
    known = canonical_objects(legacy, existing)
    existing_missing = read_csv(args.missing) if args.missing.exists() else []
    rows: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []
    unchanged = 0
    downloads = 0
    for candidate in candidates:
        prior = existing_by_id.get(candidate["candidate_id"])
        if prior and existing_row_is_valid(prior):
            rows.append(refresh_existing_row(prior, candidate))
            unchanged += 1
            continue
        recovered = recover_existing_candidate(candidate, args.raw_root)
        if recovered:
            row, issue = recovered
            unchanged += 1
        else:
            row, issue = download_candidate(
                candidate,
                raw_root=args.raw_root,
                known_objects=known,
                max_file_bytes=args.max_file_bytes,
            )
            downloads += row["processing_status"] in {"downloaded", "downloaded_reused"}
        rows.append(row)
        if issue:
            issues.append(issue)

    processed = {row["candidate_id"] for row in candidates}
    retained_issues = [
        row
        for row in existing_missing
        if not (
            row["related_id"] in processed
            and row["issue_type"] in {"download_failure", "invalid_html_response", "mime_mismatch"}
        )
    ]
    merged = merge_rows(existing, rows, key="file_id")
    write_csv(args.files, REGISTRY_FILE_FIELDS, merged)
    write_csv(
        args.missing,
        REGISTRY_MISSING_FIELDS,
        merge_rows(retained_issues, issues, key="issue_id"),
    )
    failures = sum(row["processing_status"] not in USABLE_REGISTRY_STATUSES for row in rows)
    reused = sum(row["processing_status"] == "downloaded_reused" for row in rows)
    print(
        f"Processed {len(candidates)} candidates: {unchanged} unchanged, "
        f"{downloads} downloaded ({reused} byte-reused), {failures} failed/invalid"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
