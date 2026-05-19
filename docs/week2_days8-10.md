# Week 2 — Days 8–10 Checklist

## Day 8 — HTTP + BeautifulSoup

```bash
cd ~/projects/policypulse-ai
source .venv/bin/activate
python3 notebooks/scraping_basics.py
```

**Done when:** Script prints 3 quotes from quotes.toscrape.com.

## Day 9 — EU AI Act Scrapy spider

```bash
chmod +x scripts/run_spider.sh
./scripts/run_spider.sh eu_ai_act
psql -U ppuser -d policypulse -c "SELECT COUNT(*) FROM documents;"
```

**Done when:** At least 5 documents in `documents` (EU source).

## Day 10 — More sources + inspect data

Federal Register blocks raw HTML scraping; we use their **public API** instead.

```bash
./scripts/run_spider.sh federal_register
./scripts/run_spider.sh nist_airc
python3 -m ingestion.inspect_documents
```

**Done when:** Documents exist for multiple sources and `inspect_documents` looks sensible.

## Run all Week 2 spiders

```bash
./scripts/run_spider.sh eu_ai_act
./scripts/run_spider.sh federal_register
./scripts/run_spider.sh nist_airc
```
