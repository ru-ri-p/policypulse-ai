# api/routers/users.py
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from api.auth import get_current_user
from ingestion.db import run_query
from relevance.scorer import get_user_profile, score_documents_for_user

router = APIRouter()

ALLOWED_JURISDICTIONS = {"EU", "US", "UK"}
ALLOWED_SIZES = {"startup", "smb", "enterprise"}


class UserAccount(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime | None = None


class CompanyProfile(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    jurisdictions: List[str] = Field(default_factory=list)
    tech_used: List[str] = Field(default_factory=list)


class UserProfileResponse(UserAccount):
    company_profile: Optional[CompanyProfile] = None


class ProfileUpsertRequest(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = Field(None, description="startup | smb | enterprise")
    jurisdictions: List[str] = Field(default_factory=list, description="EU, US, UK")
    tech_used: List[str] = Field(default_factory=list, description="e.g. facial_recognition, generative_ai")


class FeedItem(BaseModel):
    doc_id: int
    title: str
    jurisdiction: Optional[str] = None
    score: float


@router.get("/profile", response_model=UserProfileResponse)
def get_profile(user: dict = Depends(get_current_user)):
    """Return account info and company profile if set."""
    profile = get_user_profile(user["id"])
    company = CompanyProfile(**profile) if profile else None
    return UserProfileResponse(
        id=user["id"],
        email=user["email"],
        created_at=user["created_at"],
        company_profile=company,
    )


@router.post("/profile", response_model=UserProfileResponse)
def upsert_profile(
    body: ProfileUpsertRequest,
    user: dict = Depends(get_current_user),
):
    """Create or update the authenticated user's company profile for relevance scoring."""
    jurisdictions = []
    for j in body.jurisdictions:
        code = j.strip().upper()
        if code not in ALLOWED_JURISDICTIONS:
            raise HTTPException(status_code=400, detail=f"Invalid jurisdiction: {j}")
        if code not in jurisdictions:
            jurisdictions.append(code)

    company_size = body.company_size.lower() if body.company_size else None
    if company_size and company_size not in ALLOWED_SIZES:
        raise HTTPException(
            status_code=400,
            detail=f"company_size must be one of: {', '.join(sorted(ALLOWED_SIZES))}",
        )

    tech_used = [t.strip() for t in body.tech_used if t.strip()]

    run_query(
        """
        INSERT INTO user_profiles (
            user_id, company_name, industry, company_size, jurisdictions, tech_used, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (user_id) DO UPDATE
            SET company_name = EXCLUDED.company_name,
                industry = EXCLUDED.industry,
                company_size = EXCLUDED.company_size,
                jurisdictions = EXCLUDED.jurisdictions,
                tech_used = EXCLUDED.tech_used,
                updated_at = NOW()
        """,
        (
            user["id"],
            body.company_name,
            body.industry,
            company_size,
            jurisdictions,
            tech_used,
        ),
    )

    return get_profile(user)


@router.get("/feed", response_model=List[FeedItem])
def get_personalized_feed(
    limit: int = 20,
    user: dict = Depends(get_current_user),
):
    """Personalised policy feed ranked by relevance to your company profile."""
    if not get_user_profile(user["id"]):
        raise HTTPException(
            status_code=400,
            detail="Complete your profile first via POST /user/profile",
        )

    scored = score_documents_for_user(user["id"], limit=min(limit, 50))
    return [FeedItem(**item) for item in scored]
