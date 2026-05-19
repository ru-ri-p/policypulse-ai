# Week 4 — Days 22–28 Checklist

## Day 22 — Explore zero-shot classification

```bash
source .venv/bin/activate
pip install transformers torch sentence-transformers scikit-learn pandas numpy accelerate
pip freeze > requirements.txt
python3 -m ml_pipeline.classify_explore
```

**Done when:** Top label is `regulation` for the sample EU AI Act text.

## Day 23 — Classify all documents

```bash
psql -U ppuser -d policypulse -f ingestion/migrations/002_ml_columns.sql
python3 -m ml_pipeline.run_classification
psql -U ppuser -d policypulse -c "SELECT title, risk_level, doc_type_classified FROM documents LIMIT 10;"
```

**Note:** 1,000+ documents takes hours on CPU. Run overnight or use `LIMIT` in SQL for a test batch.

## Days 24–28 — Summarisation + pipeline

```bash
python3 -m ml_pipeline.run_summarisation
```

New scrapes auto-classify and summarise via `MLPipeline` in Scrapy settings.

**Disable ML on a quick scrape** (saves time):

```bash
cd ingestion
scrapy crawl eu_ai_act -s ITEM_PIPELINES='{"spiders.pipelines.PostgresPipeline": 300}'
```
