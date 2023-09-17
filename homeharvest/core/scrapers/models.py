from dataclasses import dataclass
from enum import Enum


class ListingType(Enum):
    FOR_SALE = "for_sale"
    FOR_RENT = "for_rent"
    SOLD = "sold"


@dataclass
class Address:
    address_one: str
    city: str
    state: str
    zip_code: str

    address_two: str | None = None


@dataclass
class Property:
    address: Address
    url: str

    beds: int | None = None
    baths: float | None = None
    stories: int | None = None
    agent_name: str | None = None
    year_built: int | None = None
    square_feet: int | None = None
    price_per_square_foot: int | None = None
    year_built: int | None = None
    price: int | None = None
    mls_id: str | None = None

    listing_type: ListingType | None = None
    lot_size: int | None = None
    description: str | None = None


@dataclass
class Building:
    address: Address
    url: str

    num_units: int | None = None
    min_unit_price: int | None = None
    max_unit_price: int | None = None
    avg_unit_price: int | None = None

    listing_type: str | None = None
