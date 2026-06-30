"""Email notifications via Gmail SMTP.

Notifications are best-effort: if no SMTP credentials are configured, or sending
fails for any reason, we never raise — the booking action has already succeeded
and the in-app status is the source of truth. Sends are scheduled as FastAPI
background tasks so they never add latency to the API response.
"""

from __future__ import annotations

import smtplib
from datetime import datetime
from email.message import EmailMessage

from app.core.config import get_settings


def _email_enabled() -> bool:
    return get_settings().email_enabled


def _fmt(when: datetime) -> str:
    return when.strftime("%a %d %b, %H:%M")


def send_email(to: str, subject: str, body: str) -> bool:
    """Send a plain-text email. Returns True on success, False otherwise."""
    if not _email_enabled():
        return False
    settings = get_settings()
    msg = EmailMessage()
    msg["From"] = f"{settings.email_from_name} <{settings.email_sender}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        return True
    except Exception:
        # Never let a notification failure surface to the booking flow.
        return False


def notify_new_request(
    owner_email: str,
    *,
    client_name: str,
    service_name: str,
    salon_name: str,
    when: datetime,
) -> bool:
    return send_email(
        owner_email,
        f"New booking request — {service_name}",
        (
            f"Hi,\n\n{client_name} has requested a {service_name} at {salon_name} "
            f"for {_fmt(when)}.\n\nLog in to your CutPoint dashboard to accept or "
            f"decline the request.\n\n— CutPoint"
        ),
    )


def notify_accepted(
    client_email: str,
    *,
    service_name: str,
    salon_name: str,
    when: datetime,
) -> bool:
    return send_email(
        client_email,
        f"Your booking is confirmed — {salon_name}",
        (
            f"Good news! {salon_name} has confirmed your {service_name} for "
            f"{_fmt(when)}.\n\nSee you then.\n\n— CutPoint"
        ),
    )


def notify_declined(
    client_email: str,
    *,
    service_name: str,
    salon_name: str,
    suggested: datetime | None,
) -> bool:
    extra = (
        f" They suggested {_fmt(suggested)} instead — open CutPoint to rebook."
        if suggested
        else " Please pick another time on CutPoint."
    )
    return send_email(
        client_email,
        f"Update on your booking — {salon_name}",
        (
            f"Unfortunately {salon_name} couldn't take your {service_name} for "
            f"the requested time.{extra}\n\n— CutPoint"
        ),
    )
