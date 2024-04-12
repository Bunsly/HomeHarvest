import pandas as pd
from datetime import datetime
from .core.scrapers.models import Property, ListingType
from .exceptions import InvalidListingType, InvalidDate

ordered_properties = [
    "property_url",
    "mls",
    "mls_id",
    "status",
    "style",
    "street",
    "unit",
    "city",
    "state",
    "zip_code",
    "beds",
    "full_baths",
    "half_baths",
    "sqft",
    "year_built",
    "days_on_mls",
    "list_price",
    "list_date",
    "sold_price",
    "last_sold_date",
    "lot_sqft",
    "price_per_sqft",
    "latitude",
    "longitude",
    "stories",
    "hoa_fee",
    "parking_garage",
    "primary_photo",
    "alt_photos",
]


def process_result(result: Property) -> pd.DataFrame:
    prop_data = {prop: None for prop in ordered_properties}
    prop_data.update(result.__dict__)

    if "address" in prop_data:
        address_data = prop_data["address"]
        prop_data["street"] = address_data.street
        prop_data["unit"] = address_data.unit
        prop_data["city"] = address_data.city
        prop_data["state"] = address_data.state
        prop_data["zip_code"] = address_data.zip

    prop_data["price_per_sqft"] = prop_data["prc_sqft"]

    description = result.description
    prop_data["primary_photo"] = description.primary_photo
    prop_data["alt_photos"] = ", ".join(description.alt_photos)
    prop_data["style"] = description.style.value
    prop_data["beds"] = description.beds
    prop_data["full_baths"] = description.baths_full
    prop_data["half_baths"] = description.baths_half
    prop_data["sqft"] = description.sqft
    prop_data["lot_sqft"] = description.lot_sqft
    prop_data["sold_price"] = description.sold_price
    prop_data["year_built"] = description.year_built
    prop_data["parking_garage"] = description.garage
    prop_data["stories"] = description.stories

    properties_df = pd.DataFrame([prop_data])
    properties_df = properties_df.reindex(columns=ordered_properties)

    return properties_df[ordered_properties]


def validate_input(listing_type: str) -> None:
    if listing_type.upper() not in ListingType.__members__:
        raise InvalidListingType(
            f"Provided listing type, '{listing_type}', does not exist."
        )


def validate_dates(date_from: str | None, date_to: str | None) -> None:
    if (date_from is not None and date_to is None) or (date_from is None and date_to is not None):
        raise InvalidDate("Both date_from and date_to must be provided.")

    if date_from and date_to:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")

            if date_to_obj < date_from_obj:
                raise InvalidDate("date_to must be after date_from.")
        except ValueError as e:
            raise InvalidDate(f"Invalid date format or range")
