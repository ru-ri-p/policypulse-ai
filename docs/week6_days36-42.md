# Week 6 — Days 36–42

## Diff engine smoke test

```bash
python3 -c "
from ml_pipeline.diff_engine import compute_text_diff
d = compute_text_diff('Old rule. Ban X.', 'Old rule. Ban X and Y. New obligation.')
print(d)
"
```

## Migration

```bash
psql -U ppuser -d policypulse -f ingestion/migrations/004_change_tracking.sql
```

## Process one document (sync, no Celery)

```bash
python3 -m ml_pipeline.processor --id 1
```

## Process pending batch

```bash
python3 -m ml_pipeline.processor --pending --limit 5
```

## Celery ML task

```bash
brew services start redis
./scripts/celery_worker.sh
celery -A infra.celery_app call ingestion.tasks.process_document --args='[1]'
```

## Phase 2 tag (when ready)

```bash
git add .
git commit -m "Phase 2 Complete: ML pipeline, diffs, semantic search"
git tag v0.2.0
git push && git push --tags
```

## View flagged changes

```sql
SELECT title, change_percent, is_major_change, LEFT(change_summary, 120)
FROM documents
WHERE change_summary IS NOT NULL
ORDER BY scraped_at DESC
LIMIT 10;
```
