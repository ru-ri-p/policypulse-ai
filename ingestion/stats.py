# ingestion/stats.py
from ingestion.db import run_query


def print_stats():
    total = run_query("SELECT COUNT(*) FROM documents", fetch=True)[0][0]
    by_jurisdiction = run_query(
        """
        SELECT jurisdiction, COUNT(*)
        FROM documents
        GROUP BY jurisdiction
        ORDER BY COUNT(*) DESC
        """,
        fetch=True,
    )
    by_source = run_query(
        """
        SELECT s.name, COUNT(d.id)
        FROM sources s
        LEFT JOIN documents d ON d.source_id = s.id
        GROUP BY s.name
        ORDER BY COUNT(d.id) DESC
        """,
        fetch=True,
    )

    print("\n=== PolicyPulse Database Stats ===")
    print(f"Total documents: {total}")
    print("\nBy jurisdiction:")
    for jurisdiction, count in by_jurisdiction:
        print(f"  {jurisdiction}: {count}")
    print("\nBy source:")
    for name, count in by_source:
        print(f"  {name}: {count}")
    print()

    return total


if __name__ == "__main__":
    print_stats()
