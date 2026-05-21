# relevance/alert_service.py
from ingestion.db import run_query
from infra.email_sender import is_email_configured, send_email
from infra.logger import get_logger
from relevance.scorer import score_document_for_user

log = get_logger("relevance.alert_service")

RELEVANCE_THRESHOLD = 0.7
URGENCY_IMMEDIATE = "immediate"


def get_documents_changed_recently(hours: int = 24) -> list:
    """Documents scraped or materially updated in the last N hours."""
    return run_query(
        """
        SELECT id, title, jurisdiction, digest_urgency, url,
               COALESCE(change_summary, '') AS change_summary
        FROM documents
        WHERE scraped_at >= NOW() - make_interval(hours => %s)
        ORDER BY scraped_at DESC
        """,
        (hours,),
        fetch=True,
    )


def get_users_with_profiles() -> list:
    return run_query(
        """
        SELECT u.id, u.email
        FROM users u
        INNER JOIN user_profiles p ON p.user_id = u.id
        """,
        fetch=True,
    )


def alert_already_sent(user_id: int, document_id: int) -> bool:
    rows = run_query(
        """
        SELECT 1 FROM alerts
        WHERE user_id = %s AND document_id = %s AND sent_at IS NOT NULL
        """,
        (user_id, document_id),
        fetch=True,
    )
    return bool(rows)


def record_alert(user_id: int, document_id: int, relevance_score: float, sent: bool) -> None:
    run_query(
        """
        INSERT INTO alerts (user_id, document_id, relevance_score, sent_at)
        VALUES (%s, %s, %s, CASE WHEN %s THEN NOW() ELSE NULL END)
        ON CONFLICT (user_id, document_id) DO UPDATE
            SET relevance_score = EXCLUDED.relevance_score,
                sent_at = CASE WHEN %s THEN NOW() ELSE alerts.sent_at END
        """,
        (user_id, document_id, relevance_score, sent, sent),
    )


def build_alert_email_body(title: str, url: str, score: float, urgency: str | None, change_summary: str) -> str:
    lines = [
        "PolicyPulse AI — Policy alert",
        "",
        f"Document: {title}",
        f"Relevance score: {score:.2f}",
        f"Urgency: {urgency or 'unknown'}",
        "",
    ]
    if change_summary:
        lines.extend(["What changed:", change_summary[:500], ""])
    lines.extend([f"Read more: {url}", "", "— PolicyPulse AI"])
    return "\n".join(lines)


def process_alerts_for_user(user_id: int, email: str, hours: int = 24) -> dict:
    """Score recent documents for one user and send qualifying alerts."""
    sent_count = 0
    checked = 0

    for doc_id, title, jurisdiction, urgency, url, change_summary in get_documents_changed_recently(hours):
        checked += 1
        score = score_document_for_user(user_id, doc_id)
        if score is None:
            continue

        record_alert(user_id, doc_id, score, sent=False)

        if score <= RELEVANCE_THRESHOLD:
            continue
        if (urgency or "").lower() != URGENCY_IMMEDIATE:
            continue
        if alert_already_sent(user_id, doc_id):
            continue

        body = build_alert_email_body(title, url, score, urgency, change_summary)
        subject = f"[PolicyPulse] High-priority policy update: {title[:60]}"
        if is_email_configured():
            if send_email(email, subject, body):
                record_alert(user_id, doc_id, score, sent=True)
                sent_count += 1
        else:
            log.info(
                "Alert qualified (no SMTP): user=%s doc=%s score=%s urgency=%s",
                user_id,
                doc_id,
                score,
                urgency,
            )
            record_alert(user_id, doc_id, score, sent=True)

    return {"user_id": user_id, "checked": checked, "sent": sent_count}


def run_nightly_alerts(hours: int = 24) -> dict:
    """Run alert pipeline for all users with profiles."""
    users = get_users_with_profiles()
    log.info("Running alerts for %s users", len(users))
    total_sent = 0
    for user_id, email in users:
        result = process_alerts_for_user(user_id, email, hours=hours)
        total_sent += result["sent"]
    return {"users": len(users), "alerts_sent": total_sent}
