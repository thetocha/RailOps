"""WeasyPrint rendering. Remote URLs are rejected; CSS is local string only."""

from __future__ import annotations

from weasyprint import CSS, HTML
from weasyprint.urls import FatalURLFetchingError, URLFetcher

MAX_PDF_BYTES = 5 * 1024 * 1024


class RemoteResourceDeniedError(OSError):
    """Raised when WeasyPrint tries to fetch a network or file URL."""


class BlockedURLFetcher(URLFetcher):  # type: ignore[misc]
    """URL fetcher that never opens the network or filesystem."""

    def __init__(self) -> None:
        super().__init__(allowed_protocols=(), allow_redirects=False, fail_on_errors=True)

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> object:
        raise RemoteResourceDeniedError(
            f"Remote resources are not allowed during PDF rendering: {url}"
        )


def blocked_url_fetcher(url: str, **_kwargs: object) -> dict[str, object]:
    raise RemoteResourceDeniedError(f"Remote resources are not allowed during PDF rendering: {url}")


def render_pdf(*, html: str, stylesheet: str) -> bytes:
    fetcher = BlockedURLFetcher()
    try:
        document = HTML(string=html, base_url="", url_fetcher=fetcher)
        pdf = document.write_pdf(
            stylesheets=[CSS(string=stylesheet, base_url="", url_fetcher=fetcher)]
        )
    except FatalURLFetchingError as exc:
        raise RemoteResourceDeniedError(str(exc)) from exc
    if not pdf:
        raise RuntimeError("PDF renderer returned no bytes.")
    payload = bytes(pdf)
    if len(payload) > MAX_PDF_BYTES:
        raise RuntimeError("Generated PDF exceeded the size limit.")
    if not payload.startswith(b"%PDF-"):
        raise RuntimeError("Renderer did not return a PDF.")
    return payload
