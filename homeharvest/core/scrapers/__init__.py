from dataclasses import dataclass
import requests
import tls_client
from .models import Property, ListingType, SiteName


@dataclass
class ScraperInput:
    location: str
    listing_type: ListingType
    site_name: SiteName
    radius: float | None = None
    proxy: str | None = None


class Scraper:
    def __init__(self, scraper_input: ScraperInput, session: requests.Session | tls_client.Session = None):
        self.location = scraper_input.location
        self.listing_type = scraper_input.listing_type

        if not session:
            self.session = requests.Session()
        else:
            self.session = session

        if scraper_input.proxy:
            proxy_url = scraper_input.proxy
            proxies = {"http": proxy_url, "https": proxy_url}
            self.session.proxies.update(proxies)

        self.listing_type = scraper_input.listing_type
        self.site_name = scraper_input.site_name
        self.radius = scraper_input.radius

    def search(self) -> list[Property]:
        ...

    @staticmethod
    def _parse_home(home) -> Property:
        ...

    def handle_location(self):
        ...
