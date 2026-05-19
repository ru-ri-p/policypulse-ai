# Phase 4 — LLM Digests

## Setup

```bash
source .venv/bin/activate
pip install openai
pip freeze > requirements.txt

psql -U ppuser -d policypulse -f ingestion/migrations/006_digests.sql

# Add to .env (get key at https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-...
```

## Generate digests

```bash
# One document (test — ~$0.0001 with gpt-4o-mini)
python3 -m digests.run_digests --id 1

# Small batch
python3 -m digests.run_digests --limit 3

# All documents missing or stale digests (costs $ — run when ready)
python3 -m digests.run_digests
```

Caching: skips rows where `digest_content_hash` matches current `content_hash`.

## API

```bash
./scripts/run_api.sh
```

- `GET /documents/{id}/digest` — structured digest only
- `GET /documents/{id}` — includes `digest` object when generated

## Celery

```bash
celery -A infra.celery_app call ingestion.tasks.generate_document_digest --args='[1]'
celery -A infra.celery_app call ingestion.tasks.generate_pending_digests --kwargs='{"limit": 5}'
```

Daily beat at 12:00 UTC: `generate_pending_digests` (50 docs).

## Milestone

```bash
git tag v0.4.0
```
