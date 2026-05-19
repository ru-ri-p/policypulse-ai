# Week 1 — Day 6 Consolidation Checklist

~2 hours. Re-run everything from memory to lock in Week 1.

## 1. Environment

```bash
cd ~/projects/policypulse-ai
source .venv/bin/activate
python3 --version
psql --version
```

## 2. Database connection

```bash
python3 test_db.py
```

Expected: `Connected to: PostgreSQL 16.x ...`

## 3. Schema (only if setting up a fresh DB)

```bash
psql -U ppuser -d policypulse -f ingestion/schema.sql
psql -U ppuser -d policypulse -c "\dt"
```

## 4. Seed sources

```bash
python3 -m ingestion.seed_sources
psql -U ppuser -d policypulse -c "SELECT * FROM sources;"
```

Expected: **3 rows**

## 5. Python review

```bash
python3 notebooks/python_review.py
```

## 6. Re-read these files (open in your editor)

- `ingestion/schema.sql`
- `ingestion/db.py`
- `ingestion/seed_sources.py`
- `test_db.py`

## Done when

You can explain what `get_connection()`, `run_query()`, and `%s` placeholders do without looking at the code.
