# api/routers/playbooks.py — Layer 2 playbooks & exposure packs
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ingestion.db import run_query
from ingestion.playbooks.loader import (
    get_exposure_pack,
    get_playbook,
    get_playbooks,
    list_exposure_pack_ids,
)
from ingestion.tagging import impacts_for_client_playbooks

router = APIRouter()


class PlaybookSummary(BaseModel):
    id: str
    name: str
    zones: List[str]
    sectors: List[str]
    jurisdictions: List[str]
    impact_summary: Optional[str] = None


class ExposurePackResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    jurisdictions: List[str] = []
    regions: List[str] = []
    default_playbooks: List[str] = []


class PlaybookImpact(BaseModel):
    playbook_id: str
    name: str
    level: str
    summary: Optional[str] = None


@router.get("/", response_model=List[PlaybookSummary])
def list_playbooks():
    """List all GCC regulatory playbooks."""
    return [
        PlaybookSummary(
            id=pb["id"],
            name=pb["name"],
            zones=pb.get("zones", []),
            sectors=pb.get("sectors", []),
            jurisdictions=pb.get("jurisdictions", []),
            impact_summary=pb.get("impact_summary"),
        )
        for pb in get_playbooks()
    ]


@router.get("/exposure-packs", response_model=List[ExposurePackResponse])
def list_exposure_packs():
    """List client exposure packs (e.g. dubai_hq = MENA + EU + US)."""
    return [get_exposure_pack(pid) for pid in list_exposure_pack_ids()]


@router.get("/exposure-packs/{pack_id}", response_model=ExposurePackResponse)
def get_exposure_pack_detail(pack_id: str):
    pack = get_exposure_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Exposure pack not found")
    return pack


@router.get("/impacts/{doc_id}", response_model=List[PlaybookImpact])
def get_document_playbook_impacts(
    doc_id: int,
    exposure_pack: Optional[str] = Query(
        None,
        description="Filter to playbooks in an exposure pack (e.g. dubai_hq)",
    ),
):
    """Playbook impact levels for a document, optionally filtered by exposure pack."""
    rows = run_query(
        "SELECT playbook_impacts FROM documents WHERE id = %s",
        (doc_id,),
        fetch=True,
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Document not found")

    impacts = rows[0][0] or {}
    if isinstance(impacts, str):
        import json

        impacts = json.loads(impacts)

    if exposure_pack:
        pack = get_exposure_pack(exposure_pack)
        if not pack:
            raise HTTPException(status_code=404, detail="Exposure pack not found")
        impacts = impacts_for_client_playbooks(impacts, pack.get("default_playbooks", []))

    return [
        PlaybookImpact(
            playbook_id=pid,
            name=data.get("name", pid),
            level=data.get("level", "low"),
            summary=data.get("summary"),
        )
        for pid, data in sorted(
            impacts.items(),
            key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x[1].get("level"), 3),
        )
    ]


@router.get("/{playbook_id}", response_model=PlaybookSummary)
def get_playbook_detail(playbook_id: str):
    pb = get_playbook(playbook_id)
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return PlaybookSummary(
        id=pb["id"],
        name=pb["name"],
        zones=pb.get("zones", []),
        sectors=pb.get("sectors", []),
        jurisdictions=pb.get("jurisdictions", []),
        impact_summary=pb.get("impact_summary"),
    )
