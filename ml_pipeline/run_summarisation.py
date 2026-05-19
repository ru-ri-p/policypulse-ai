# ml_pipeline/run_summarisation.py
from ingestion.db import run_query
from infra.logger import get_logger
from ml_pipeline.summariser import PolicySummariser

log = get_logger("ml_pipeline.run_summarisation")

BATCH_SIZE = 20


def summarise_all_documents():
    """Summarise documents that do not have a summary yet."""
    summariser = PolicySummariser()
    total = 0

    while True:
        docs = run_query(
            """
            SELECT id, content
            FROM documents
            WHERE summary IS NULL AND content IS NOT NULL
            LIMIT %s
            """,
            (BATCH_SIZE,),
            fetch=True,
        )

        if not docs:
            break

        log.info("Summarising %s documents...", len(docs))

        for doc_id, content in docs:
            if not content or len(content.split()) < 50:
                run_query(
                    "UPDATE documents SET summary = %s WHERE id = %s",
                    (content or "", doc_id),
                )
                continue

            summary = summariser.summarise(content)
            run_query(
                "UPDATE documents SET summary = %s WHERE id = %s",
                (summary, doc_id),
            )
            log.info("Summarised doc %s (%s chars)", doc_id, len(summary))
            total += 1

    log.info("Summarisation complete. Processed %s documents.", total)
    return total


if __name__ == "__main__":
    summarise_all_documents()
