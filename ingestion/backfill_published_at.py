# ingestion/backfill_published_at.py — set policy publication dates on existing rows
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.date_extract import infer_document_published_at
from ingestion.db import run_query


def backfill(limit: int | None = None, only_missing: bool = True):
    where = "WHERE published_at IS NULL" if only_missing else ""
    rows = run_query(
        f"""
        SELECT d.id, d.title, d.url, d.content, s.name
        FROM documents d
        LEFT JOIN sources s ON s.id = d.source_id
        {where}
        ORDER BY d.id
        {"LIMIT %s" if limit else ""}
        """,
        (limit,) if limit else None,
        fetch=True,
    )

    updated = 0
    for doc_id, title, url, content, source_name in rows:
        published = infer_document_published_at(
            title or "",
            url or "",
            content or "",
            source_name or "",
        )
        if not published:
            continue
        run_query(
            "UPDATE documents SET published_at = %s WHERE id = %s",
            (published, doc_id),
        )
        updated += 1
        if updated % 200 == 0:
            print(f"Set published_at on {updated} documents...")

    print(f"Done. Set publication date on {updated} / {len(rows)} documents examined.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backfill documents.published_at")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--all", action="store_true", help="Re-infer even if published_at set")
    args = parser.parse_args()
    backfill(limit=args.limit, only_missing=not args.all)
