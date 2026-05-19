# ml_pipeline/embedder.py
import argparse

from sentence_transformers import SentenceTransformer

from ingestion.db import get_connection, run_query
from infra.logger import get_logger

log = get_logger("ml_pipeline.embedder")


class DocumentEmbedder:
    def __init__(self):
        log.info("Loading embedding model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        log.info("Embedding model loaded.")

    def embed_text(self, text: str) -> list:
        """Converts text to a 384-dimensional vector."""
        truncated = " ".join(text.split()[:500])
        vector = self.model.encode(truncated)
        return vector.tolist()

    def _store_embedding(self, doc_id: int, vector: list) -> None:
        vector_str = "[" + ",".join(str(v) for v in vector) + "]"
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE documents SET embedding = %s::vector WHERE id = %s",
                (vector_str, doc_id),
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def embed_all_documents(self, limit: int | None = None):
        """Generates and stores embeddings for all unembedded documents."""
        sql = "SELECT id, title, content FROM documents WHERE embedding IS NULL"
        params = None
        if limit is not None:
            sql += " LIMIT %s"
            params = (limit,)

        docs = run_query(sql, params, fetch=True)
        log.info("Embedding %s documents...", len(docs))

        for doc_id, title, content in docs:
            if not content:
                continue

            combined = f"{title}. {content}"
            vector = self.embed_text(combined)
            self._store_embedding(doc_id, vector)

            if doc_id % 10 == 0:
                log.info("Embedded document id %s...", doc_id)

        log.info("Embedding batch complete.")


def main():
    parser = argparse.ArgumentParser(description="Embed policy documents for semantic search")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max documents to embed this run (omit for all remaining)",
    )
    args = parser.parse_args()
    DocumentEmbedder().embed_all_documents(limit=args.limit)


if __name__ == "__main__":
    main()
