"""
homeharvest.realtor.__init__
~~~~~~~~~~~~

This module implements the scraper for realtor.com
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from json import JSONDecodeError
from typing import Dict, Union, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    wait_exponential,
    stop_after_attempt,
)

from .. import Scraper
from ..models import (
    Property,
    Address,
    ListingType,
    Description,
    PropertyType,
    Agent,
    Broker,
    Builder,
    Advertisers,
    Office,
)
from .queries import GENERAL_RESULTS_QUERY, SEARCH_HOMES_DATA, HOMES_DATA


class RealtorScraper(Scraper):
    SEARCH_GQL_URL = "https://www.realtor.com/api/v1/rdc_search_srp?client_id=rdc-search-new-communities&schema=vesta"
    PROPERTY_URL = "https://www.realtor.com/realestateandhomes-detail/"
    PROPERTY_GQL = "https://graph.realtor.com/graphql"
    ADDRESS_AUTOCOMPLETE_URL = "https://parser-external.geo.moveaws.com/suggest"
    NUM_PROPERTY_WORKERS = 20
    DEFAULT_PAGE_SIZE = 200

    def __init__(self, scraper_input):
        super().__init__(scraper_input)

    def handle_location(self):
        params = {
            "input": self.location,
            "client_id": self.listing_type.value.lower().replace("_", "-"),
            "limit": "1",
            "area_types": "city,state,county,postal_code,address,street,neighborhood,school,school_district,university,park",
        }

        response = self.session.get(
            self.ADDRESS_AUTOCOMPLETE_URL,
            params=params,
        )
        response_json = response.json()

        result = response_json["autocomplete"]

        if not result:
            return None

        return result[0]

    def get_latest_listing_id(self, property_id: str) -> str | None:
        query = """query Property($property_id: ID!) {
                    property(id: $property_id) {
                        listings {
                            listing_id
                            primary
                        }
                    }
                }
                """

        variables = {"property_id": property_id}
        payload = {
            "query": query,
            "variables": variables,
        }

        response = self.session.post(self.SEARCH_GQL_URL, json=payload)
        response_json = response.json()

        property_info = response_json["data"]["property"]
        if property_info["listings"] is None:
            return None

        primary_listing = next(
            (listing for listing in property_info["listings"] if listing["primary"]),
            None,
        )
        if primary_listing:
            return primary_listing["listing_id"]
        else:
            return property_info["listings"][0]["listing_id"]

    def handle_home(self, property_id: str) -> list[Property]:
        query = (
            """query Home($property_id: ID!) {
                    home(property_id: $property_id) %s
                }"""
            % HOMES_DATA
        )

        variables = {"property_id": property_id}
        payload = {
            "query": query,
            "variables": variables,
        }

        response = self.session.post(self.SEARCH_GQL_URL, json=payload)
        response_json = response.json()

        property_info = response_json["data"]["home"]

        return [self.process_property(property_info, "home")]

    @staticmethod
    def process_advertisers(advertisers: list[dict] | None) -> Advertisers | None:
        if not advertisers:
            return None

        def _parse_fulfillment_id(fulfillment_id: str | None) -> str | None:
            return fulfillment_id if fulfillment_id and fulfillment_id != "0" else None

        processed_advertisers = Advertisers()

        for advertiser in advertisers:
            advertiser_type = advertiser.get("type")
            if advertiser_type == "seller":  #: agent
                processed_advertisers.agent = Agent(
                    uuid=_parse_fulfillment_id(advertiser.get("fulfillment_id")),
                    nrds_id=advertiser.get("nrds_id"),
                    mls_set=advertiser.get("mls_set"),
                    name=advertiser.get("name"),
                    email=advertiser.get("email"),
                    phones=advertiser.get("phones"),
                )

                if advertiser.get("broker") and advertiser["broker"].get("name"):  #: has a broker
                    processed_advertisers.broker = Broker(
                        uuid=_parse_fulfillment_id(advertiser["broker"].get("fulfillment_id")),
                        name=advertiser["broker"].get("name"),
                    )

                if advertiser.get("office"):  #: has an office
                    processed_advertisers.office = Office(
                        uuid=_parse_fulfillment_id(advertiser["office"].get("fulfillment_id")),
                        mls_set=advertiser["office"].get("mls_set"),
                        name=advertiser["office"].get("name"),
                        email=advertiser["office"].get("email"),
                        phones=advertiser["office"].get("phones"),
                    )

            if advertiser_type == "community":  #: could be builder
                if advertiser.get("builder"):
                    processed_advertisers.builder = Builder(
                        uuid=_parse_fulfillment_id(advertiser["builder"].get("fulfillment_id")),
                        name=advertiser["builder"].get("name"),
                    )

        return processed_advertisers

    def process_property(self, result: dict, query_name: str) -> Property | None:
        mls = result["source"].get("id") if "source" in result and isinstance(result["source"], dict) else None

        if not mls and self.mls_only:
            return

        able_to_get_lat_long = (
            result
            and result.get("location")
            and result["location"].get("address")
            and result["location"]["address"].get("coordinate")
        )

        is_pending = result["flags"].get("is_pending")
        is_contingent = result["flags"].get("is_contingent")

        if (is_pending or is_contingent) and (self.exclude_pending and self.listing_type != ListingType.PENDING):
            return

        property_id = result["property_id"]
        prop_details = self.get_prop_details(property_id) if self.extra_property_data and query_name != "home" else {}
        if not prop_details:
            prop_details = self.process_extra_property_details(result)

        property_estimates_root = result.get("current_estimates") or result.get("estimates", {}).get("currentValues")
        estimated_value = self.get_key(property_estimates_root, [0, "estimate"])

        advertisers = self.process_advertisers(result.get("advertisers"))

        realty_property = Property(
            mls=mls,
            mls_id=(
                result["source"].get("listing_id")
                if "source" in result and isinstance(result["source"], dict)
                else None
            ),
            property_url=result["href"],
            property_id=property_id,
            listing_id=result.get("listing_id"),
            status=("PENDING" if is_pending else "CONTINGENT" if is_contingent else result["status"].upper()),
            list_price=result["list_price"],
            list_price_min=result["list_price_min"],
            list_price_max=result["list_price_max"],
            list_date=(result["list_date"].split("T")[0] if result.get("list_date") else None),
            prc_sqft=result.get("price_per_sqft"),
            last_sold_date=result.get("last_sold_date"),
            new_construction=result["flags"].get("is_new_construction") is True,
            hoa_fee=(result["hoa"]["fee"] if result.get("hoa") and isinstance(result["hoa"], dict) else None),
            latitude=(result["location"]["address"]["coordinate"].get("lat") if able_to_get_lat_long else None),
            longitude=(result["location"]["address"]["coordinate"].get("lon") if able_to_get_lat_long else None),
            address=self._parse_address(result, search_type="general_search"),
            description=self._parse_description(result),
            neighborhoods=self._parse_neighborhoods(result),
            county=(result["location"]["county"].get("name") if result["location"]["county"] else None),
            fips_code=(result["location"]["county"].get("fips_code") if result["location"]["county"] else None),
            days_on_mls=self.calculate_days_on_mls(result),
            nearby_schools=prop_details.get("schools"),
            assessed_value=prop_details.get("assessed_value"),
            estimated_value=estimated_value if estimated_value else None,
            advertisers=advertisers,
            tax=prop_details.get("tax"),
            tax_history=prop_details.get("tax_history"),
        )
        return realty_property

    def general_search(self, variables: dict, search_type: str) -> Dict[str, Union[int, list[Property]]]:
        """
        Handles a location area & returns a list of properties
        """

        date_param = ""
        if self.listing_type == ListingType.SOLD:
            if self.date_from and self.date_to:
                date_param = f'sold_date: {{ min: "{self.date_from}", max: "{self.date_to}" }}'
            elif self.last_x_days:
                date_param = f'sold_date: {{ min: "$today-{self.last_x_days}D" }}'
        else:
            if self.date_from and self.date_to:
                date_param = f'list_date: {{ min: "{self.date_from}", max: "{self.date_to}" }}'
            elif self.last_x_days:
                date_param = f'list_date: {{ min: "$today-{self.last_x_days}D" }}'

        property_type_param = ""
        if self.property_type:
            property_types = [pt.value for pt in self.property_type]
            property_type_param = f"type: {json.dumps(property_types)}"

        sort_param = (
            "sort: [{ field: sold_date, direction: desc }]"
            if self.listing_type == ListingType.SOLD
            else "sort: [{ field: list_date, direction: desc }]"
        )

        pending_or_contingent_param = (
            "or_filters: { contingent: true, pending: true }" if self.listing_type == ListingType.PENDING else ""
        )

        listing_type = ListingType.FOR_SALE if self.listing_type == ListingType.PENDING else self.listing_type
        is_foreclosure = ""

        if variables.get("foreclosure") is True:
            is_foreclosure = "foreclosure: true"
        elif variables.get("foreclosure") is False:
            is_foreclosure = "foreclosure: false"

        if search_type == "comps":  #: comps search, came from an address
            query = """query Property_search(
                    $coordinates: [Float]!
                    $radius: String!
                    $offset: Int!,
                    ) {
                        home_search(
                            query: {
                                %s
                                nearby: {
                                    coordinates: $coordinates
                                    radius: $radius
                                }
                                status: %s
                                %s
                                %s
                                %s
                            }
                            %s
                            limit: 200
                            offset: $offset
                    ) %s
                }""" % (
                is_foreclosure,
                listing_type.value.lower(),
                date_param,
                property_type_param,
                pending_or_contingent_param,
                sort_param,
                GENERAL_RESULTS_QUERY,
            )
        elif search_type == "area":  #: general search, came from a general location
            query = """query Home_search(
                                $city: String,
                                $county: [String],
                                $state_code: String,
                                $postal_code: String
                                $offset: Int,
                            ) {
                                home_search(
                                    query: {
                                        %s
                                        city: $city
                                        county: $county
                                        postal_code: $postal_code
                                        state_code: $state_code
                                        status: %s
                                        %s
                                        %s
                                        %s
                                    }
                                    %s
                                    limit: 200
                                    offset: $offset
                                ) %s
                            }""" % (
                is_foreclosure,
                listing_type.value.lower(),
                date_param,
                property_type_param,
                pending_or_contingent_param,
                sort_param,
                GENERAL_RESULTS_QUERY,
            )
        else:  #: general search, came from an address
            query = (
                """query Property_search(
                        $property_id: [ID]!
                        $offset: Int!,
                    ) {
                        home_search(
                            query: {
                                property_id: $property_id
                            }
                            limit: 1
                            offset: $offset
                        ) %s
                    }"""
                % GENERAL_RESULTS_QUERY
            )

        payload = {
            "query": query,
            "variables": variables,
        }

        response = self.session.post(self.SEARCH_GQL_URL, json=payload)
        response_json = response.json()
        search_key = "home_search" if "home_search" in query else "property_search"

        properties: list[Property] = []

        if (
            response_json is None
            or "data" not in response_json
            or response_json["data"] is None
            or search_key not in response_json["data"]
            or response_json["data"][search_key] is None
            or "results" not in response_json["data"][search_key]
        ):
            return {"total": 0, "properties": []}

        properties_list = response_json["data"][search_key]["results"]
        total_properties = response_json["data"][search_key]["total"]
        offset = variables.get("offset", 0)

        #: limit the number of properties to be processed
        #: example, if your offset is 200, and your limit is 250, return 50
        properties_list = properties_list[: self.limit - offset]

        with ThreadPoolExecutor(max_workers=self.NUM_PROPERTY_WORKERS) as executor:
            futures = [executor.submit(self.process_property, result, search_key) for result in properties_list]

            for future in as_completed(futures):
                result = future.result()
                if result:
                    properties.append(result)

        return {
            "total": total_properties,
            "properties": properties,
        }

    def search(self):
        location_info = self.handle_location()
        if not location_info:
            return []

        location_type = location_info["area_type"]

        search_variables = {
            "offset": 0,
        }

        search_type = (
            "comps"
            if self.radius and location_type == "address"
            else "address" if location_type == "address" and not self.radius else "area"
        )
        if location_type == "address":
            if not self.radius:  #: single address search, non comps
                property_id = location_info["mpr_id"]
                return self.handle_home(property_id)

            else:  #: general search, comps (radius)
                if not location_info.get("centroid"):
                    return []

                coordinates = list(location_info["centroid"].values())
                search_variables |= {
                    "coordinates": coordinates,
                    "radius": "{}mi".format(self.radius),
                }

        elif location_type == "postal_code":
            search_variables |= {
                "postal_code": location_info.get("postal_code"),
            }

        else:  #: general search, location
            search_variables |= {
                "city": location_info.get("city"),
                "county": location_info.get("county"),
                "state_code": location_info.get("state_code"),
                "postal_code": location_info.get("postal_code"),
            }

        if self.foreclosure:
            search_variables["foreclosure"] = self.foreclosure

        result = self.general_search(search_variables, search_type=search_type)
        total = result["total"]
        homes = result["properties"]

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    self.general_search,
                    variables=search_variables | {"offset": i},
                    search_type=search_type,
                )
                for i in range(
                    self.DEFAULT_PAGE_SIZE,
                    min(total, self.limit),
                    self.DEFAULT_PAGE_SIZE,
                )
            ]

            for future in as_completed(futures):
                homes.extend(future.result()["properties"])

        return homes

    @staticmethod
    def get_key(data: dict, keys: list):
        try:
            value = data
            for key in keys:
                value = value[key]

            return value or {}
        except (KeyError, TypeError, IndexError):
            return {}

    def process_extra_property_details(self, result: dict) -> dict:
        schools = self.get_key(result, ["nearbySchools", "schools"])
        assessed_value = self.get_key(result, ["taxHistory", 0, "assessment", "total"])
        tax_history = self.get_key(result, ["taxHistory"])

        schools = [school["district"]["name"] for school in schools if school["district"].get("name")]

        # Process tax history
        latest_tax = None
        processed_tax_history = None
        if tax_history and isinstance(tax_history, list):
            tax_history = sorted(tax_history, key=lambda x: x.get("year", 0), reverse=True)

            if tax_history and "tax" in tax_history[0]:
                latest_tax = tax_history[0]["tax"]

            processed_tax_history = []
            for entry in tax_history:
                if "year" in entry and "tax" in entry:
                    processed_entry = {
                        "year": entry["year"],
                        "tax": entry["tax"],
                    }
                    if "assessment" in entry and isinstance(entry["assessment"], dict):
                        processed_entry["assessment"] = {
                            "building": entry["assessment"].get("building"),
                            "land": entry["assessment"].get("land"),
                            "total": entry["assessment"].get("total"),
                        }
                    processed_tax_history.append(processed_entry)

        return {
            "schools": schools if schools else None,
            "assessed_value": assessed_value if assessed_value else None,
            "tax": latest_tax,
            "tax_history": processed_tax_history,
        }

    @retry(
        retry=retry_if_exception_type(JSONDecodeError),
        wait=wait_exponential(min=4, max=10),
        stop=stop_after_attempt(3),
    )
    def get_prop_details(self, property_id: str) -> dict:
        if not self.extra_property_data:
            return {}

        query = """query GetHome($property_id: ID!) {
                    home(property_id: $property_id) {
                        __typename

                        nearbySchools: nearby_schools(radius: 5.0, limit_per_level: 3) {
                            __typename schools { district { __typename id name } }
                        }
                        taxHistory: tax_history { __typename tax year assessment { __typename building land total } }
                    }
                }"""

        variables = {"property_id": property_id}
        response = self.session.post(self.SEARCH_GQL_URL, json={"query": query, "variables": variables})

        data = response.json()
        property_details = data["data"]["home"]

        return self.process_extra_property_details(property_details)

    @staticmethod
    def _parse_neighborhoods(result: dict) -> Optional[str]:
        neighborhoods_list = []
        neighborhoods = result["location"].get("neighborhoods", [])

        if neighborhoods:
            for neighborhood in neighborhoods:
                name = neighborhood.get("name")
                if name:
                    neighborhoods_list.append(name)

        return ", ".join(neighborhoods_list) if neighborhoods_list else None

    @staticmethod
    def handle_none_safely(address_part):
        if address_part is None:
            return ""

        return address_part

    @staticmethod
    def _parse_address(result: dict, search_type):
        if search_type == "general_search":
            address = result["location"]["address"]
        else:
            address = result["address"]

        return Address(
            full_line=address.get("line"),
            street=" ".join(
                part
                for part in [
                    address.get("street_number"),
                    address.get("street_direction"),
                    address.get("street_name"),
                    address.get("street_suffix"),
                ]
                if part is not None
            ).strip(),
            unit=address["unit"],
            city=address["city"],
            state=address["state_code"],
            zip=address["postal_code"],
        )

    @staticmethod
    def _parse_description(result: dict) -> Description | None:
        if not result:
            return None

        description_data = result.get("description", {})

        if description_data is None or not isinstance(description_data, dict):
            description_data = {}

        style = description_data.get("type", "")
        if style is not None:
            style = style.upper()

        primary_photo = ""
        if (primary_photo_info := result.get("primary_photo")) and (
            primary_photo_href := primary_photo_info.get("href")
        ):
            primary_photo = primary_photo_href.replace("s.jpg", "od-w480_h360_x2.webp?w=1080&q=75")

        return Description(
            primary_photo=primary_photo,
            alt_photos=RealtorScraper.process_alt_photos(result.get("photos", [])),
            style=(PropertyType.__getitem__(style) if style and style in PropertyType.__members__ else None),
            beds=description_data.get("beds"),
            baths_full=description_data.get("baths_full"),
            baths_half=description_data.get("baths_half"),
            sqft=description_data.get("sqft"),
            lot_sqft=description_data.get("lot_sqft"),
            sold_price=(
                result.get("last_sold_price") or description_data.get("sold_price")
                if result.get("last_sold_date") or result["list_price"] != description_data.get("sold_price")
                else None
            ),  #: has a sold date or list and sold price are different
            year_built=description_data.get("year_built"),
            garage=description_data.get("garage"),
            stories=description_data.get("stories"),
            text=description_data.get("text"),
        )

    @staticmethod
    def calculate_days_on_mls(result: dict) -> Optional[int]:
        list_date_str = result.get("list_date")
        list_date = datetime.strptime(list_date_str.split("T")[0], "%Y-%m-%d") if list_date_str else None
        last_sold_date_str = result.get("last_sold_date")
        last_sold_date = datetime.strptime(last_sold_date_str, "%Y-%m-%d") if last_sold_date_str else None
        today = datetime.now()

        if list_date:
            if result["status"] == "sold":
                if last_sold_date:
                    days = (last_sold_date - list_date).days
                    if days >= 0:
                        return days
            elif result["status"] in ("for_sale", "for_rent"):
                days = (today - list_date).days
                if days >= 0:
                    return days

    @staticmethod
    def process_alt_photos(photos_info: list[dict]) -> list[str] | None:
        if not photos_info:
            return None

        return [
            photo_info["href"].replace("s.jpg", "od-w480_h360_x2.webp?w=1080&q=75")
            for photo_info in photos_info
            if photo_info.get("href")
        ]
