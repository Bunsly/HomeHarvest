from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class SiteName(Enum):
    ZILLOW = "zillow"
    REDFIN = "redfin"
    REALTOR = "realtor.com"

    @classmethod
    def get_by_value(cls, value):
        for item in cls:
            if item.value == value:
                return item
        raise ValueError(f"{value} not found in {cls}")


class ListingType(Enum):
    FOR_SALE = "FOR_SALE"
    FOR_RENT = "FOR_RENT"
    SOLD = "SOLD"


class PropertyType(Enum):
    HOUSE = "HOUSE"
    BUILDING = "BUILDING"
    CONDO = "CONDO"
    TOWNHOUSE = "TOWNHOUSE"
    SINGLE_FAMILY = "SINGLE_FAMILY"
    MULTI_FAMILY = "MULTI_FAMILY"
    MANUFACTURED = "MANUFACTURED"
    NEW_CONSTRUCTION = "NEW_CONSTRUCTION"
    APARTMENT = "APARTMENT"
    APARTMENTS = "APARTMENTS"
    LAND = "LAND"
    LOT = "LOT"
    OTHER = "OTHER"

    BLANK = "BLANK"

    @classmethod
    def from_int_code(cls, code):
        mapping = {
            1: cls.HOUSE,
            2: cls.CONDO,
            3: cls.TOWNHOUSE,
            4: cls.MULTI_FAMILY,
            5: cls.LAND,
            6: cls.OTHER,
            8: cls.SINGLE_FAMILY,
            13: cls.SINGLE_FAMILY,
        }

        return mapping.get(code, cls.BLANK)


@dataclass
class Address:
    address_one: str | None = None
    address_two: str | None = "#"
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None


@dataclass
class Property:
    property_url: str
    site_name: SiteName
    listing_type: ListingType
    address: Address
    property_type: PropertyType | None = None

    # house for sale
    tax_assessed_value: int | None = None
    lot_area_value: float | None = None
    lot_area_unit: str | None = None
    stories: int | None = None
    year_built: int | None = None
    price_per_sqft: int | None = None
    mls_id: str | None = None

    agent_name: str | None = None
    img_src: str | None = None
    description: str | None = None
    status_text: str | None = None
    posted_time: str | None = None

    # building for sale
    bldg_name: str | None = None
    area_min: int | None = None

    beds_min: int | None = None
    beds_max: int | None = None

    baths_min: float | None = None
    baths_max: float | None = None

    sqft_min: int | None = None
    sqft_max: int | None = None

    price_min: int | None = None
    price_max: int | None = None

    unit_count: int | None = None

    latitude: float | None = None
    longitude: float | None = None
