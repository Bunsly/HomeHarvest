from dataclasses import dataclass
from enum import Enum


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
    street_address: str
    city: str
    state: str
    zip_code: str
    unit: str | None = None
    country: str | None = None


@dataclass
class Property:
    property_url: str
    site_name: SiteName
    listing_type: ListingType
    address: Address
    property_type: PropertyType | None = None

    # house for sale
    price: int | None = None
    tax_assessed_value: int | None = None
    currency: str | None = None
    square_feet: int | None = None
    beds: int | None = None
    baths: float | None = None
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
    latitude: float | None = None
    longitude: float | None = None
    posted_time: str | None = None

    # building for sale
    bldg_name: str | None = None
    bldg_unit_count: int | None = None
    bldg_min_beds: int | None = None
    bldg_min_baths: float | None = None
    bldg_min_area: int | None = None

    # apt
    apt_min_price: int | None = None
    apt_max_price: int | None = None
    apt_min_sqft: int | None = None
    apt_max_sqft: int | None = None
