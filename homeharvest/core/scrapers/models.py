from dataclasses import dataclass
from enum import Enum
from typing import Optional


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


@dataclass
class Address:
    street: str | None = None
    unit: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None


@dataclass
class Agent:
    name: str
    phone: str | None = None
    email: str | None = None


@dataclass
class Property:
    property_url: str | None = None
    mls: str | None = None
    mls_id: str | None = None
    status: str | None = None
    style: str | None = None

    beds: int | None = None
    baths_full: int | None = None
    baths_half: int | None = None
    list_price: int | None = None
    list_date: str | None = None
    sold_price: int | None = None
    last_sold_date: str | None = None
    prc_sqft: float | None = None
    est_sf: int | None = None
    lot_sf: int | None = None
    hoa_fee: int | None = None

    address: Address | None = None

    yr_blt: int | None = None
    latitude: float | None = None
    longitude: float | None = None

    stories: int | None = None
    prkg_gar: float | None = None

    neighborhoods: Optional[str] = None
