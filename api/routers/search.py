# api/routers/search.py
from typing import List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


class SearchResult(BaseModel):
    id: int
    title: str
    jurisdiction: str | None
    similarity: float


@router.get("/", response_model=List[SearchResult])
def search_documents(
    q: str = Query(..., min_length=2, description="Natural language search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Semantic search across policy documents with embeddings."""
    from ml_pipeline.search import semantic_search

    try:
        results = semantic_search(q, limit)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Search unavailable: {exc}. Embed documents first.",
        ) from exc

    return [
        SearchResult(
            id=r[0],
            title=r[1],
            jurisdiction=r[2],
            similarity=round(float(r[3]), 3),
        )
        for r in results
    ]
