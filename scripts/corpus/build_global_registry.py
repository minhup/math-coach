from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from scripts.corpus.core import iter_xlsx_rows, write_csv
from scripts.corpus.registry import (
    REGISTRY_COLLECTION_FIELDS,
    REGISTRY_URL_FIELDS,
    parse_master_row,
    url_rows,
)

DEFAULT_WORKBOOK = Path("docs/research/global_math_problem_source_registry_expanded.xlsx")
DEFAULT_COLLECTIONS = Path("data/corpus/manifests/registry_collections.csv")
DEFAULT_URLS = Path("data/corpus/manifests/registry_urls.csv")


def build_registry(
    workbook: Path, inventory_date: str
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    collections: list[dict[str, object]] = []
    urls: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for sheet, row_number, cells in iter_xlsx_rows(workbook):
        if sheet != "Master Download Queue" or row_number == 1:
            continue
        collection = parse_master_row(cells, row_number=row_number, inventory_date=inventory_date)
        collection_id = str(collection["collection_id"])
        if collection_id in seen_ids:
            raise ValueError(f"duplicate registry collection ID: {collection_id}")
        seen_ids.add(collection_id)
        collections.append(collection)
        urls.extend(url_rows(cells, collection_id=collection_id, inventory_date=inventory_date))
    return collections, sorted(urls, key=lambda row: str(row["registry_url_id"]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the expanded global source registry.")
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    parser.add_argument("--collections", type=Path, default=DEFAULT_COLLECTIONS)
    parser.add_argument("--urls", type=Path, default=DEFAULT_URLS)
    parser.add_argument("--inventory-date", default=datetime.now(UTC).date().isoformat())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    collections, urls = build_registry(args.workbook, args.inventory_date)
    write_csv(args.collections, REGISTRY_COLLECTION_FIELDS, collections)
    write_csv(args.urls, REGISTRY_URL_FIELDS, urls)
    print(f"Wrote {len(collections)} registry collections and {len(urls)} URL provenance rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
