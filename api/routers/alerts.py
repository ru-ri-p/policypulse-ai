# api/routers/alerts.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.auth import get_current_user
from ingestion.db import run_query

router = APIRouter()

ALLOWED_JURISDICTIONS = {"EU", "US", "UK"}


class AlertSubscribeRequest(BaseModel):
    jurisdictions: List[str] = Field(
        ...,
        min_length=1,
        description="Jurisdictions to monitor, e.g. ['EU', 'US']",
    )


class AlertResponse(BaseModel):
    id: int
    jurisdictions: List[str]


@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def subscribe_alerts(
    body: AlertSubscribeRequest,
    user: dict = Depends(get_current_user),
):
    """Subscribe to policy alerts for one or more jurisdictions."""
    normalized = []
    for j in body.jurisdictions:
        code = j.strip().upper()
        if code not in ALLOWED_JURISDICTIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid jurisdiction: {j}. Use EU, US, or UK.",
            )
        if code not in normalized:
            normalized.append(code)

    rows = run_query(
        """
        INSERT INTO alert_subscriptions (user_id, jurisdictions)
        VALUES (%s, %s)
        RETURNING id, jurisdictions
        """,
        (user["id"], normalized),
        fetch=True,
    )
    return AlertResponse(id=rows[0][0], jurisdictions=rows[0][1])


@router.get("/", response_model=List[AlertResponse])
def list_alerts(user: dict = Depends(get_current_user)):
    """List the current user's alert subscriptions."""
    rows = run_query(
        """
        SELECT id, jurisdictions
        FROM alert_subscriptions
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user["id"],),
        fetch=True,
    )
    return [AlertResponse(id=r[0], jurisdictions=r[1]) for r in rows]
