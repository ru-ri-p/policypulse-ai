# Week 3 — Days 15–21 Checklist

## Day 15 — Celery + Redis

```bash
brew install redis
brew services start redis
redis-cli ping   # PONG

source .venv/bin/activate
pip install celery redis flower
pip freeze > requirements.txt

python3 -c "from infra.celery_app import app; print('celery OK')"
```

Run a spider task manually:

```bash
export PYTHONPATH=~/projects/policypulse-ai
cd ~/projects/policypulse-ai
source .venv/bin/activate
celery -A infra.celery_app worker --loglevel=info &
celery -A infra.celery_app call ingestion.tasks.run_spider --args='["eu_ai_act"]'
```

Or use helper scripts:

```bash
./scripts/celery_worker.sh    # terminal 1
./scripts/celery_beat.sh      # terminal 2 (scheduled runs)
```

## Day 16 — Logging

```bash
python3 -m infra.logger
ls logs/
```

## Days 17–20 — 100+ documents

```bash
./scripts/run_spider.sh eu_ai_act
./scripts/run_spider.sh federal_register
./scripts/run_spider.sh nist_airc
./scripts/run_spider.sh ico_uk
python3 -m ingestion.seed_sources   # adds ICO source if missing
python3 -m ingestion.stats
```

**Done when:** `Total documents: 100` or more.

## Day 21 — Milestone tag

```bash
git add .
git commit -m "Phase 1 Complete: 100+ documents, 3 spiders, scheduled ingestion"
git tag v0.1.0
git push && git push --tags
```
