# PolicyPulse AI

Track AI policy documents from EU and US sources. Scrapes policy text, stores it in PostgreSQL with pgvector, and will add embeddings, relevance scoring, and digests in later phases.

## Project structure

| Path | Purpose |
|------|---------|
| `ingestion/schema.sql` | Database tables: `sources`, `documents`, `document_versions` |
| `ingestion/db.py` | Postgres connection helpers (`get_connection`, `run_query`) |
| `ingestion/seed_sources.py` | Seeds the three policy sources |
| `ingestion/cleaner.py` | Text cleaning (HTML entities, URLs, whitespace) |
| `ingestion/change_detector.py` | Detects content changes and archives old versions |
| `ingestion/inspect_documents.py` | Quick CLI summary of scraped documents |
| `ingestion/spiders/` | Scrapy project (settings, pipelines, spiders) |
| `ingestion/spiders/spiders/eu_ai_act.py` | EU AI Act Monitor spider |
| `ingestion/spiders/spiders/federal_register.py` | US Federal Register API spider |
| `ingestion/spiders/spiders/nist_airc.py` | NIST AI Resource Center spider |
| `notebooks/scraping_basics.py` | Day 8: requests + BeautifulSoup tutorial |
| `scripts/run_spider.sh` | Run any spider from the project root |
| `test_db.py` | Verify Postgres connection via `.env` |

## Setup

```bash
cd ~/projects/policypulse-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` (see course guide) and apply schema:

```bash
psql -U ppuser -d policypulse -f ingestion/schema.sql
python3 -m ingestion.seed_sources
```

## Run spiders

```bash
source .venv/bin/activate
./scripts/run_spider.sh eu_ai_act
./scripts/run_spider.sh federal_register
./scripts/run_spider.sh nist_airc
python3 -m ingestion.inspect_documents
```

Or from `ingestion/`:

```bash
cd ingestion
scrapy crawl eu_ai_act
```

## Utilities

```bash
python3 -m ingestion.cleaner
python3 test_db.py
```

## Scheduling (Week 3)

```bash
brew install redis
brew services start redis
redis-cli ping   # PONG

./scripts/celery_worker.sh   # terminal 1
./scripts/celery_beat.sh     # terminal 2
```

Monitor tasks: `celery -A infra.celery_app flower` (http://localhost:5555)

## Stats

```bash
python3 -m ingestion.stats
```

## Machine learning (Week 4)

```bash
python3 -m ml_pipeline.classify_explore          # Day 22 demo
python3 -m ml_pipeline.run_classification        # classify all (slow on CPU)
python3 -m ml_pipeline.run_summarisation         # summarise all (slow on CPU)
```

Apply ML columns: `psql -U ppuser -d policypulse -f ingestion/migrations/002_ml_columns.sql`

## Semantic search (Week 5)

```bash
python3 -m notebooks.embeddings_intro
python3 -m ml_pipeline.embedder --limit 50    # quick test
python3 -m ml_pipeline.embedder               # all documents (slow)
python3 -m ml_pipeline.search
```

## Change detection + full ML processor (Week 6)

```bash
psql -U ppuser -d policypulse -f ingestion/migrations/004_change_tracking.sql
python3 -m ml_pipeline.processor --pending --limit 5   # sync batch (slow)
```

After scrapes, Celery queues `process_document` per doc (requires Redis + worker).
Phase 2 tag: `git tag v0.2.0` when ready.

## REST API (Phase 3)

```bash
psql -U ppuser -d policypulse -f ingestion/migrations/005_api_auth.sql
# Add SECRET_KEY to .env (see .env.example)
./scripts/run_api.sh
```

Interactive docs: http://localhost:8000/docs

## LLM digests (Phase 4)

```bash
psql -U ppuser -d policypulse -f ingestion/migrations/006_digests.sql
# OPENAI_API_KEY in .env
python3 -m digests.run_digests --limit 3
```

API: `GET /documents/{id}/digest`

## Phase 1 progress

- Week 1: Environment, schema, source seeding
- Week 2: Scrapy spiders, cleaning pipeline, change detection
- Week 3: Celery scheduling, logging, 100+ documents, stats report
