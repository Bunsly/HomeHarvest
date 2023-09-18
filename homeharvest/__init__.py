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


def validate_input(site_name: str, listing_type: str) -> None:
    if site_name.lower() not in _scrapers:
        raise InvalidSite(f"Provided site, '{site_name}', does not exist.")

    if listing_type.upper() not in ListingType.__members__:
        raise InvalidListingType(
            f"Provided listing type, '{listing_type}', does not exist."
        )


def get_ordered_properties(result: Union[Building, Property]) -> list[str]:
    if isinstance(result, Property):
        return [
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
        return [
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
    return []


def process_result(result: Union[Building, Property]) -> pd.DataFrame:
    prop_data = result.__dict__

    address_data = prop_data["address"]
    prop_data["site_name"] = prop_data["site_name"]
    prop_data["listing_type"] = prop_data["listing_type"].value
    prop_data["property_type"] = prop_data["property_type"].value.lower() if prop_data["property_type"] else None
    prop_data["address_one"] = address_data.address_one
    prop_data["city"] = address_data.city
    prop_data["state"] = address_data.state
    prop_data["zip_code"] = address_data.zip_code
    prop_data["address_two"] = address_data.address_two

    del prop_data["address"]

    properties_df = pd.DataFrame([prop_data])
    properties_df = properties_df[get_ordered_properties(result)]

    return properties_df


def scrape_property(
    location: str,
    site_name: str,
    listing_type: str = "for_sale",  #: for_sale, for_rent, sold
) -> pd.DataFrame:
    validate_input(site_name, listing_type)

    scraper_input = ScraperInput(
        location=location,
        listing_type=ListingType[listing_type.upper()],
        site_name=site_name.lower(),
    )

    site = _scrapers[site_name.lower()](scraper_input)
    results = site.search()

    properties_dfs = [process_result(result) for result in results]

    return pd.concat(properties_dfs, ignore_index=True)
