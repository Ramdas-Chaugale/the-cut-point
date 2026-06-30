"""Email notification tests (SMTP fully mocked — no real network)."""

from __future__ import annotations

from datetime import datetime
from email.message import EmailMessage

import pytest
from app.services import email


class FakeSMTP:
    """Records messages instead of sending them."""

    sent: list[EmailMessage] = []

    def __init__(self, host: str, port: int, timeout: int | None = None) -> None:
        pass

    def __enter__(self) -> FakeSMTP:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def starttls(self) -> None:
        pass

    def login(self, user: str, password: str) -> None:
        pass

    def send_message(self, msg: EmailMessage) -> None:
        FakeSMTP.sent.append(msg)


@pytest.fixture(autouse=True)
def _reset() -> None:
    FakeSMTP.sent = []


def test_disabled_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(email, "_email_enabled", lambda: False)
    assert email.send_email("a@b.com", "Subject", "Body") is False
    assert FakeSMTP.sent == []


def test_sends_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(email, "_email_enabled", lambda: True)
    monkeypatch.setattr(email.smtplib, "SMTP", FakeSMTP)
    assert email.send_email("a@b.com", "Subject", "Body") is True
    assert len(FakeSMTP.sent) == 1
    assert FakeSMTP.sent[0]["To"] == "a@b.com"
    assert FakeSMTP.sent[0]["Subject"] == "Subject"


def test_smtp_error_returns_false(monkeypatch: pytest.MonkeyPatch) -> None:
    class Boom:
        def __init__(self, *a: object, **k: object) -> None:
            raise OSError("connection refused")

    monkeypatch.setattr(email, "_email_enabled", lambda: True)
    monkeypatch.setattr(email.smtplib, "SMTP", Boom)
    assert email.send_email("a@b.com", "s", "b") is False


def test_notify_accepted_subject(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(email, "_email_enabled", lambda: True)
    monkeypatch.setattr(email.smtplib, "SMTP", FakeSMTP)
    email.notify_accepted(
        "c@b.com",
        service_name="Classic Cut",
        salon_name="Sharp Fades",
        when=datetime(2024, 1, 1, 10, 0),
    )
    assert "Sharp Fades" in FakeSMTP.sent[0]["Subject"]
    assert "Classic Cut" in FakeSMTP.sent[0].get_content()


def test_notify_declined_includes_suggestion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(email, "_email_enabled", lambda: True)
    monkeypatch.setattr(email.smtplib, "SMTP", FakeSMTP)
    email.notify_declined(
        "c@b.com",
        service_name="Classic Cut",
        salon_name="Sharp Fades",
        suggested=datetime(2024, 1, 2, 11, 0),
    )
    body = FakeSMTP.sent[0].get_content()
    assert "11:00" in body
