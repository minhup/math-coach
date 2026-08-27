from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from scripts.corpus.core import deterministic_id, sha256_file
from scripts.corpus.download_registry_sources import (
    canonical_objects,
    download_candidate,
    existing_row_is_valid,
    recover_existing_candidate,
)


class RegistryFixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in {"/first.pdf", "/second.pdf"}:
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", 'attachment; filename="fixture.pdf"')
            self.end_headers()
            self.wfile.write(b"%PDF-1.7\nregistry fixture")
            return
        if self.path == "/page":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<!doctype html><title>Registry page</title>")
            return
        self.send_error(404)

    def log_message(self, _format: str, *_args: object) -> None:
        return


@contextmanager
def fixture_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), RegistryFixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def candidate(
    url: str,
    *,
    collection_id: str = "J01",
    method: str = "direct_file",
    mime_type: str = "application/pdf",
) -> dict[str, str]:
    candidate_id = deterministic_id("gcand", collection_id, url)
    return {
        "candidate_id": candidate_id,
        "collection_id": collection_id,
        "logical_set_id": deterministic_id("set", collection_id, "2025", "contest"),
        "year": "2025",
        "artifact_type": "question",
        "source_url": url,
        "discovery_url": url,
        "url_role": "official",
        "source_type": "official_organization",
        "official_status": "official",
        "expected_mime_type": mime_type,
        "expected_size": "",
        "selected": "yes",
        "acquisition_method": method,
        "language": "en",
        "notes": "fixture",
    }


def test_registry_download_reuses_identical_bytes_across_provenance_rows(
    tmp_path: Path,
) -> None:
    with fixture_server() as base_url:
        first_candidate = candidate(f"{base_url}/first.pdf")
        first, first_issue = download_candidate(
            first_candidate,
            raw_root=tmp_path / "raw",
            known_objects={},
            retrieved_at="2026-08-26T00:00:00+00:00",
        )
        known = canonical_objects([{key: str(value) for key, value in first.items()}])
        second, second_issue = download_candidate(
            candidate(f"{base_url}/second.pdf", collection_id="J02"),
            raw_root=tmp_path / "raw",
            known_objects=known,
            retrieved_at="2026-08-26T00:00:00+00:00",
        )

    assert first_issue is second_issue is None
    assert first["processing_status"] == "downloaded"
    assert second["processing_status"] == "downloaded_reused"
    assert second["byte_duplicate_of_file_id"] == first["file_id"]
    assert second["local_path"] == first["local_path"]
    assert len(list((tmp_path / "raw").rglob("*.pdf"))) == 1
    assert existing_row_is_valid({key: str(value) for key, value in second.items()})

    recovered = recover_existing_candidate(first_candidate, tmp_path / "raw")
    assert recovered is not None
    assert recovered[0]["sha256"] == first["sha256"]


def test_registry_html_snapshot_is_allowed_but_document_masquerade_is_not(
    tmp_path: Path,
) -> None:
    with fixture_server() as base_url:
        snapshot, snapshot_issue = download_candidate(
            candidate(
                f"{base_url}/page",
                method="html_snapshot",
                mime_type="unknown",
            ),
            raw_root=tmp_path / "raw",
            retrieved_at="2026-08-26T00:00:00+00:00",
        )
        masquerade, masquerade_issue = download_candidate(
            candidate(f"{base_url}/page", collection_id="J02"),
            raw_root=tmp_path / "raw",
            retrieved_at="2026-08-26T00:00:00+00:00",
        )

    assert snapshot_issue is None
    assert snapshot["processing_status"] == "downloaded"
    assert Path(str(snapshot["local_path"])).suffix == ".html"
    assert masquerade["processing_status"] == "invalid_html_response"
    assert masquerade_issue is not None
    assert masquerade_issue["issue_type"] == "invalid_html_response"


def test_registry_download_failure_is_manifested_without_partial_file(
    tmp_path: Path,
) -> None:
    with fixture_server() as base_url:
        item = candidate(f"{base_url}/missing")
        row, issue = download_candidate(
            item,
            raw_root=tmp_path / "raw",
            retrieved_at="2026-08-26T00:00:00+00:00",
        )

    assert row["processing_status"] == "download_failed"
    assert row["local_path"] == ""
    assert issue is not None
    assert issue["issue_type"] == "download_failure"
    assert not list((tmp_path / "raw").rglob("*.part"))


def test_canonical_objects_ignores_missing_and_uses_stable_file_id(
    tmp_path: Path,
) -> None:
    path = tmp_path / "fixture.pdf"
    path.write_bytes(b"%PDF-1.7\nregistry fixture")
    digest = sha256_file(path)
    rows = [
        {"file_id": "z", "local_path": path.as_posix(), "sha256": digest},
        {"file_id": "a", "local_path": path.as_posix(), "sha256": digest},
        {"file_id": "wrong", "local_path": path.as_posix(), "sha256": "wrong"},
        {"file_id": "missing", "local_path": "missing.pdf", "sha256": "bad"},
    ]

    assert canonical_objects(rows)[digest]["file_id"] == "a"
    assert "wrong" not in canonical_objects(rows)
