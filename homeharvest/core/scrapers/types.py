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
class Home:
    address: Address
    url: str

    beds: int | None = None
    baths: int | None = None
    stories: int | None = None
    agent_name: str | None = None
    description: str | None = None
    year_built: int | None = None
    square_feet: int | None = None
    price_per_square_foot: int | None = None
    price: int | None = None
    mls_id: str | None = None
