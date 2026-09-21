"""Best-effort product-page data extraction.

Pastes a retailer product page URL (e.g. a Walmart item page) and pulls the fields
embedded in that page's structured data — OpenGraph meta tags + schema.org JSON-LD —
so the person at the POS doesn't have to type name/price/image/brand/SKU by hand.

Deliberate limits (honest by design):
- Only server-side structured data is read (nog JS rendering) — sites that render all
  of their data client-side won't yield anything.
- Extraction is best-effort; results must be reviewed in the form before saving.
- Nothing here touches the database — this service returns a suggestion only.
- Uses Python's stdlib html.parser, so no new parsing dependency is added.
"""

import html
import json
import re
from html.parser import HTMLParser
from urllib.parse import urljoin

import httpx

from app.schemas.product import ProductUrlSuggestion

_TIMEOUT_SECONDS = 12.0
_MAX_BYTES = 8 * 1024 * 1024  # stop reading a page that is huge/unbounded

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Separators used to strip a site-name suffix from a page title, e.g.
# "Product Name | Walmart.com" -> "Product Name".
_TITLE_SEPARATORS = (" | ", " - ", " – ", " — ", " · ", " :: ")
_SITE_NAME_MARKERS = ("walmart", "amazon", "bestbuy", ".com", ".ca")

_PRICE_RE = re.compile(r"\d+(?:\.\d+)?")


def fetch_product_from_url(url: str) -> ProductUrlSuggestion:
    """Fetch ``url`` and return whatever product fields can be extracted.

    Never raises for network problems — a fetch that fails (bot protection, timeout,
    no product data) returns a suggestion with ``error`` set so the caller can show a
    clear message and the user can fall back to manual entry.
    """
    normalized = _normalize_url(url)
    suggestion = ProductUrlSuggestion(url=normalized)

    try:
        with httpx.Client(
            timeout=_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers=_BROWSER_HEADERS,
        ) as client:
            response = client.get(normalized)
            response.raise_for_status()
            content = response.content[:_MAX_BYTES].decode("utf-8", errors="replace")
    except httpx.HTTPError:
        suggestion.error = "Couldn't fetch the page — the site may be blocking the request."
        return suggestion

    parsed = _parse_html(content)
    fields = _extract_fields(parsed, base_url=str(response.url))

    if not any(fields.get(f) for f in _PRODUCT_SIGNAL_FIELDS):
        suggestion.error = "The page loaded but no product data could be found on it."
        return suggestion

    suggestion.product_name = fields.get("product_name")
    suggestion.selling_price = fields.get("selling_price")
    suggestion.currency = fields.get("currency")
    suggestion.brand = fields.get("brand")
    suggestion.sku = fields.get("sku")
    suggestion.barcode = fields.get("barcode")
    suggestion.product_image_url = fields.get("product_image_url")
    suggestion.short_description = fields.get("short_description")
    suggestion.description = fields.get("description")
    return suggestion


_EXTRACTABLE_FIELDS = (
    "product_name",
    "selling_price",
    "currency",
    "brand",
    "sku",
    "barcode",
    "product_image_url",
    "short_description",
    "description",
)

# Fields that signal the page genuinely describes a product. The <title> tag (which
# feeds product_name) exists on every page — a blog post title is not product data.
# The heuristic: require at least one of these to deem the extraction successful.
_PRODUCT_SIGNAL_FIELDS = ("selling_price", "brand", "sku", "barcode", "product_image_url")


def _normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


