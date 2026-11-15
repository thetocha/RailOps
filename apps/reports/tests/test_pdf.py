from __future__ import annotations

import pytest

from apps.reports.pdf import (
    MAX_PDF_BYTES,
    RemoteResourceDeniedError,
    blocked_url_fetcher,
    render_pdf,
)


def test_empty_html_renders_a_pdf() -> None:
    payload = render_pdf(
        html="<html><body><h1>RailOps</h1></body></html>", stylesheet="h1{color:black}"
    )
    assert payload.startswith(b"%PDF-")
    assert len(payload) < MAX_PDF_BYTES


def test_blocked_url_fetcher_rejects_remote_urls() -> None:
    with pytest.raises(RemoteResourceDeniedError):
        blocked_url_fetcher("https://example.invalid/secret.png")


def test_remote_image_is_rejected() -> None:
    with pytest.raises(RemoteResourceDeniedError):
        render_pdf(
            html='<html><body><img src="https://example.invalid/x.png"></body></html>',
            stylesheet="",
        )


def test_remote_stylesheet_url_is_rejected() -> None:
    with pytest.raises(RemoteResourceDeniedError):
        render_pdf(
            html="<html><body>Hi</body></html>",
            stylesheet="body{background:url(https://example.invalid/bg.png)}",
        )


def test_oversized_pdf_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeHTML:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def write_pdf(self, *args: object, **kwargs: object) -> bytes:
            return b"%PDF-" + (b"x" * (MAX_PDF_BYTES + 1))

    monkeypatch.setattr("apps.reports.pdf.HTML", FakeHTML)
    monkeypatch.setattr("apps.reports.pdf.CSS", lambda *args, **kwargs: object())
    with pytest.raises(RuntimeError, match="size limit"):
        render_pdf(html="<html></html>", stylesheet="")


def test_non_pdf_bytes_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeHTML:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def write_pdf(self, *args: object, **kwargs: object) -> bytes:
            return b"not-a-pdf"

    monkeypatch.setattr("apps.reports.pdf.HTML", FakeHTML)
    monkeypatch.setattr("apps.reports.pdf.CSS", lambda *args, **kwargs: object())
    with pytest.raises(RuntimeError, match="did not return a PDF"):
        render_pdf(html="<html></html>", stylesheet="")


def test_empty_renderer_output_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeHTML:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def write_pdf(self, *args: object, **kwargs: object) -> None:
            return None

    monkeypatch.setattr("apps.reports.pdf.HTML", FakeHTML)
    monkeypatch.setattr("apps.reports.pdf.CSS", lambda *args, **kwargs: object())
    with pytest.raises(RuntimeError, match="no bytes"):
        render_pdf(html="<html></html>", stylesheet="")
