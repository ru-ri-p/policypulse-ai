# digests/run_digests.py
import argparse

from digests.generator import generate_digest
from ingestion.db import run_query
from infra.logger import get_logger

log = get_logger("digests.run_digests")

BATCH_SIZE = 25


def save_digest(document_id: int, digest: dict, content_hash: str) -> None:
    run_query(
        """
        UPDATE documents
        SET digest_what_changed = %s,
            digest_who_affected = %s,
            digest_what_to_do = %s,
            digest_urgency = %s,
            digest_key_deadline = %s,
            digest_content_hash = %s,
            digest_generated_at = NOW()
        WHERE id = %s
        """,
        (
            digest.get("what_changed"),
            digest.get("who_is_affected"),
            digest.get("what_to_do"),
            digest.get("urgency"),
            digest.get("key_deadline"),
            content_hash,
            document_id,
        ),
    )


def documents_needing_digest(limit: int | None = None):
    """Documents with no digest or content changed since last digest."""
    sql = """
        SELECT id, title, content, content_hash
        FROM documents
        WHERE content IS NOT NULL
          AND (
                digest_what_changed IS NULL
                OR digest_content_hash IS DISTINCT FROM content_hash
              )
        ORDER BY scraped_at DESC NULLS LAST
    """
    params = None
    if limit is not None:
        sql += " LIMIT %s"
        params = (limit,)
    return run_query(sql, params, fetch=True)


def run_batch(limit: int | None = None, force: bool = False) -> int:
    """
    Generate digests for documents that need them.
    Skips cached rows unless force=True.
    """
    if force:
        sql = """
            SELECT id, title, content, content_hash
            FROM documents
            WHERE content IS NOT NULL
            ORDER BY id
        """
        params = None
        if limit:
            sql += " LIMIT %s"
            params = (limit,)
        docs = run_query(sql, params, fetch=True)
    else:
        docs = documents_needing_digest(limit)

    log.info("Generating digests for %s documents...", len(docs))
    count = 0

    for doc_id, title, content, content_hash in docs:
        digest = generate_digest(title or "", content or "")
        save_digest(doc_id, digest, content_hash)
        log.info("Digest saved for document %s: %s", doc_id, (title or "")[:50])
        count += 1

    log.info("Digest batch complete. Processed %s documents.", count)
    return count


def generate_digest_for_document(document_id: int) -> dict:
    """Generate and persist digest for a single document."""
    rows = run_query(
        "SELECT id, title, content, content_hash FROM documents WHERE id = %s",
        (document_id,),
        fetch=True,
    )
    if not rows:
        return {"status": "not_found", "document_id": document_id}

    doc_id, title, content, content_hash = rows[0]
    if not content:
        return {"status": "empty", "document_id": document_id}

    digest = generate_digest(title, content)
    save_digest(doc_id, digest, content_hash)
    return {"status": "ok", "document_id": doc_id, "digest": digest}


def main():
    parser = argparse.ArgumentParser(description="Batch-generate policy digests")
    parser.add_argument("--limit", type=int, default=None, help="Max documents this run")
    parser.add_argument("--force", action="store_true", help="Regenerate even if cached")
    parser.add_argument("--id", type=int, default=None, help="Single document id")
    args = parser.parse_args()

    if args.id:
        print(generate_digest_for_document(args.id))
    else:
        run_batch(limit=args.limit, force=args.force)


if __name__ == "__main__":
    main()
