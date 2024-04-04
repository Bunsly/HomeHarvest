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

        self.session = requests.Session()
        self.session.headers.update({"user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'})
        if scraper_input.proxy:
            proxy_url = scraper_input.proxy
            proxies = {"http": proxy_url, "https": proxy_url}
            self.session.proxies.update(proxies)
        self.listing_type = scraper_input.listing_type
        self.site_name = scraper_input.site_name

    def search(self) -> list[Property]:
        ...

    @staticmethod
    def _parse_home(home) -> Property:
        ...

    def handle_location(self):
        ...
