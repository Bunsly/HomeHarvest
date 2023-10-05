import warnings
import pandas as pd
from .core.scrapers import ScraperInput
from .utils import process_result, ordered_properties, validate_input
from .core.scrapers.realtor import RealtorScraper
from .core.scrapers.models import ListingType
from .exceptions import InvalidListingType, NoResultsFound


def scrape_property(
    location: str,
    listing_type: str = "for_sale",
    radius: float = None,
    mls_only: bool = False,
    past_days: int = None,
    proxy: str = None,
) -> pd.DataFrame:
    """
    Scrape properties from Realtor.com based on a given location and listing type.
    :param location: Location to search (e.g. "Dallas, TX", "85281", "2530 Al Lipscomb Way")
    :param listing_type: Listing Type (for_sale, for_rent, sold)
    :param radius: Get properties within _ (e.g. 1.0) miles. Only applicable for individual addresses.
    :param mls_only: If set, fetches only listings with MLS IDs.
    :param past_days: Get properties sold or listed (dependent on your listing_type) in the last _ days.
    :param proxy: Proxy to use for scraping
    """
    validate_input(listing_type)

    scraper_input = ScraperInput(
        location=location,
        listing_type=ListingType[listing_type.upper()],
        proxy=proxy,
        radius=radius,
        mls_only=mls_only,
        last_x_days=past_days,
    )

    site = RealtorScraper(scraper_input)
    results = site.search()

    properties_dfs = [process_result(result) for result in results]
    if not properties_dfs:
        raise NoResultsFound("no results found for the query")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        return pd.concat(properties_dfs, ignore_index=True, axis=0)[ordered_properties]
