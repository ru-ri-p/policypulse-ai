# api/routers/documents.py
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ingestion.db import run_query

router = APIRouter()


class DigestFields(BaseModel):
    what_changed: Optional[str] = None
    who_is_affected: Optional[str] = None
    what_to_do: Optional[str] = None
    urgency: Optional[str] = None
    key_deadline: Optional[str] = None
    generated_at: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    title: str
    url: str
    jurisdiction: Optional[str] = None
    doc_type: Optional[str] = None
    risk_level: Optional[str] = None
    summary: Optional[str] = None
    change_percent: Optional[float] = None
    is_major_change: Optional[bool] = None
    change_summary: Optional[str] = None
    digest: Optional[DigestFields] = None


def _row_to_document(row) -> DocumentResponse:
    digest = None
    if row[10]:
        digest = DigestFields(
            what_changed=row[10],
            who_is_affected=row[11],
            what_to_do=row[12],
            urgency=row[13],
            key_deadline=row[14],
            generated_at=row[15].isoformat() if row[15] else None,
        )
    return DocumentResponse(
        id=row[0],
        title=row[1],
        url=row[2],
        jurisdiction=row[3],
        doc_type=row[4],
        risk_level=row[5],
        summary=row[6],
        change_percent=row[7],
        is_major_change=row[8],
        change_summary=row[9],
        digest=digest,
    )


_DOCUMENT_SELECT = """
    SELECT id, title, url, jurisdiction, doc_type_classified, risk_level, summary,
           change_percent, is_major_change, change_summary,
           digest_what_changed, digest_who_affected, digest_what_to_do,
           digest_urgency, digest_key_deadline, digest_generated_at
"""


@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction: EU, US, UK"),
    risk_level: Optional[str] = Query(None, description="Filter by risk: high, medium, low"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List policy documents with optional filters."""
    where_clauses = []
    params: list = []

    if jurisdiction:
        where_clauses.append("jurisdiction = %s")
        params.append(jurisdiction.upper())

    if risk_level:
        where_clauses.append("risk_level = %s")
        params.append(risk_level.lower())

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    params.extend([limit, offset])

    rows = run_query(
        f"""
        {_DOCUMENT_SELECT}
        FROM documents
        {where_sql}
        ORDER BY scraped_at DESC NULLS LAST
        LIMIT %s OFFSET %s
        """,
        tuple(params),
        fetch=True,
    )

    return [_row_to_document(r) for r in rows]


@router.get("/{doc_id}/digest", response_model=DigestFields)
def get_document_digest(doc_id: int):
    """Get the structured compliance digest for a document."""
    rows = run_query(
        """
        SELECT digest_what_changed, digest_who_affected, digest_what_to_do,
               digest_urgency, digest_key_deadline, digest_generated_at
        FROM documents WHERE id = %s
        """,
        (doc_id,),
        fetch=True,
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Document not found")

    r = rows[0]
    if not r[0]:
        raise HTTPException(
            status_code=404,
            detail="Digest not generated yet. Run digests/run_digests.py or wait for Celery.",
        )

    return DigestFields(
        what_changed=r[0],
        who_is_affected=r[1],
        what_to_do=r[2],
        urgency=r[3],
        key_deadline=r[4],
        generated_at=r[5].isoformat() if r[5] else None,
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: int):
    """Get a single document by ID."""
    rows = run_query(
        f"{_DOCUMENT_SELECT} FROM documents WHERE id = %s",
        (doc_id,),
        fetch=True,
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Document not found")
    return _row_to_document(rows[0])
