# Week 2 — Days 11–14 Checklist

## Day 11 — Data cleaning

```bash
python3 -m ingestion.cleaner
```

**Done when:** Prints cleaned text without URLs or extra whitespace.

Cleaning also runs automatically in the Scrapy `PostgresPipeline` before save.

## Day 12 — Change detection

```bash
python3 -c "from ingestion.change_detector import check_and_save_version; print('OK')"
```

**Done when:** Imports without errors. Full tests come in Week 3.

## Day 13 — NIST spider

```bash
./scripts/run_spider.sh nist_airc
```

**Done when:** NIST documents appear in `documents` for source `NIST AI Resource Center`.

## Day 14 — README + Git

```bash
git add .
git status
git commit -m "Phase 1 Week 2: Three spiders, DB pipeline, change detector"
git push
```

**Done when:** README is on GitHub and commit is pushed.
