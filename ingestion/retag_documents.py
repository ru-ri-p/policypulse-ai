# ingestion/retag_documents.py — backfill zones, sectors, playbook impacts
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.db import run_query
from ingestion.tagging import tag_document


def retag_all(limit: int | None = None):
    rows = run_query(
        f"""
        SELECT d.id, d.title, d.url, d.content, d.jurisdiction, s.name
        FROM documents d
        LEFT JOIN sources s ON s.id = d.source_id
        ORDER BY d.id
        {"LIMIT %s" if limit else ""}
        """,
        (limit,) if limit else None,
        fetch=True,
    )

    updated = 0
    for row in rows:
        doc_id, title, url, content, jurisdiction, source_name = row
        zones, sectors, impacts = tag_document(
            title or "",
            url or "",
            content or "",
            source_name or "",
            jurisdiction,
        )
        run_query(
            """
            UPDATE documents
            SET zones = %s,
                sectors = %s,
                playbook_impacts = %s::jsonb,
                region = COALESCE(region, %s)
            WHERE id = %s
            """,
            (
                zones,
                sectors,
                json.dumps(impacts),
                _region_from_jurisdiction(jurisdiction),
                doc_id,
            ),
        )
        updated += 1
        if updated % 100 == 0:
            print(f"Tagged {updated} documents...")

    print(f"Done. Tagged {updated} documents.")


def _region_from_jurisdiction(jurisdiction: str | None) -> str:
    from ingestion.regions import get_region

    return get_region(jurisdiction)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backfill zone/sector/playbook tags")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    retag_all(limit=args.limit)
