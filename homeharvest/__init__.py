import warnings
import pandas as pd
from .core.scrapers import ScraperInput
from .utils import process_result, ordered_properties, validate_input, validate_dates
from .core.scrapers.realtor import RealtorScraper
from .core.scrapers.models import ListingType


def scrape_property(
    location: str,
    listing_type: str = "for_sale",
    radius: float = None,
    mls_only: bool = False,
    past_days: int = None,
    proxy: str = None,
    date_from: str = None,  #: TODO: Switch to one parameter, Date, with date_from and date_to, pydantic validation
    date_to: str = None,
    foreclosure: bool = None,
    extra_property_data: bool = True,
    exclude_pending: bool = False,
) -> pd.DataFrame:
    """
    Scrape properties from Realtor.com based on a given location and listing type.
    :param location: Location to search (e.g. "Dallas, TX", "85281", "2530 Al Lipscomb Way")
    :param listing_type: Listing Type (for_sale, for_rent, sold, pending)
    :param radius: Get properties within _ (e.g. 1.0) miles. Only applicable for individual addresses.
    :param mls_only: If set, fetches only listings with MLS IDs.
    :param proxy: Proxy to use for scraping
    :param past_days: Get properties sold or listed (dependent on your listing_type) in the last _ days.
    :param date_from, date_to: Get properties sold or listed (dependent on your listing_type) between these dates. format: 2021-01-28
    :param foreclosure: If set, fetches only foreclosure listings.
    :param extra_property_data: Increases requests by O(n). If set, this fetches additional property data (e.g. agent, broker, property evaluations etc.)
    :param exclude_pending: If true, this excludes pending or contingent properties from the results, unless listing type is pending.
    """
    validate_input(listing_type)
    validate_dates(date_from, date_to)

    scraper_input = ScraperInput(
        location=location,
        listing_type=ListingType[listing_type.upper()],
        proxy=proxy,
        radius=radius,
        mls_only=mls_only,
        last_x_days=past_days,
        date_from=date_from,
        date_to=date_to,
        foreclosure=foreclosure,
        extra_property_data=extra_property_data,
        exclude_pending=exclude_pending,
    )

    site = RealtorScraper(scraper_input)
    results = site.search()

    properties_dfs = [df for result in results if not (df := process_result(result)).empty]
    if not properties_dfs:
        return pd.DataFrame()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)

        return pd.concat(properties_dfs, ignore_index=True, axis=0)[ordered_properties].replace({"None": pd.NA, None: pd.NA, "": pd.NA})
