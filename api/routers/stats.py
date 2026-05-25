# api/routers/stats.py
from fastapi import APIRouter

from ingestion.db import run_query
from ingestion.regions import get_region

router = APIRouter()


@router.get("/")
def get_stats():
    """Aggregate document counts for the dashboard."""
    total = run_query("SELECT COUNT(*) FROM documents", fetch=True)[0][0]
    by_jurisdiction = run_query(
        """
        SELECT jurisdiction, COUNT(*)
        FROM documents
        WHERE jurisdiction IS NOT NULL
        GROUP BY jurisdiction
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
    high_risk = run_query(
        "SELECT COUNT(*) FROM documents WHERE risk_level = 'high'",
        fetch=True,
    )[0][0]

    by_region: dict[str, int] = {}
    for row in by_jurisdiction:
        region = get_region(row[0])
        by_region[region] = by_region.get(region, 0) + row[1]

    return {
        "total": total,
        "high_risk": high_risk,
        "by_jurisdiction": {row[0]: row[1] for row in by_jurisdiction},
        "by_region": by_region,
        "by_source": {row[0]: row[1] for row in by_source},
    }
