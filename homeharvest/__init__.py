from .core.scrapers.redfin import RedfinScraper
from .core.scrapers.realtor import RealtorScraper
from .core.scrapers.zillow import ZillowScraper
from .core.scrapers.models import ListingType, Property, Building, SiteName
from .core.scrapers import ScraperInput
from .exceptions import InvalidSite, InvalidListingType
from typing import Union
import pandas as pd


_scrapers = {
    "redfin": RedfinScraper,
    "realtor.com": RealtorScraper,
    "zillow": ZillowScraper,
}


def scrape_property(
    location: str,
    site_name: str,
    listing_type: str = "for_sale",  #: for_sale, for_rent, sold
) -> Union[list[Building], list[Property]]:
    if site_name.lower() not in _scrapers:
        raise InvalidSite(f"Provided site, '{site_name}', does not exist.")

    if listing_type.upper() not in ListingType.__members__:
        raise InvalidListingType(
            f"Provided listing type, '{listing_type}', does not exist."
        )

    scraper_input = ScraperInput(
        location=location,
        listing_type=ListingType[listing_type.upper()],
        site_name=SiteName[site_name.upper()],
    )

    site = _scrapers[site_name.lower()](scraper_input)
    results = site.search()

    properties_dfs = []

    for result in results:
        prop_data = result.__dict__

        address_data = prop_data["address"]
        prop_data["site_name"] = prop_data["site_name"].value
        prop_data["listing_type"] = prop_data["listing_type"].value
        prop_data["property_type"] = prop_data["property_type"].value.lower()
        prop_data["address_one"] = address_data.address_one
        prop_data["city"] = address_data.city
        prop_data["state"] = address_data.state
        prop_data["zip_code"] = address_data.zip_code
        prop_data["address_two"] = address_data.address_two

        del prop_data["address"]

        if isinstance(result, Property):
            desired_order = [
                "listing_type",
                "address_one",
                "city",
                "state",
                "zip_code",
                "address_two",
                "url",
                "property_type",
                "price",
                "beds",
                "baths",
                "square_feet",
                "price_per_square_foot",
                "lot_size",
                "stories",
                "year_built",
                "agent_name",
                "mls_id",
                "description",
            ]

        elif isinstance(result, Building):
            desired_order = [
                "address_one",
                "city",
                "state",
                "zip_code",
                "address_two",
                "url",
                "num_units",
                "min_unit_price",
                "max_unit_price",
                "avg_unit_price",
                "listing_type",
            ]

        properties_df = pd.DataFrame([prop_data])
        properties_df = properties_df[desired_order]
        properties_dfs.append(properties_df)

    return pd.concat(properties_dfs, ignore_index=True)
