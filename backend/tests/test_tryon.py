"""Realistic AI try-on tests (fal.ai fully mocked — no real API calls)."""

from __future__ import annotations

import pytest
from app.main import app
from app.services import tryon
from fastapi.testclient import TestClient

client = TestClient(app)

_IMG = "data:image/jpeg;base64," + "A" * 64


def test_build_prompt_known_style() -> None:
    prompt = tryon.build_prompt("high-fade-pompadour")
    assert "Pompadour" in prompt
    assert "same face" in prompt.lower() or "identity" in prompt.lower()


def test_build_prompt_unknown_style() -> None:
    with pytest.raises(tryon.TryOnError):
        tryon.build_prompt("does-not-exist")


def test_generate_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tryon, "_enabled", lambda: False)
    with pytest.raises(tryon.TryOnError):
        tryon.generate_tryon(_IMG, "high-fade-pompadour")


def test_generate_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tryon, "_enabled", lambda: True)
    monkeypatch.setattr(
        tryon,
        "_run_fal",
        lambda model, prompt, image_url: {"images": [{"url": "https://cdn.fal/out.png"}]},
    )
    assert tryon.generate_tryon(_IMG, "high-fade-pompadour") == "https://cdn.fal/out.png"


def test_generate_upstream_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(model: str, prompt: str, image_url: str) -> dict:
        raise RuntimeError("quota exceeded")

    monkeypatch.setattr(tryon, "_enabled", lambda: True)
    monkeypatch.setattr(tryon, "_run_fal", boom)
    with pytest.raises(tryon.TryOnError):
        tryon.generate_tryon(_IMG, "high-fade-pompadour")


def test_endpoint_unavailable_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tryon, "_enabled", lambda: False)
    resp = client.post(
        "/api/tryon/generate", json={"image_data_url": _IMG, "style_id": "high-fade-pompadour"}
    )
    assert resp.status_code == 503


def test_endpoint_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tryon, "_enabled", lambda: True)
    monkeypatch.setattr(
        tryon,
        "_run_fal",
        lambda model, prompt, image_url: {"images": [{"url": "https://cdn.fal/out.png"}]},
    )
    resp = client.post(
        "/api/tryon/generate", json={"image_data_url": _IMG, "style_id": "high-fade-pompadour"}
    )
    assert resp.status_code == 200
    assert resp.json()["image_url"] == "https://cdn.fal/out.png"


def _fail_with(monkeypatch: pytest.MonkeyPatch, message: str) -> None:
    def boom(model: str, prompt: str, image_url: str) -> dict:
        raise RuntimeError(message)

    monkeypatch.setattr(tryon, "_enabled", lambda: True)
    monkeypatch.setattr(tryon, "_run_fal", boom)


def test_billing_state_is_not_shown_to_the_user(monkeypatch: pytest.MonkeyPatch) -> None:
    # fal returns "User is locked. Reason: TOP_UP." when the account is empty.
    # That is the account holder's business, not something to put on screen.
    _fail_with(monkeypatch, "User is locked. Reason: TOP_UP.")
    with pytest.raises(tryon.TryOnError) as err:
        tryon.generate_tryon(_IMG, "high-fade-pompadour")

    shown = str(err.value)
    assert "temporarily unavailable" in shown
    for leak in ("TOP_UP", "locked", "User is"):
        assert leak not in shown


def test_quota_message_is_sanitised(monkeypatch: pytest.MonkeyPatch) -> None:
    _fail_with(monkeypatch, "insufficient credit on account acct_9931")
    with pytest.raises(tryon.TryOnError) as err:
        tryon.generate_tryon(_IMG, "high-fade-pompadour")
    assert "acct_9931" not in str(err.value)


def test_rate_limit_gets_its_own_message(monkeypatch: pytest.MonkeyPatch) -> None:
    _fail_with(monkeypatch, "429 rate limit exceeded")
    with pytest.raises(tryon.TryOnError) as err:
        tryon.generate_tryon(_IMG, "high-fade-pompadour")
    assert "busy" in str(err.value)


