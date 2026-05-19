# ingestion/inspect_documents.py — Week 2 Day 10 data quality check
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.db import run_query


def main():
    total = run_query("SELECT COUNT(*) FROM documents", fetch=True)[0][0]
    print(f"Total documents: {total}\n")

    by_source = run_query(
        """
        SELECT s.name, COUNT(d.id)
        FROM sources s
        LEFT JOIN documents d ON d.source_id = s.id
        GROUP BY s.name
        ORDER BY s.name
        """,
        fetch=True,
    )
    print("By source:")
    for name, count in by_source:
        print(f"  {name}: {count}")

    samples = run_query(
        """
        SELECT title, jurisdiction, LEFT(content, 80) AS preview
        FROM documents
        ORDER BY scraped_at DESC
        LIMIT 5
        """,
        fetch=True,
    )
    print("\nLatest 5 documents:")
    for title, jurisdiction, preview in samples:
        print(f"  [{jurisdiction}] {title[:70]}")
        print(f"    {preview}...")


if __name__ == "__main__":
    main()
