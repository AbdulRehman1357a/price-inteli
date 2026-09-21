from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class RawCompetitorPriceObservation:
    price: Decimal
    currency: str
    availability: str | None


class CompetitorPriceProvider(ABC):
    """Rule: manual entry and API ingestion are the only two ways a
    CompetitorPrice row gets created — "do not implement unauthorized
    scraping." Manual entry (competitor_service.record_manual_price) writes
    a row directly from a form submission, no adapter needed. This
    interface is for the API path only: it fetches from a URL the
    organization has already configured on the CompetitorProduct itself
    (external_product_url) — a legitimate, authorized API endpoint the org
    has access to (e.g. their own competitive-intelligence data
    subscription), never a scraper crawling a competitor's own HTML pages.
    """

    @abstractmethod
    def fetch_price(self, external_product_url: str) -> RawCompetitorPriceObservation: ...
