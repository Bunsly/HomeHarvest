from dataclasses import dataclass
import requests
from .models import Property, ListingType


@dataclass
class ScraperInput:
    location: str
    listing_type: ListingType
    proxy_url: str | None = None


class Scraper:
    listing_type = ListingType.FOR_SALE

    def __init__(self, scraper_input: ScraperInput):
        self.location = scraper_input.location
        self.session = requests.Session()
        Scraper.listing_type = scraper_input.listing_type

        if scraper_input.proxy_url:
            self.session.proxies = {
                "http": scraper_input.proxy_url,
                "https": scraper_input.proxy_url,
            }

    def search(self) -> list[Property]:
        ...

    @staticmethod
    def _parse_home(home) -> Property:
        ...

    def handle_location(self):
        ...
