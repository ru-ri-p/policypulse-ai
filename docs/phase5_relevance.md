# Phase 5 — Relevance + Alerts

## Migration

```bash
psql -U ppuser -d policypulse -f ingestion/migrations/007_user_profiles_relevance.sql
```

## API (Swagger — login as `ruri@example.com`)

1. **POST /user/profile** — company onboarding
```json
{
  "company_name": "Acme Health",
  "industry": "healthcare",
  "company_size": "smb",
  "jurisdictions": ["EU", "US"],
  "tech_used": ["facial_recognition", "generative_ai"]
}
```

2. **GET /user/feed** — ranked policy documents  
3. **GET /user/profile** — view profile

## Scoring (Python)

```bash
python3 -c "
from relevance.scorer import score_documents_for_user
print(score_documents_for_user(2, limit=10))
"
```

Requires documents with **embeddings** and a **user_profiles** row.

## Nightly alerts (Celery)

```bash
celery -A infra.celery_app call ingestion.tasks.run_nightly_relevance_alerts
```

Sends email when:
- Document changed in last 24h
- Relevance score > 0.7
- `digest_urgency` = `immediate`

Configure SMTP in `.env` or alerts are logged only.

## Milestone

```bash
git tag v0.5.0
```