class _PageParser(HTMLParser):
    """Collects the only HTML bits this feature needs: <title>, meta tags (OG +
    description), and <script type="application/ld+json"> blocks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: str | None = None
        self.meta: dict[str, str] = {}  # property-or-name -> content
        self.jsonld_blocks: list[str] = []

        self._in_title = False
        self._title_parts: list[str] = []
        self._capture_jsonld = False
        self._jsonld_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self._in_title = True
            self._title_parts = []
        elif tag == "meta":
            content = attrs.get("content")
            key = attrs.get("property") or attrs.get("name")
            if content and key:
                self.meta.setdefault(key.strip().lower(), content)
        elif tag == "script" and attrs.get("type", "").strip().lower() == "application/ld+json":
            self._capture_jsonld = True
            self._jsonld_parts = []

    def handle_data(self, data):
        if self._in_title:
            self._title_parts.append(data)
        if self._capture_jsonld:
            self._jsonld_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "title" and self._in_title:
            self._in_title = False
            self.title = html.unescape("".join(self._title_parts)).strip()
        elif tag == "script" and self._capture_jsonld:
            self._capture_jsonld = False
            self.jsonld_blocks.append("".join(self._jsonld_parts))


def _parse_html(content: str) -> _PageParser:
    parser = _PageParser()
    parser.feed(content)
    return parser


def _extract_fields(parsed: _PageParser, *, base_url: str) -> dict[str, str | None]:
    """Merge JSON-LD (preferred) with OpenGraph/title/meta fallbacks."""
    jsonld = _find_product_jsonld(parsed.jsonld_blocks)
    meta = parsed.meta

    product_name = (
        jsonld.get("name")
        or _clean_title(meta.get("og:title") or parsed.title or "")
        or None
    )
    brand = _json_key(jsonld, ("brand",), "name") or _clean_site_name(meta.get("og:site_name"))
    image = _json_media_url(jsonld, "image") or meta.get("og:image") or meta.get("twitter:image")
    description = _json_key(jsonld, None, "description") or meta.get("og:description")
    short_description = meta.get("description") or description
    sku = jsonld.get("sku")
    barcode = _first(jsonld.get(k) for k in ("gtin", "gtin13", "gtin14", "gtin12", "gtin8"))
    price, currency = _json_price(jsonld)

    image = _resolve_url(image, base_url)

    result = {
        "product_name": _clean(product_name, 255),
        "selling_price": price,
        "currency": _clean(currency, 10) or None,
        "brand": _clean(brand, 255) or None,
        "sku": _clean(sku, 150) or None,
        "barcode": _clean(barcode, 150) or None,
        "product_image_url": _clean(image, 500) or None,
        "short_description": _clean(short_description, 500) or None,
        "description": _clean(description, 2000) or None,
    }
    return result


def _find_product_jsonld(blocks: list[str]) -> dict:
    """Return the schema.org Product object found in the JSON-LD blocks, or {}."""
    for block in blocks:
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        node = _walk_for_product(data)
        if node:
            return node
    return {}


def _walk_for_product(data) -> dict | None:
    """Depth-first search for a node whose @type includes 'Product'."""
    if isinstance(data, list):
        for item in data:
            found = _walk_for_product(item)
            if found:
                return found
    elif isinstance(data, dict):
        type_ = data.get("@type")
        types = type_ if isinstance(type_, list) else [type_]
        if "Product" in types:
            return data
        for graph_key in ("@graph", "hasPart"):
            value = data.get(graph_key)
            if value is not None:
                found = _walk_for_product(value)
                if found:
                    return found
        for key, value in data.items():
            if key.startswith("@"):
                continue
            found = _walk_for_product(value)
            if found:
                return found
    return None


def _json_key(node: dict, path: tuple | None, key: str) -> str | None:
    """Return the first non-null value for ``key`` walking values whose keys match
    ``path`` (or everything when path is None). Handles lists and wrapped objects."""
    if path:
        current = node
        for part in path:
            value = current.get(part)
            if isinstance(value, list):
                value = _first(value)
            if not isinstance(value, dict):
                return _string(value)
            current = value
        value = current.get(key)
        return _string(value) if not isinstance(value, (dict, list)) else None

    # No path: probe mutable fields (sku, name, ...) using the top-level node and any
    # nested dict values recursively, taking the first non-null match of node[key].
    def _probe(n):
        if isinstance(n, dict):
            v = n.get(key)
            if v is not None and not isinstance(v, (dict, list)):
                return _string(v)
            for sub in n.values():
                found = _probe(sub)
                if found:
                    return found
        elif isinstance(n, list):
            for sub in n:
                found = _probe(sub)
                if found:
                    return found
        return None

    return _probe(node)


def _json_price(node: dict) -> tuple[str | None, str | None]:
    """Best-effort price/currency from offers (dict, list, or wrapped)."""
    offers = node.get("offers")
    if isinstance(offers, list):
        offers = _first(offers)
    if isinstance(offers, dict) and "offers" in offers:
        offers = offers["offers"]
        if isinstance(offers, list):
            offers = _first(offers)
    if not isinstance(offers, dict):
        return None, None

    price = None
    for key in ("price", "lowPrice", "highPrice"):
        value = _string(offers.get(key))
        if value:
            parsed = _PRICE_RE.search(value)
            if parsed:
                price = parsed.group()
                break
    currency = _string(offers.get("priceCurrency")) or _string(offers.get("currency"))
    return price, currency


def _json_media_url(node: dict, key: str) -> str | None:
    """Resolve an image/media value that may be a str, a list, or {url: ...}."""
    value = node.get(key)
    if isinstance(value, list):
        value = _first(value)
    if isinstance(value, dict):
        value = value.get("url")
    if isinstance(value, list):
        value = _first(value)
    return _string(value)


def _resolve_url(value: str | None, base_url: str) -> str | None:
    return urljoin(base_url, value) if value else None


def _clean_title(title: str) -> str | None:
    """Strip a trailing site-name suffix from an og:title / <title>."""
    title = title.strip()
    if not title:
        return None
    for sep in _TITLE_SEPARATORS:
        for part in title.split(sep):
            part = part.strip()
            if part and not any(m in part.lower() for m in _SITE_NAME_MARKERS):
                return part
    return title


def _clean_site_name(site_name: str | None) -> str | None:
    site_name = (site_name or "").strip()
    return site_name or None


def _clean(value, max_len: int) -> str | None:
    value = _string(value)
    if not value:
        return None
    value = " ".join(value.split())
    return value[:max_len] if len(value) > max_len else value


def _string(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return None
    text = str(value).strip()
    return text or None


def _first(values) -> any:  # noqa: ANN401 — any JSON value
    for value in values:
        if value is not None:
            return value
    return None