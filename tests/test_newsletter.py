from src.web import newsletter, style
from src.web.newsletter import email_from_digest


def test_subject_and_body():
    md = "# Faultline weekly: 2026-11-19 to 2026-11-25\n\nThis week: Bankruptcy filings 1.\n\n## Bankruptcy filings\n- [X Corp](u): text\n"
    subject, body = email_from_digest(md)
    assert subject == "Faultline weekly: 2026-11-19 to 2026-11-25"
    assert body.startswith("This week:") and "# Faultline weekly" not in body
    assert "not investment advice" in body


def test_skips_without_key(monkeypatch, capsys):
    monkeypatch.delenv("BUTTONDOWN_API_KEY", raising=False)
    assert newsletter.main() == 0
    assert "skipped" in capsys.readouterr().out


def test_no_signup_box_until_configured(monkeypatch):
    monkeypatch.setattr(style, "NEWSLETTER_USER", "")
    assert style.subscribe_box() == ""
    monkeypatch.setattr(style, "NEWSLETTER_USER", "faultline")
    box = style.subscribe_box()
    assert "embed-subscribe/faultline" in box and 'name="email"' in box
