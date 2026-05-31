# ingestion/spiders/pipelines.py
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ingestion.cleaner import clean_text
from ingestion.date_extract import infer_document_published_at
from ingestion.db import run_query
from ingestion.regions import get_region
from ingestion.tagging import tag_document


class PostgresPipeline:
    """Save each scraped PolicyDocumentItem to Postgres."""

    def process_item(self, item, spider):
        content = clean_text(item.get("content") or "")
        printable_ratio = sum(c.isprintable() or c in "\n\r\t" for c in content) / max(
            len(content), 1
        )
        if printable_ratio < 0.85:
            spider.logger.warning("Skipping non-text content: %s", item.get("url"))
            return item
        if len(content) < 100:
            spider.logger.warning("Skipping thin document: %s", item.get("url"))
            return item

        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()

        result = run_query(
            "SELECT id FROM sources WHERE name = %s",
            (item["source_name"],),
            fetch=True,
        )
        source_id = result[0][0] if result else None

        existing = run_query(
            "SELECT id, content, content_hash FROM documents WHERE url = %s",
            (item["url"],),
            fetch=True,
        )

        zones, sectors, impacts = tag_document(
            item["title"] or "",
            item["url"] or "",
            content,
            item["source_name"] or "",
            item.get("jurisdiction"),
        )
        region = get_region(item.get("jurisdiction"))
        impacts_json = json.dumps(impacts)
        published_at = infer_document_published_at(
            item["title"] or "",
            item["url"] or "",
            content,
            item.get("source_name") or "",
            item.get("published_at"),
        )

        run_query(
            """
            INSERT INTO documents (
                source_id, title, url, content, doc_type, jurisdiction,
                content_hash, zones, sectors, playbook_impacts, region,
                first_scraped_at, published_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, NOW(), %s)
            ON CONFLICT (url) DO UPDATE
                SET content = EXCLUDED.content,
                    content_hash = EXCLUDED.content_hash,
                    scraped_at = NOW(),
                    ml_processed_at = NULL,
                    zones = EXCLUDED.zones,
                    sectors = EXCLUDED.sectors,
                    playbook_impacts = EXCLUDED.playbook_impacts,
                    region = EXCLUDED.region,
                    published_at = COALESCE(EXCLUDED.published_at, documents.published_at)
            """,
            (
                source_id,
                item["title"],
                item["url"],
                content,
                item.get("doc_type"),
                item.get("jurisdiction"),
                content_hash,
                zones,
                sectors,
                impacts_json,
                region,
                published_at,
            ),
        )

        doc_row = run_query(
            "SELECT id FROM documents WHERE url = %s",
            (item["url"],),
            fetch=True,
        )
        doc_id = doc_row[0][0] if doc_row else None

        content_changed = False
        if existing and doc_id:
            old_id, old_content, old_hash = existing[0]
            if old_hash and old_hash != content_hash and old_content:
                content_changed = True
                from ingestion.change_detector import record_content_change

                diff = record_content_change(
                    doc_id, old_content, old_hash, content, content_hash
                )
                if diff and diff.get("is_major_change"):
                    spider.logger.warning(
                        "Major change (%.1f%%) on document %s",
                        diff["change_percent"],
                        doc_id,
                    )
        elif not existing:
            content_changed = True

        item["content"] = content
        item["db_id"] = doc_id
        spider.logger.info("Saved: %s", (item["title"] or "")[:60])

        if doc_id:
            _enqueue_ml_processing(doc_id, spider)
            if content_changed:
                _enqueue_digest_generation(doc_id, spider)

        return item


def _enqueue_digest_generation(document_id: int, spider):
    """Queue LLM digest when content is new or changed."""
    try:
        from ingestion.tasks import generate_document_digest

        generate_document_digest.delay(document_id)
        spider.logger.info("Queued digest generation for document %s", document_id)
    except Exception as exc:
        spider.logger.debug(
            "Digest queue skipped for doc %s (%s). Run: python3 -m digests.run_digests --id %s",
            document_id,
            exc,
            document_id,
        )


def _enqueue_ml_processing(document_id: int, spider):
    """Queue full ML pipeline via Celery, or skip quietly if broker is down."""
    try:
        from ingestion.tasks import process_document

        process_document.delay(document_id)
        spider.logger.info("Queued ML processing for document %s", document_id)
    except Exception as exc:
        spider.logger.debug(
            "Celery unavailable for doc %s (%s). Run: python3 -m ml_pipeline.processor --id %s",
            document_id,
            exc,
            document_id,
        )


class MLPipeline:
    """
    Classify and summarise new documents after they are saved.
    Models load once per spider run (lazy singleton).
    """

    _classifier = None
    _summariser = None

    @classmethod
    def _get_classifier(cls):
        if cls._classifier is None:
            from ml_pipeline.classifier import PolicyClassifier

            cls._classifier = PolicyClassifier()
        return cls._classifier

    @classmethod
    def _get_summariser(cls):
        if cls._summariser is None:
            from ml_pipeline.summariser import PolicySummariser

            cls._summariser = PolicySummariser()
        return cls._summariser

    def process_item(self, item, spider):
        content = item.get("content") or ""
        title = item.get("title") or ""
        url = item.get("url")

        if not content or not url:
            return item

        try:
            classification = self._get_classifier().classify_full(content, title)
            summary = self._get_summariser().summarise(content)

            run_query(
                """
                UPDATE documents
                SET doc_type_classified = %s,
                    risk_level = %s,
                    classification_score = %s,
                    summary = %s
                WHERE url = %s
                """,
                (
                    classification["doc_type"],
                    classification["risk_level"],
                    classification["doc_type_confidence"],
                    summary,
                    url,
                ),
            )
            spider.logger.info(
                "ML processed: %s | %s / %s",
                (title or "")[:40],
                classification["doc_type"],
                classification["risk_level"],
            )
        except Exception as exc:
            spider.logger.error("ML pipeline failed for %s: %s", url, exc)

        return item
