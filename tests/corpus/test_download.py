from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from scripts.corpus.core import deterministic_id
from scripts.corpus.download_sources import (
    detect_mime,
    download_candidate,
    existing_row_is_valid,
    recover_existing_candidate,
)


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/paper.pdf":
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", 'attachment; filename="paper.pdf"')
            self.end_headers()
            self.wfile.write(b"%PDF-1.7\nfixture")
            return
        if self.path == "/html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<!doctype html><title>not a file</title>")
            return
        self.send_error(404)

    def log_message(self, _format: str, *_args: object) -> None:
        return


@contextmanager
def fixture_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def candidate(url: str, expected_mime: str = "application/pdf") -> dict[str, str]:
    return {
        "candidate_id": deterministic_id("cand", "ptnk", "2024", url),
        "exam_family": "ptnk",
        "academic_year": "2024-2025",
        "calendar_year": "2024",
        "exam_variant": "fixture",
        "subject": "mathematics",
        "paper_type": "question_paper",
        "source_id": "src_fixture",
        "source_url": url,
        "discovery_url": url,
        "source_name": "fixture",
        "source_type": "official_school",
        "official_status": "official",
        "expected_mime_type": expected_mime,
        "expected_size": "",
        "selected": "yes",
        "rights_status": "unknown",
        "notes": "fixture",
    }


def test_signature_mime_detection() -> None:
    assert detect_mime(b"%PDF-1.7\n") == "application/pdf"
    assert detect_mime(b"\x89PNG\r\n\x1a\n") == "image/png"
    assert detect_mime(b"\xff\xd8\xff") == "image/jpeg"
    assert detect_mime(b"  <html>") == "text/html"
    assert detect_mime(b"unrecognized") == "application/octet-stream"


def test_download_is_atomic_and_recoverable_without_duplication(tmp_path: Path) -> None:
    with fixture_server() as base_url:
        item = candidate(f"{base_url}/paper.pdf")
        row, issue = download_candidate(
            item,
            raw_root=tmp_path / "raw",
            retrieved_at="2026-08-26T00:00:00+00:00",
        )

    assert issue is None
    assert row["processing_status"] == "downloaded"
    assert row["detected_mime_type"] == "application/pdf"
    assert row["original_filename"] == "paper.pdf"
    assert existing_row_is_valid({key: str(value) for key, value in row.items()})
    recovered = recover_existing_candidate(item, tmp_path / "raw")
    assert recovered is not None
    recovered_row, recovered_issue = recovered
    assert recovered_issue is None
    assert recovered_row["sha256"] == row["sha256"]
    assert len(list((tmp_path / "raw" / "ptnk" / "2024").glob("*.pdf"))) == 1


def test_download_failure_and_html_masquerading_are_recorded(tmp_path: Path) -> None:
    with fixture_server() as base_url:
        failed_row, failed_issue = download_candidate(
            candidate(f"{base_url}/missing"),
            raw_root=tmp_path / "raw",
            retrieved_at="2026-08-26T00:00:00+00:00",
        )
        html_row, html_issue = download_candidate(
            candidate(f"{base_url}/html"),
            raw_root=tmp_path / "raw",
            retrieved_at="2026-08-26T00:00:00+00:00",
        )

    assert failed_row["processing_status"] == "download_failed"
    assert failed_row["local_path"] == ""
    assert failed_issue is not None
    assert failed_issue["issue_type"] == "download_failure"
    assert html_row["processing_status"] == "invalid_html_response"
    assert html_row["detected_mime_type"] == "text/html"
    assert html_issue is not None
    assert html_issue["issue_type"] == "invalid_html_response"
