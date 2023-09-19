from dataclasses import dataclass
import requests
from .models import Property, ListingType, SiteName


@dataclass
class ScraperInput:
    location: str
    listing_type: ListingType
    site_name: SiteName
    proxy: str | None = None


class Scraper:
    def __init__(self, scraper_input: ScraperInput):
        self.location = scraper_input.location
        self.listing_type = scraper_input.listing_type

        self.session = requests.Session(proxies=scraper_input.proxy)
        self.listing_type = scraper_input.listing_type
        self.site_name = scraper_input.site_name

        self.proxy = (lambda p: {"http": p, "https": p} if p else None)(
            scraper_input.proxy
        )

    def search(self) -> list[Property]:
        ...

    @staticmethod
    def _parse_home(home) -> Property:
        ...

    def handle_location(self):
        ...
