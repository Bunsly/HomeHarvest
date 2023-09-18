from .core.scrapers.redfin import RedfinScraper
from .core.scrapers.realtor import RealtorScraper
from .core.scrapers.zillow import ZillowScraper
from .core.scrapers.models import ListingType, Property, SiteName
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


def get_ordered_properties(result: Property) -> list[str]:
    return [
        "property_url",
        "site_name",
        "listing_type",
        "property_type",
        "status_text",
        "currency",
        "price",
        "apt_min_price",
        "tax_assessed_value",
        "square_feet",
        "price_per_sqft",
        "beds",
        "baths",
        "lot_area_value",
        "lot_area_unit",
        "street_address",
        "unit",
        "city",
        "state",
        "zip_code",
        "country",
        "posted_time",
        "bldg_min_beds",
        "bldg_min_baths",
        "bldg_min_area",
        "bldg_unit_count",
        "bldg_name",
        "stories",
        "year_built",
        "agent_name",
        "mls_id",
        "description",
        "img_src",
        "latitude",
        "longitude",
    ]


def process_result(result: Property) -> pd.DataFrame:
    prop_data = result.__dict__

    prop_data["site_name"] = prop_data["site_name"].value
    prop_data["listing_type"] = prop_data["listing_type"].value.lower()
    prop_data["property_type"] = prop_data["property_type"].value.lower()
    if "address" in prop_data:
        address_data = prop_data["address"]
        prop_data["street_address"] = address_data.street_address
        prop_data["unit"] = address_data.unit
        prop_data["city"] = address_data.city
        prop_data["state"] = address_data.state
        prop_data["zip_code"] = address_data.zip_code
        prop_data["country"] = address_data.country

        del prop_data["address"]

    properties_df = pd.DataFrame([prop_data])
    properties_df = properties_df[get_ordered_properties(result)]

    return properties_df


def scrape_property(
    location: str,
    site_name: str,
    listing_type: str = "for_sale",  #: for_sale, for_rent, sold
) -> list[Property]:
    validate_input(site_name, listing_type)

    scraper_input = ScraperInput(
        location=location,
        listing_type=ListingType[listing_type.upper()],
        site_name=SiteName[site_name.upper()],
    )

    site = _scrapers[site_name.lower()](scraper_input)
    results = site.search()

    properties_dfs = [process_result(result) for result in results]
    if not properties_dfs:
        return pd.DataFrame()

    return pd.concat(properties_dfs, ignore_index=True)
