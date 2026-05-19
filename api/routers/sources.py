# api/routers/sources.py
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ingestion.db import run_query

router = APIRouter()


class SourceResponse(BaseModel):
    id: int
    name: str
    url: str
    jurisdiction: Optional[str] = None
    document_count: int = 0


@router.get("/", response_model=List[SourceResponse])
def list_sources():
    """List all configured policy sources and document counts."""
    rows = run_query(
        """
        SELECT s.id, s.name, s.url, s.jurisdiction, COUNT(d.id)
        FROM sources s
        LEFT JOIN documents d ON d.source_id = s.id
        GROUP BY s.id, s.name, s.url, s.jurisdiction
        ORDER BY s.name
        """,
        fetch=True,
    )
    return [
        SourceResponse(
            id=r[0],
            name=r[1],
            url=r[2],
            jurisdiction=r[3],
            document_count=r[4],
        )
        for r in rows
    ]
