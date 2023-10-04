from dataclasses import dataclass
import requests
import tls_client
from typing import Optional
from .models import Property, SiteName, Status
from ...exceptions import InvalidTimeFrame

VALID_TIMEFRAMES = ["1W", "1M", "3M", "6M", "1Y"]
VALID_STATUSES = ["sold", "for_sale", "for_rent"]


@dataclass
class ScraperInput:
    location: str
    status: str
    site_name: str
    proxy: Optional[str] = None
    timeframe: Optional[str] = None

    def __post_init__(self):
        if self.status == "sold" and not self.timeframe:
            raise InvalidTimeFrame("Timeframe is required when status is 'sold'")

        if self.timeframe and self.timeframe not in VALID_TIMEFRAMES:
            raise InvalidTimeFrame(f"Invalid timeframe provided: {self.timeframe}")

        if self.status and self.status not in VALID_STATUSES:
            raise InvalidTimeFrame(f"Invalid status provided: {self.status}")


class Scraper:
    def __init__(
        self,
        scraper_input: ScraperInput,
        session: requests.Session | tls_client.Session = None,
    ):
        self.location = scraper_input.location
        self.status = scraper_input.status
        self.timeframe = scraper_input.timeframe

        if not session:
            self.session = requests.Session()
        else:
            self.session = session

        if scraper_input.proxy:
            proxy_url = scraper_input.proxy
            proxies = {"http": proxy_url, "https": proxy_url}
            self.session.proxies.update(proxies)

        self.listing_type = scraper_input.status
        self.site_name = scraper_input.site_name

    def search(self) -> list[Property]:
        ...

    @staticmethod
    def _parse_home(home) -> Property:
        ...

    def handle_location(self):
        ...
