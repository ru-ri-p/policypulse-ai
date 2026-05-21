# relevance/scorer.py
from ingestion.db import run_query
from ml_pipeline.embedder import DocumentEmbedder
from ml_pipeline.search import semantic_search

_embedder = None


def _get_embedder() -> DocumentEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = DocumentEmbedder()
    return _embedder


def build_profile_query(profile: dict) -> str:
    """Converts a user profile dict into a natural language query for semantic search."""
    parts = []
    if profile.get("industry"):
        parts.append(f"AI regulation for {profile['industry']} industry")
    if profile.get("jurisdictions"):
        jur = ", ".join(profile["jurisdictions"])
        parts.append(f"compliance requirements in {jur}")
    if profile.get("tech_used"):
        tech = ", ".join(profile["tech_used"])
        parts.append(f"rules about {tech}")
    if profile.get("company_size"):
        parts.append(f"obligations for {profile['company_size']} companies")
    return ". ".join(parts) or "AI policy and regulation"


def get_user_profile(user_id: int) -> dict | None:
    rows = run_query(
        """
        SELECT company_name, industry, company_size, jurisdictions, tech_used
        FROM user_profiles
        WHERE user_id = %s
        """,
        (user_id,),
        fetch=True,
    )
    if not rows:
        return None
    p = rows[0]
    return {
        "company_name": p[0],
        "industry": p[1],
        "company_size": p[2],
        "jurisdictions": list(p[3] or []),
        "tech_used": list(p[4] or []),
    }


def _apply_jurisdiction_boost(semantic_score: float, jurisdiction: str | None, profile: dict) -> float:
    boost = 0.0
    if jurisdiction and jurisdiction in (profile.get("jurisdictions") or []):
        boost += 0.15
    return min(float(semantic_score) + boost, 1.0)


def score_document_for_user(user_id: int, document_id: int) -> float | None:
    """Score a single document for a user (0–1). Returns None if profile or doc missing."""
    profile = get_user_profile(user_id)
    if not profile:
        return None

    rows = run_query(
        "SELECT title, jurisdiction, embedding IS NOT NULL FROM documents WHERE id = %s",
        (document_id,),
        fetch=True,
    )
    if not rows:
        return None

    title, jurisdiction, has_embedding = rows[0]
    if not has_embedding:
        return 0.0

    query = build_profile_query(profile)
    semantic_results = semantic_search(query, limit=100)
    scores_by_id = {r[0]: float(r[3]) for r in semantic_results}

    if document_id in scores_by_id:
        return round(_apply_jurisdiction_boost(scores_by_id[document_id], jurisdiction, profile), 3)

    # Direct embedding similarity if not in top-N search results
    doc_rows = run_query(
        "SELECT title, content FROM documents WHERE id = %s",
        (document_id,),
        fetch=True,
    )
    if not doc_rows or not doc_rows[0][1]:
        return 0.0

    doc_title, content = doc_rows[0]
    query_vec = _get_embedder().embed_text(query)
    doc_vec = _get_embedder().embed_text(f"{doc_title}. {content}")

    import numpy as np

    sim = float(np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec) + 1e-9))
    return round(_apply_jurisdiction_boost(sim, jurisdiction, profile), 3)


def score_documents_for_user(user_id: int, limit: int = 50) -> list:
    """Returns a personalised list of documents ranked by relevance for this user."""
    profile = get_user_profile(user_id)
    if not profile:
        return []

    query = build_profile_query(profile)
    semantic_results = semantic_search(query, limit=limit)

    scored = []
    for doc_id, title, jurisdiction, semantic_score in semantic_results:
        final_score = _apply_jurisdiction_boost(semantic_score, jurisdiction, profile)
        scored.append(
            {
                "doc_id": doc_id,
                "title": title,
                "jurisdiction": jurisdiction,
                "score": round(final_score, 3),
            }
        )

    return sorted(scored, key=lambda x: x["score"], reverse=True)
