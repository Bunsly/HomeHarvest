from dataclasses import dataclass
from enum import Enum


class SiteName(Enum):
    ZILLOW = "zillow"
    REDFIN = "redfin"
    REALTOR = "realtor.com"


class ListingType(Enum):
    FOR_SALE = "for_sale"
    FOR_RENT = "for_rent"
    SOLD = "sold"


class PropertyType(Enum):
    HOUSE = "HOUSE"
    CONDO = "CONDO"
    TOWNHOUSE = "TOWNHOUSE"
    SINGLE_FAMILY = "SINGLE_FAMILY"
    MULTI_FAMILY = "MULTI_FAMILY"
    MANUFACTURED = "MANUFACTURED"
    APARTMENT = "APARTMENT"
    LAND = "LAND"
    OTHER = "OTHER"

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

        return mapping.get(code, cls.OTHER)


@dataclass
class Address:
    address_one: str
    city: str
    state: str
    zip_code: str

    address_two: str | None = None


@dataclass()
class Realty:
    site_name: SiteName
    address: Address
    url: str
    listing_type: ListingType | None = None


@dataclass
class Property(Realty):
    price: int | None = None
    beds: int | None = None
    baths: float | None = None
    stories: int | None = None
    year_built: int | None = None
    square_feet: int | None = None
    price_per_square_foot: int | None = None
    year_built: int | None = None
    mls_id: str | None = None

    agent_name: str | None = None
    property_type: PropertyType | None = None
    lot_size: int | None = None
    description: str | None = None


@dataclass
class Building(Realty):
    num_units: int | None = None
    min_unit_price: int | None = None
    max_unit_price: int | None = None
    avg_unit_price: int | None = None
