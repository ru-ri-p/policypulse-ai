# Week 5 — Days 29–30

## Day 29 — Embeddings intro

```bash
source .venv/bin/activate
python3 -m notebooks.embeddings_intro
```

**Done when:** EU sentences ~0.8+, cake sentence ~0.3 or lower.

## Day 30 — Store embeddings + search

```bash
# Quick test (no long run)
python3 -m ml_pipeline.embedder --limit 50
psql -U ppuser -d policypulse -f ingestion/migrations/003_vector_index.sql
python3 -m ml_pipeline.search

# Full corpus (run when machine is idle)
python3 -m ml_pipeline.embedder
```

**Done when:** `semantic_search()` returns relevant EU/US policy titles for the facial recognition query.
