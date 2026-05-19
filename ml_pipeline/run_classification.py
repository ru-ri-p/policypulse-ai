# ml_pipeline/run_classification.py
from ml_pipeline.classifier import PolicyClassifier
from ingestion.db import run_query
from infra.logger import get_logger

log = get_logger("ml_pipeline.run_classification")

BATCH_SIZE = 50


def classify_all_documents():
    """Fetches unclassified documents in batches and classifies them."""
    classifier = PolicyClassifier()
    total = 0

    while True:
        docs = run_query(
            """
            SELECT id, title, content
            FROM documents
            WHERE doc_type_classified IS NULL
            LIMIT %s
            """,
            (BATCH_SIZE,),
            fetch=True,
        )

        if not docs:
            break

        log.info("Classifying %s documents...", len(docs))

        for doc_id, title, content in docs:
            if not content:
                continue

            result = classifier.classify_full(content, title or "")

            run_query(
                """
                UPDATE documents
                SET doc_type_classified = %s,
                    risk_level = %s,
                    classification_score = %s
                WHERE id = %s
                """,
                (
                    result["doc_type"],
                    result["risk_level"],
                    result["doc_type_confidence"],
                    doc_id,
                ),
            )
            log.info(
                "Classified doc %s: %s / %s",
                doc_id,
                result["doc_type"],
                result["risk_level"],
            )
            total += 1

    log.info("Classification complete. Processed %s documents.", total)
    return total


if __name__ == "__main__":
    classify_all_documents()
