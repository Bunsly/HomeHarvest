from .core.scrapers.redfin import RedfinScraper
from .core.scrapers.types import ListingType, Home
from .core.scrapers import ScraperInput
from .exceptions import InvalidSite, InvalidListingType


_scrapers = {
    "redfin": RedfinScraper,
}


def scrape_property(
        location: str,
        listing_type: str = "for_sale",  #: for_sale, for_rent, sold
        site_name: str = "redfin",
) -> list[Home]:  #: eventually, return pandas dataframe
    if site_name.lower() not in _scrapers:
        raise InvalidSite(f"Provided site, '{site_name}', does not exist.")

    if listing_type.upper() not in ListingType.__members__:
        raise InvalidListingType(f"Provided listing type, '{listing_type}', does not exist.")

    scraper_input = ScraperInput(
        location=location,
        listing_type=ListingType[listing_type.upper()],
    )

    site = _scrapers[site_name.lower()](scraper_input)

    return site.search()
