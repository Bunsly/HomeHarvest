from dataclasses import dataclass
import requests
from .models import Property, ListingType, SiteName


@dataclass
class ScraperInput:
    location: str
    listing_type: ListingType
    radius: float | None = None
    mls_only: bool | None = None
    proxy: str | None = None
    last_x_days: int | None = None


class Scraper:
    def __init__(
        self,
        scraper_input: ScraperInput,
        session: requests.Session = None,
    ):
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
        self.radius = scraper_input.radius
        self.last_x_days = scraper_input.last_x_days
        self.mls_only = scraper_input.mls_only

    def search(self) -> list[Property]:
        ...

    @staticmethod
    def _parse_home(home) -> Property:
        ...

    def handle_location(self):
        ...
