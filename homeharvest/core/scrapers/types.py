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
