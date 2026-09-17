"""Minimal SMTP mailer configured from environment variables.

Required for sending:
    SMTP_HOST, SMTP_PORT (587 STARTTLS or 465 SSL), SMTP_USER, SMTP_PASSWORD
Optional:
    SMTP_FROM            - sender address (defaults to SMTP_USER)
    ADMIN_NOTIFY_EMAIL   - where admin notifications go (defaults to SMTP_FROM)

For Gmail use SMTP_HOST=smtp.gmail.com, SMTP_PORT=587 and an App Password
(Google Account -> Security -> 2-Step Verification -> App passwords).
"""
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

logger = logging.getLogger("ifdc.mailer")


def _settings():
    host = os.getenv("SMTP_HOST", "").strip()
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", "").strip() or user
    return {
        "host": host,
        "port": int(os.getenv("SMTP_PORT", "587") or 587),
        "user": user,
        "password": password,
        "sender": sender,
        "admin": os.getenv("ADMIN_NOTIFY_EMAIL", "").strip() or sender,
    }


def mail_configured() -> bool:
    s = _settings()
    return bool(s["host"] and s["user"] and s["password"] and s["admin"])


def send_admin_email(subject: str, text: str, html: str | None = None, reply_to: str | None = None) -> bool:
    """Send a notification to the admin inbox. Returns True on success, never raises."""
    s = _settings()
    if not mail_configured():
        logger.warning("SMTP is not configured - admin email '%s' was not sent", subject)
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr(("IFDC Website", s["sender"]))
    message["To"] = s["admin"]
    message["Message-ID"] = make_msgid(domain=s["sender"].split("@")[-1] or None)
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(text)
    if html:
        message.add_alternative(html, subtype="html")

    try:
        context = ssl.create_default_context()
        if s["port"] == 465:
            with smtplib.SMTP_SSL(s["host"], s["port"], context=context, timeout=20) as server:
                server.login(s["user"], s["password"])
                server.send_message(message)
        else:
            with smtplib.SMTP(s["host"], s["port"], timeout=20) as server:
                server.starttls(context=context)
                server.login(s["user"], s["password"])
                server.send_message(message)
        return True
    except Exception:  # noqa: BLE001 - notification failures must not break the request
        logger.exception("Failed to send admin email '%s'", subject)
        return False
