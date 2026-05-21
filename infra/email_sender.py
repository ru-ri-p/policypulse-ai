# infra/email_sender.py
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

from infra.logger import get_logger

load_dotenv()
log = get_logger("infra.email_sender")


def is_email_configured() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("EMAIL_FROM"))


def send_email(to_email: str, subject: str, body_text: str) -> bool:
    """
    Send email via SMTP. Configure in .env:
      SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASSWORD, EMAIL_FROM
    """
    if not is_email_configured():
        log.warning("SMTP not configured — skipping email to %s", to_email)
        return False

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    from_addr = os.getenv("EMAIL_FROM")

    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_text, "plain"))

    try:
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.starttls()
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, [to_email], msg.as_string())
        log.info("Email sent to %s: %s", to_email, subject)
        return True
    except Exception as exc:
        log.error("Failed to send email to %s: %s", to_email, exc)
        return False
