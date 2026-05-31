# api/routers/documents.py
import json
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ingestion.db import run_query

router = APIRouter()

UpdateStatus = Literal["new", "updated", "major_update"]


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
    first_scraped_at: Optional[str] = None
    scraped_at: Optional[str] = None
    published_at: Optional[str] = None
    update_status: UpdateStatus = "new"
    version_count: int = 0
    change_percent: Optional[float] = None
    is_major_change: Optional[bool] = None
    change_summary: Optional[str] = None
    zones: List[str] = []
    sectors: List[str] = []
    playbook_impacts: Dict[str, Any] = {}
    digest: Optional[DigestFields] = None


def _parse_impacts(raw) -> dict:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        return json.loads(raw)
    return {}


def _iso(dt) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def _compute_update_status(
    version_count: int,
    is_major_change: bool | None,
    change_summary: str | None,
    change_percent: float | None,
) -> UpdateStatus:
    if is_major_change:
        return "major_update"
    if version_count > 0 or change_summary or (change_percent and change_percent > 0):
        return "updated"
    return "new"


def _row_to_document(row) -> DocumentResponse:
    digest = None
    if row[17]:
        digest = DigestFields(
            what_changed=row[17],
            who_is_affected=row[18],
            what_to_do=row[19],
            urgency=row[20],
            key_deadline=row[21],
            generated_at=_iso(row[22]),
        )
    version_count = int(row[13] or 0)
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
        first_scraped_at=_iso(row[10]),
        scraped_at=_iso(row[11]),
        published_at=_iso(row[12]),
        version_count=version_count,
        update_status=_compute_update_status(
            version_count, row[8], row[9], row[7]
        ),
        zones=list(row[14] or []),
        sectors=list(row[15] or []),
        playbook_impacts=_parse_impacts(row[16]),
        digest=digest,
    )


_DOCUMENT_SELECT = """
    SELECT d.id, d.title, d.url, d.jurisdiction, d.doc_type_classified, d.risk_level, d.summary,
           d.change_percent, d.is_major_change, d.change_summary,
           d.first_scraped_at, d.scraped_at, d.published_at,
           (SELECT COUNT(*)::int FROM document_versions v WHERE v.document_id = d.id),
           d.zones, d.sectors, d.playbook_impacts,
           d.digest_what_changed, d.digest_who_affected, d.digest_what_to_do,
           d.digest_urgency, d.digest_key_deadline, d.digest_generated_at
"""


@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction: EU, US, UK, UAE, SA"),
    region: Optional[str] = Query(None, description="Filter by region: MENA, EU, US, UK"),
    zone: Optional[str] = Query(None, description="Filter by zone: DIFC, ADGM, MAINLAND, DMCC"),
    sector: Optional[str] = Query(None, description="Filter by sector: financial_services, fintech, ..."),
    risk_level: Optional[str] = Query(None, description="Filter by risk: high, medium, low"),
    q: Optional[str] = Query(None, description="Case-insensitive title/summary keyword"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List policy documents with optional filters."""
    from ingestion.regions import JURISDICTION_TO_REGION

    where_clauses = []
    params: list = []

    if jurisdiction:
        where_clauses.append("d.jurisdiction = %s")
        params.append(jurisdiction.upper())

    if region and not jurisdiction:
        region_jurisdictions = [
            k for k, v in JURISDICTION_TO_REGION.items() if v == region.upper()
        ]
        if region_jurisdictions:
            placeholders = ", ".join(["%s"] * len(region_jurisdictions))
            where_clauses.append(f"d.jurisdiction IN ({placeholders})")
            params.extend(region_jurisdictions)

    if zone:
        where_clauses.append("%s = ANY(d.zones)")
        params.append(zone.upper())

    if sector:
        where_clauses.append("%s = ANY(d.sectors)")
        params.append(sector.lower())

    if risk_level:
        where_clauses.append("d.risk_level = %s")
        params.append(risk_level.lower())

    if q:
        where_clauses.append(
            "(d.title ILIKE %s OR COALESCE(d.summary, '') ILIKE %s OR COALESCE(d.change_summary, '') ILIKE %s)"
        )
        pattern = f"%{q}%"
        params.extend([pattern, pattern, pattern])

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    params.extend([limit, offset])

    rows = run_query(
        f"""
        {_DOCUMENT_SELECT}
        FROM documents d
        {where_sql}
        ORDER BY d.published_at DESC NULLS LAST, d.scraped_at DESC NULLS LAST
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
        generated_at=_iso(r[5]),
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: int):
    """Get a single document by ID."""
    rows = run_query(
        f"{_DOCUMENT_SELECT} FROM documents d WHERE d.id = %s",
        (doc_id,),
        fetch=True,
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Document not found")
    return _row_to_document(rows[0])