def test_unknown_failure_gets_a_generic_message(monkeypatch: pytest.MonkeyPatch) -> None:
    _fail_with(monkeypatch, "ConnectionResetError at 10.0.0.4:443")
    with pytest.raises(tryon.TryOnError) as err:
        tryon.generate_tryon(_IMG, "high-fade-pompadour")
    shown = str(err.value)
    assert "10.0.0.4" not in shown
    assert "could not generate" in shown


def test_endpoint_does_not_leak_billing_state(monkeypatch: pytest.MonkeyPatch) -> None:
    _fail_with(monkeypatch, "User is locked. Reason: TOP_UP.")
    resp = client.post(
        "/api/tryon/generate", json={"image_data_url": _IMG, "style_id": "high-fade-pompadour"}
    )
    assert resp.status_code == 502
    assert "TOP_UP" not in resp.text


# --- free inpainting provider ------------------------------------------------

_MASK = "data:image/png;base64," + "B" * 64
_PNG = b"\x89PNG\r\n\x1a\n" + b"fake"


def _cloudflare_on(monkeypatch: pytest.MonkeyPatch, on: bool = True) -> None:
    settings = tryon.get_settings()
    monkeypatch.setattr(type(settings), "cloudflare_enabled", property(lambda self: on))


def test_a_mask_selects_inpainting_and_returns_a_data_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tryon, "_enabled", lambda: True)
    _cloudflare_on(monkeypatch)
    monkeypatch.setattr(tryon, "_run_cloudflare_inpaint", lambda *a, **k: _PNG)

    def fal_must_not_run(*_a, **_k):
        raise AssertionError("fal.ai was called even though a mask was supplied")

    monkeypatch.setattr(tryon, "_run_fal", fal_must_not_run)

    out = tryon.generate_tryon(_IMG, "high-fade-pompadour", _MASK)
    assert out.startswith("data:image/png;base64,")


def test_without_a_mask_it_falls_through_to_fal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tryon, "_enabled", lambda: True)
    _cloudflare_on(monkeypatch)
    monkeypatch.setattr(
        tryon,
        "_run_fal",
        lambda model, prompt, image_url: {"images": [{"url": "https://cdn.fal/out.png"}]},
    )
    assert tryon.generate_tryon(_IMG, "high-fade-pompadour") == "https://cdn.fal/out.png"


def test_the_inpaint_prompt_describes_rather_than_instructs() -> None:
    # Inpainting fills a region, so an instruction to "change" the hair makes no
    # sense: there is nothing there to change.
    prompt = tryon.build_inpaint_prompt("high-fade-pompadour")
    assert "Pompadour" in prompt
    assert "change" not in prompt.lower()
    assert "photorealistic" in prompt.lower()


def test_inpaint_failure_is_sanitised(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tryon, "_enabled", lambda: True)
    _cloudflare_on(monkeypatch)

    def boom(*_a, **_k):
        raise RuntimeError("HTTP 500: account 1234abcd internal failure")

    monkeypatch.setattr(tryon, "_run_cloudflare_inpaint", boom)
    with pytest.raises(tryon.TryOnError) as err:
        tryon.generate_tryon(_IMG, "high-fade-pompadour", _MASK)
    assert "1234abcd" not in str(err.value)


def test_exhausted_allowance_says_the_preview_still_works(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tryon, "_enabled", lambda: True)
    _cloudflare_on(monkeypatch)

    def boom(*_a, **_k):
        raise RuntimeError("you have used up your daily free allocation of 10,000 neurons")

    monkeypatch.setattr(tryon, "_run_cloudflare_inpaint", boom)
    with pytest.raises(tryon.TryOnError) as err:
        tryon.generate_tryon(_IMG, "high-fade-pompadour", _MASK)
    shown = str(err.value)
    assert "free limit" in shown
    assert "neurons" not in shown


def test_a_malformed_mask_is_reported_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tryon, "_enabled", lambda: True)
    _cloudflare_on(monkeypatch)

    def must_not_reach_the_network(*_a, **_k):
        raise AssertionError("a bad mask should be rejected before any request")

    monkeypatch.setattr(tryon, "_run_cloudflare_inpaint", must_not_reach_the_network)
    with pytest.raises(tryon.TryOnError) as err:
        tryon.generate_tryon(_IMG, "high-fade-pompadour", "data:image/png;base64,!!!!")
    assert "could not be read" in str(err.value)
