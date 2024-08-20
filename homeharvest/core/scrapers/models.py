from __future__ import annotations
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
    PENDING = "PENDING"
    SOLD = "SOLD"


@dataclass
class Agent:
    name: str | None = None
    phone: str | None = None


class PropertyType(Enum):
    APARTMENT = "APARTMENT"
    BUILDING = "BUILDING"
    COMMERCIAL = "COMMERCIAL"
    GOVERNMENT = "GOVERNMENT"
    INDUSTRIAL = "INDUSTRIAL"
    CONDO_TOWNHOME = "CONDO_TOWNHOME"
    CONDO_TOWNHOME_ROWHOME_COOP = "CONDO_TOWNHOME_ROWHOME_COOP"
    CONDO = "CONDO"
    CONDOP = "CONDOP"
    CONDOS = "CONDOS"
    COOP = "COOP"
    DUPLEX_TRIPLEX = "DUPLEX_TRIPLEX"
    FARM = "FARM"
    INVESTMENT = "INVESTMENT"
    LAND = "LAND"
    MOBILE = "MOBILE"
    MULTI_FAMILY = "MULTI_FAMILY"
    RENTAL = "RENTAL"
    SINGLE_FAMILY = "SINGLE_FAMILY"
    TOWNHOMES = "TOWNHOMES"
    OTHER = "OTHER"


@dataclass
class Address:
    full_line: str | None = None
    street: str | None = None
    unit: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None


@dataclass
class Description:
    primary_photo: str | None = None
    alt_photos: list[str] | None = None
    style: PropertyType | None = None
    beds: int | None = None
    baths_full: int | None = None
    baths_half: int | None = None
    sqft: int | None = None
    lot_sqft: int | None = None
    sold_price: int | None = None
    year_built: int | None = None
    garage: float | None = None
    stories: int | None = None
    text: str | None = None


@dataclass
class AgentPhone:  #: For documentation purposes only (at the moment)
    number: str | None = None
    type: str | None = None
    primary: bool | None = None
    ext: str | None = None


@dataclass
class Entity:
    name: str
    uuid: str | None = None


@dataclass
class Agent(Entity):
    phones: list[dict] | AgentPhone | None = None
    email: str | None = None
    href: str | None = None


@dataclass
class Office(Entity):
    email: str | None = None
    href: str | None = None
    phones: list[dict] | AgentPhone | None = None


@dataclass
class Broker(Entity):
    pass


@dataclass
class Builder(Entity):
    pass


@dataclass
class Advertisers:
    agent: Agent | None = None
    broker: Broker | None = None
    builder: Builder | None = None
    office: Office | None = None


@dataclass
class Property:
    property_url: str
    mls: str | None = None
    mls_id: str | None = None
    status: str | None = None
    address: Address | None = None

    list_price: int | None = None
    list_price_min: int | None = None
    list_price_max: int | None = None

    list_date: str | None = None
    pending_date: str | None = None
    last_sold_date: str | None = None
    prc_sqft: int | None = None
    new_construction: bool | None = None
    hoa_fee: int | None = None
    days_on_mls: int | None = None
    description: Description | None = None

    latitude: float | None = None
    longitude: float | None = None
    neighborhoods: Optional[str] = None
    county: Optional[str] = None
    fips_code: Optional[str] = None
    nearby_schools: list[str] = None
    assessed_value: int | None = None
    estimated_value: int | None = None

    advertisers: Advertisers | None = None
