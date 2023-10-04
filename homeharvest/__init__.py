import pandas as pd
from typing import Union
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from .utils import process_result, ordered_properties
from .core.scrapers import ScraperInput
from .core.scrapers.realtor import RealtorScraper
from .core.scrapers.models import Status, Property, SiteName
from .exceptions import InvalidSite, InvalidListingType


_scrapers = {
    "realtor.com": RealtorScraper,
}


def _validate_input(site_name: str, status: str) -> None:
    if site_name.lower() not in _scrapers:
        raise InvalidSite(f"Provided site, '{site_name}', does not exist.")

    if status.upper() not in Status.__members__:
        raise InvalidListingType(f"Provided listing type, '{status}', does not exist.")


def _scrape_single_site(
    location: str, site_name: str, status: str, proxy: str = None, timeframe: str = None
) -> pd.DataFrame:
    """
    Helper function to scrape a single site.
    """
    _validate_input(site_name, status)

    scraper_input = ScraperInput(
        location=location,
        status=status,
        site_name=SiteName.get_by_value(site_name.lower()),
        proxy=proxy,
        timeframe=timeframe,
    )

    site = _scrapers[site_name.lower()](scraper_input)
    results = site.search()

    properties_dfs = [process_result(result) for result in results]
    if not properties_dfs:
        return pd.DataFrame()

    return pd.concat(properties_dfs, ignore_index=True, axis=0)[ordered_properties]


def scrape_property(
    location: str,
    timeframe: str = None,
    site_name: Union[str, list[str]] = None,
    status: str = "sale",
    proxy: str = None,
) -> pd.DataFrame:
    """
    Scrape property from various sites from a given location and listing type.

    :returns: pd.DataFrame
    :param location: US Location (e.g. 'San Francisco, CA', 'Cook County, IL', '85281', '2530 Al Lipscomb Way')
    :param site_name: Site name or list of site names (e.g. ['realtor.com', 'zillow'], 'redfin')
    :param listing_type: Listing type (e.g. 'for_sale', 'for_rent', 'sold')
    :return: pd.DataFrame containing properties
    """
    if site_name is None:
        site_name = list(_scrapers.keys())

    if not isinstance(site_name, list):
        site_name = [site_name]

    results = []

    if len(site_name) == 1:
        final_df = _scrape_single_site(location, site_name[0], status, proxy, timeframe)
        results.append(final_df)
    else:
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(
                    _scrape_single_site, location, s_name, status, proxy, timeframe
                ): s_name
                for s_name in site_name
            }

            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)

    results = [df for df in results if not df.empty and not df.isna().all().all()]

    if not results:
        return pd.DataFrame()

    final_df = pd.concat(results, ignore_index=True)

    columns_to_track = ["Street", "Unit", "Zip"]

    #: validate they exist, otherwise create them
    for col in columns_to_track:
        if col not in final_df.columns:
            final_df[col] = None

    return final_df
