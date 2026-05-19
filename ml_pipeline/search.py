# ml_pipeline/search.py
from ml_pipeline.embedder import DocumentEmbedder
from ingestion.db import get_connection

_embedder = None


def _get_embedder() -> DocumentEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = DocumentEmbedder()
    return _embedder


def semantic_search(query: str, limit: int = 10) -> list:
    """
    Finds the most semantically similar documents to a natural language query.
    Returns a list of (id, title, jurisdiction, similarity_score) tuples.
    """
    query_vector = _get_embedder().embed_text(query)
    vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, title, jurisdiction,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM documents
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (vector_str, vector_str, limit),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    results = semantic_search("facial recognition regulations in the European Union")
    for row in results:
        doc_id, title, jurisdiction, score = row
        print(f"[{score:.3f}] {jurisdiction}: {title[:80]}")
