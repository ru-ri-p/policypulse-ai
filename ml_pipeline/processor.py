# ml_pipeline/processor.py — Week 6: unified ML pipeline
import argparse
import json

from ingestion.db import run_query
from infra.logger import get_logger

log = get_logger("ml_pipeline.processor")


class DocumentProcessor:
    """
    Runs classification, summarisation, embedding, and optional change handling
    for a single document.
    """

    def __init__(self):
        self._classifier = None
        self._summariser = None
        self._embedder = None

    def _classifier_instance(self):
        if self._classifier is None:
            from ml_pipeline.classifier import PolicyClassifier

            self._classifier = PolicyClassifier()
        return self._classifier

    def _summariser_instance(self):
        if self._summariser is None:
            from ml_pipeline.summariser import PolicySummariser

            self._summariser = PolicySummariser()
        return self._summariser

    def _embedder_instance(self):
        if self._embedder is None:
            from ml_pipeline.embedder import DocumentEmbedder

            self._embedder = DocumentEmbedder()
        return self._embedder

    def process_document(self, document_id: int) -> dict:
        rows = run_query(
            """
            SELECT id, title, content, url
            FROM documents
            WHERE id = %s
            """,
            (document_id,),
            fetch=True,
        )

        if not rows:
            log.warning("Document %s not found", document_id)
            return {"status": "not_found", "document_id": document_id}

        doc_id, title, content, url = rows[0]
        if not content:
            log.warning("Document %s has no content", document_id)
            return {"status": "empty", "document_id": document_id}

        log.info("Processing document %s: %s", doc_id, (title or "")[:60])

        classification = self._classifier_instance().classify_full(content, title or "")
        summary = self._summariser_instance().summarise(content)
        vector = self._embedder_instance().embed_text(f"{title}. {content}")
        vector_str = "[" + ",".join(str(v) for v in vector) + "]"

        run_query(
            """
            UPDATE documents
            SET doc_type_classified = %s,
                risk_level = %s,
                classification_score = %s,
                summary = %s,
                embedding = %s::vector,
                ml_processed_at = NOW()
            WHERE id = %s
            """,
            (
                classification["doc_type"],
                classification["risk_level"],
                classification["doc_type_confidence"],
                summary,
                vector_str,
                doc_id,
            ),
        )

        result = {
            "status": "ok",
            "document_id": doc_id,
            "url": url,
            "doc_type": classification["doc_type"],
            "risk_level": classification["risk_level"],
            "summary_length": len(summary),
        }
        log.info("Finished document %s: %s", doc_id, json.dumps(result))
        return result

    def process_pending(self, limit: int = 50) -> list:
        """Process documents missing ML fields or stale after content change."""
        rows = run_query(
            """
            SELECT id
            FROM documents
            WHERE content IS NOT NULL
              AND (
                    ml_processed_at IS NULL
                    OR embedding IS NULL
                    OR summary IS NULL
                    OR doc_type_classified IS NULL
              )
            ORDER BY scraped_at DESC NULLS LAST
            LIMIT %s
            """,
            (limit,),
            fetch=True,
        )

        results = []
        for (doc_id,) in rows:
            results.append(self.process_document(doc_id))
        return results


def main():
    parser = argparse.ArgumentParser(description="Run full ML pipeline on documents")
    parser.add_argument("--id", type=int, help="Single document id")
    parser.add_argument("--pending", action="store_true", help="Process pending batch")
    parser.add_argument("--limit", type=int, default=50, help="Batch size for --pending")
    args = parser.parse_args()

    processor = DocumentProcessor()

    if args.id:
        print(processor.process_document(args.id))
    elif args.pending:
        results = processor.process_pending(limit=args.limit)
        print(f"Processed {len(results)} documents")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
