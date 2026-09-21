"""Unit tests for the product URL fetcher service.

These test the HTML/JSON-LD parser against crafted HTML, never hitting the real
network. ``httpx.Client`` is monkeypatched to return a canned response so the
tests remain fast and deterministic.
"""

import json
import uuid
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from app.services import product_url_fetcher
from app.schemas.product import ProductUrlSuggestion

# ---------------------------------------------------------------------------
# Helper: a realistic product page HTML with OpenGraph + JSON-LD
# ---------------------------------------------------------------------------

_SAMPLE_URL = "https://www.walmart.com/ip/example-product/123456"

_SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Sample Widget – Great Retail Store</title>
<meta property="og:title" content="Sample Widget – Great Retail Store" />
<meta property="og:description" content="A high-quality widget for everyday use." />
<meta property="og:image" content="https://images.example.com/product.jpg" />
<meta property="og:site_name" content="Great Retail Store" />
<meta name="description" content="This is the meta description of the widget." />
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Product","name":"Sample Widget",
 "image":"https://images.example.com/product.jpg",
 "description":"A high-quality widget for everyday use.",
 "brand":{"@type":"Brand","name":"Acme"},
 "sku":"SKU-12345",
 "gtin13":"0123456789012",
 "offers":{"@type":"Offer","price":"49.99","priceCurrency":"USD","availability":"InStock"}}
</script>
</head>
<body><h1>Sample Widget</h1></body>
</html>
"""


class _FakeResponse:
    def __init__(self, html: str, url: str = _SAMPLE_URL) -> None:
        self.content = html.encode("utf-8")
        self.url = url

    def raise_for_status(self) -> None:
        pass


class _FakeClient:
    def __init__(self, html: str, url: str = _SAMPLE_URL) -> None:
        self._response = _FakeResponse(html, url)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def get(self, url: str):
        return self._response


def _make_fake_client(html: str, url: str = _SAMPLE_URL):
    """Return a callable that produces a _FakeClient for every ``httpx.Client(...)``."""
    return lambda *a, **kw: _FakeClient(html, url)


def _make_error_client(exc_class=Exception):
    def _raise(*a, **kw):
        raise exc_class("connection refused")

    return _raise


# ---------------------------------------------------------------------------
# Tests — happy path
# ---------------------------------------------------------------------------

@patch.object(product_url_fetcher, "httpx")
def test_fetch_extracts_jsonld_product_fields(mock_httpx) -> None:
    mock_httpx.Client = MagicMock(side_effect=_make_fake_client(_SAMPLE_HTML))

    suggestion = product_url_fetcher.fetch_product_from_url("https://www.walmart.com/ip/example-product/123456")

    assert suggestion.error is None
    assert suggestion.product_name == "Sample Widget"
    assert suggestion.selling_price == "49.99"
    assert suggestion.currency == "USD"
    assert suggestion.brand == "Acme"
    assert suggestion.sku == "SKU-12345"
    assert suggestion.barcode == "0123456789012"
    assert suggestion.product_image_url == "https://images.example.com/product.jpg"
    assert suggestion.short_description == "This is the meta description of the widget."
    assert suggestion.description == "A high-quality widget for everyday use."


@patch.object(product_url_fetcher, "httpx")
def test_fetch_falls_back_to_opengraph_when_no_jsonld(mock_httpx) -> None:
    html = """
    <head>
    <title>Widget (No Schema)</title>
    <meta property="og:title" content="Widget (No Schema)" />
    <meta property="og:description" content="Just the OG desc." />
    <meta property="og:image" content="https://example.com/og.jpg" />
    <meta property="og:site_name" content="Sample Store" />
    </head>
    <body></body>
    """
    mock_httpx.Client = MagicMock(side_effect=_make_fake_client(html))

    suggestion = product_url_fetcher.fetch_product_from_url("https://example.com/widget")

    assert suggestion.error is None
    assert suggestion.product_name == "Widget (No Schema)"
    assert suggestion.product_image_url == "https://example.com/og.jpg"
    assert suggestion.short_description == "Just the OG desc."


# ---------------------------------------------------------------------------
# Tests — URL normalization
# ---------------------------------------------------------------------------

@patch.object(product_url_fetcher, "httpx")
def test_fetch_prepends_https_when_scheme_is_missing(mock_httpx) -> None:
    captured_urls: list[str] = []

    def fake_client(*a, **kw):
        def _orig(url):
            captured_urls.append(url)
            return _FakeResponse(_SAMPLE_HTML, url)

        class _Client:
            def __enter__(self):
                return self
            def __exit__(self, *x):
                pass
            def get(self, url):
                return _orig(url)
        return _Client()

    mock_httpx.Client = MagicMock(side_effect=fake_client)
    suggestion = product_url_fetcher.fetch_product_from_url("www.walmart.com/ip/example-product/123456")

    assert captured_urls[0].startswith("https://")
    assert suggestion.error is None


# ---------------------------------------------------------------------------
# Tests — network failure
# ---------------------------------------------------------------------------

@patch.object(product_url_fetcher, "httpx")
def test_fetch_returns_error_when_httpx_fails(mock_httpx) -> None:
    mock_httpx.Client = MagicMock(side_effect=_make_error_client(httpx_error))
    mock_httpx.HTTPError = httpx_error

    suggestion = product_url_fetcher.fetch_product_from_url("https://www.walmart.com/ip/example-product/123456")

    assert suggestion.error is not None
    assert "block" in suggestion.error.lower()


class httpx_error(Exception):
    """Minimal stand-in so we can reference the exception class before patching."""


# ---------------------------------------------------------------------------
# Tests — page loaded but has no product data
# ---------------------------------------------------------------------------

@patch.object(product_url_fetcher, "httpx")
def test_fetch_returns_error_when_page_has_no_product_data(mock_httpx) -> None:
    html = """
    <head><title>No Product Here</title></head>
    <body><p>Hello, this is a blog post.</p></body>
    """
    mock_httpx.Client = MagicMock(side_effect=_make_fake_client(html))

    suggestion = product_url_fetcher.fetch_product_from_url("https://example.com/blog")

    assert suggestion.error is not None
    assert "no product data" in suggestion.error.lower()


# ---------------------------------------------------------------------------
# Tests — price parsing edge cases
# ---------------------------------------------------------------------------

@patch.object(product_url_fetcher, "httpx")
def test_fetch_extracts_low_price_from_offers_array(mock_httpx) -> None:
    html = """
    <head><title>Variant</title></head>
    <body>
    <script type="application/ld+json">
    {"@type":"Product","name":"Variant Widget",
     "offers":[{"@type":"Offer","price":"19.99","priceCurrency":"CAD"},
               {"@type":"Offer","price":"29.99","priceCurrency":"CAD"}]}
    </script>
    </body>
    """
    mock_httpx.Client = MagicMock(side_effect=_make_fake_client(html))

    suggestion = product_url_fetcher.fetch_product_from_url("https://example.com/variant")

    assert suggestion.selling_price == "19.99"
    assert suggestion.currency == "CAD"
