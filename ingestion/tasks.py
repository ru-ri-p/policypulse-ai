# ingestion/tasks.py
import os
import subprocess

from infra.celery_app import app
from infra.logger import get_logger

log = get_logger("ingestion.tasks")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INGESTION_DIR = os.path.join(PROJECT_ROOT, "ingestion")

MENA_SPIDER_NAMES = (
    "uae_legislation",
    "dfsa_rulebook",
    "difc_laws",
    "adgm_fsra",
    "sdaia_saudi",
    "uae_ai_office",
    "digital_dubai",
)


def _run_spider_subprocess(spider_name: str) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_ROOT
    log.info("Starting spider: %s", spider_name)

    result = subprocess.run(
        ["scrapy", "crawl", spider_name],
        cwd=INGESTION_DIR,
        capture_output=True,
        text=True,
        timeout=900,
        env=env,
    )

    if result.returncode != 0:
        log.error("Spider %s stderr: %s", spider_name, result.stderr[-2000:])
        raise RuntimeError(f"Spider {spider_name} failed: {result.stderr[-500:]}")

    log.info("Spider %s completed", spider_name)
    return {"status": "ok", "spider": spider_name}


@app.task(bind=True, max_retries=1)
def run_all_mena_spiders(self):
    """Run all MENA law-focused spiders sequentially, then retag."""
    results = []
    for name in MENA_SPIDER_NAMES:
        try:
            results.append(_run_spider_subprocess(name))
        except Exception as exc:
            log.error("MENA spider %s failed: %s", name, exc)
            results.append({"status": "error", "spider": name, "error": str(exc)})
    retag_all_documents()
    return {"spiders": results, "retag": "ok"}


@app.task
def retag_all_documents(limit: int | None = None):
    """Backfill zones, sectors, and playbook impacts."""
    from ingestion.retag_documents import retag_all

    retag_all(limit=limit)
    return {"status": "ok"}


@app.task(bind=True, max_retries=3)
def run_spider(self, spider_name: str):
    """Runs a Scrapy spider by name (Celery Beat / manual)."""
    try:
        return _run_spider_subprocess(spider_name)
    except Exception as exc:
        log.warning("Spider %s failed, scheduling retry: %s", spider_name, exc)
        raise self.retry(exc=exc, countdown=60) from exc


@app.task(bind=True, max_retries=2)
def process_document(self, document_id: int):
    """Run classifier, summariser, and embedder on one document."""
    try:
        from ml_pipeline.processor import DocumentProcessor

        log.info("ML processing document %s", document_id)
        return DocumentProcessor().process_document(document_id)
    except Exception as exc:
        log.warning("ML processing failed for %s: %s", document_id, exc)
        raise self.retry(exc=exc, countdown=120)


@app.task
def process_pending_documents(limit: int = 50):
    """Batch ML processing for documents missing embeddings or summaries."""
    from ml_pipeline.processor import DocumentProcessor

    results = DocumentProcessor().process_pending(limit=limit)
    log.info("Processed %s pending documents", len(results))
    return {"processed": len(results)}


@app.task(bind=True, max_retries=2)
def generate_document_digest(self, document_id: int):
    """Generate LLM compliance digest for one document (skips if cache valid)."""
    try:
        from digests.run_digests import generate_digest_for_document

        log.info("Generating digest for document %s", document_id)
        return generate_digest_for_document(document_id)
    except Exception as exc:
        log.warning("Digest generation failed for %s: %s", document_id, exc)
        raise self.retry(exc=exc, countdown=90)


@app.task
def generate_pending_digests(limit: int = 25):
    """Batch digest generation for documents missing or stale digests."""
    from digests.run_digests import run_batch

    count = run_batch(limit=limit)
    log.info("Generated %s digests", count)
    return {"processed": count}


@app.task
def run_nightly_relevance_alerts(hours: int = 24):
    """Score recent policy changes and email users when highly relevant + immediate urgency."""
    from relevance.alert_service import run_nightly_alerts

    result = run_nightly_alerts(hours=hours)
    log.info("Nightly alerts complete: %s", result)
    return result
