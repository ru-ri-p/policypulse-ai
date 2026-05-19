# ingestion/change_detector.py
import hashlib

from ingestion.db import run_query
from ml_pipeline.diff_engine import compute_text_diff, format_change_summary


def compute_hash(text: str) -> str:
    """Returns an MD5 hash of the given text."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def record_content_change(
    document_id: int,
    old_content: str,
    old_hash: str,
    new_content: str,
    new_hash: str,
) -> dict | None:
    """
    Archives the previous version, computes a diff, and flags the document.
    Assumes `documents.content` already holds new_content from the scraper upsert.
    """
    if not old_content or old_hash == new_hash:
        return None

    diff = compute_text_diff(old_content, new_content)
    summary = format_change_summary(diff)

    run_query(
        """
        INSERT INTO document_versions (document_id, content, content_hash)
        VALUES (%s, %s, %s)
        """,
        (document_id, old_content, old_hash),
    )

    run_query(
        """
        UPDATE documents
        SET change_percent = %s,
            is_major_change = %s,
            change_summary = %s,
            content_hash = %s
        WHERE id = %s
        """,
        (
            diff["change_percent"],
            diff["is_major_change"],
            summary,
            new_hash,
            document_id,
        ),
    )

    return diff


def check_and_save_version(document_id: int, new_content: str) -> bool:
    """Legacy helper: compares DB content to new_content, archives if different."""
    new_hash = compute_hash(new_content)

    result = run_query(
        "SELECT content_hash, content FROM documents WHERE id = %s",
        (document_id,),
        fetch=True,
    )

    if not result:
        return False

    old_hash, old_content = result[0]

    if old_hash == new_hash:
        return False

    record_content_change(document_id, old_content, old_hash, new_content, new_hash)

    run_query(
        """
        UPDATE documents
        SET content = %s, scraped_at = NOW(), ml_processed_at = NULL
        WHERE id = %s
        """,
        (new_content, document_id),
    )

    return True
