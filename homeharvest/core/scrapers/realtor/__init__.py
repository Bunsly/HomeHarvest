"""
homeharvest.realtor.__init__
~~~~~~~~~~~~

This module implements the scraper for realtor.com
"""
from typing import Dict, Union, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .. import Scraper
from ....exceptions import NoResultsFound
from ..models import Property, Address, ListingType, Description


class RealtorScraper(Scraper):
    SEARCH_URL = "https://www.realtor.com/api/v1/rdc_search_srp?client_id=rdc-search-new-communities&schema=vesta"
    PROPERTY_URL = "https://www.realtor.com/realestateandhomes-detail/"
    ADDRESS_AUTOCOMPLETE_URL = "https://parser-external.geo.moveaws.com/suggest"

    def __init__(self, scraper_input):
        self.counter = 1
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
            raise NoResultsFound("No results found for location: " + self.location)

        return result[0]

    def handle_address(self, property_id: str) -> list[Property]:
        """
        Handles a specific address & returns one property
        """
        query = """query Property($property_id: ID!) {
                    property(id: $property_id) {
                        property_id
                        details {
                            date_updated
                            garage
                            permalink
                            year_built
                            stories
                        }
                        address {
                            street_number
                            street_name
                            street_suffix
                            unit
                            city
                            state_code
                            postal_code
                            location {
                                coordinate {
                                    lat
                                    lon
                                }
                            }
                        }
                        basic {
                            baths
                            beds
                            price
                            sqft
                            lot_sqft
                            type
                            sold_price
                        }
                        public_record {
                            lot_size
                            sqft
                            stories
                            units
                            year_built
                        }
                    }
                }"""

        variables = {"property_id": property_id}

        payload = {
            "query": query,
            "variables": variables,
        }

        response = self.session.post(self.SEARCH_URL, json=payload)
        response_json = response.json()

        property_info = response_json["data"]["property"]

        return [
            Property(
                mls_id=property_id,
                property_url=f"{self.PROPERTY_URL}{property_info['details']['permalink']}",
                address=self._parse_address(
                    property_info, search_type="handle_address"
                ),
                description=self._parse_description(property_info),
            )
        ]

    def general_search(
        self, variables: dict, search_type: str
    ) -> Dict[str, Union[int, list[Property]]]:
        """
        Handles a location area & returns a list of properties
        """
        results_query = """{
                            count
                            total
                            results {
                                property_id
                                list_date
                                status
                                last_sold_price
                                last_sold_date
                                list_price
                                price_per_sqft
                                description {
                                    sqft
                                    beds
                                    baths_full
                                    baths_half
                                    lot_sqft
                                    sold_price
                                    year_built
                                    garage
                                    sold_price
                                    type
                                    name
                                    stories
                                }
                                source {
                                    id
                                    listing_id
                                }
                                hoa {
                                    fee
                                }
                                location {
                                    address {
                                        street_number
                                        street_name
                                        street_suffix
                                        unit
                                        city
                                        state_code
                                        postal_code
                                        coordinate {
                                            lon
                                            lat
                                        }
                                    }
                                    neighborhoods {
                                        name
                                    }
                                }
                            }
                        }
                    }"""

        date_param = (
            'sold_date: { min: "$today-%sD" }' % self.last_x_days
            if self.listing_type == ListingType.SOLD and self.last_x_days
            else (
                'list_date: { min: "$today-%sD" }' % self.last_x_days
                if self.last_x_days
                else ""
            )
        )
        sort_param = (
            "sort: [{ field: sold_date, direction: desc }]"
            if self.listing_type == ListingType.SOLD
            else "sort: [{ field: list_date, direction: desc }]"
        )

        if search_type == "comps":
            query = """query Property_search(
                    $coordinates: [Float]!
                    $radius: String!
                    $offset: Int!,
                    ) {
                        property_search(
                            query: { 
                                nearby: {
                                    coordinates: $coordinates
                                    radius: $radius 
                                }
                                status: %s
                                %s
                            }
                            %s
                            limit: 200
                            offset: $offset
                    ) %s""" % (
                self.listing_type.value.lower(),
                date_param,
                sort_param,
                results_query,
            )
        else:
            query = """query Home_search(
                                $city: String,
                                $county: [String],
                                $state_code: String,
                                $postal_code: String
                                $offset: Int,
                            ) {
                                home_search(
                                    query: {
                                        city: $city
                                        county: $county
                                        postal_code: $postal_code
                                        state_code: $state_code
                                        status: %s
                                        %s
                                    }
                                    %s
                                    limit: 200
                                    offset: $offset
                                ) %s""" % (
                self.listing_type.value.lower(),
                date_param,
                sort_param,
                results_query,
            )

        payload = {
            "query": query,
            "variables": variables,
        }

        response = self.session.post(self.SEARCH_URL, json=payload)
        response.raise_for_status()
        response_json = response.json()
        search_key = "property_search" if search_type == "comps" else "home_search"

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

        for result in response_json["data"][search_key]["results"]:
            self.counter += 1
            mls = (
                result["source"].get("id")
                if "source" in result and isinstance(result["source"], dict)
                else None
            )

            if not mls and self.mls_only:
                continue

            able_to_get_lat_long = (
                result
                and result.get("location")
                and result["location"].get("address")
                and result["location"]["address"].get("coordinate")
            )

            realty_property = Property(
                mls=mls,
                mls_id=result["source"].get("listing_id")
                if "source" in result and isinstance(result["source"], dict)
                else None,
                property_url=f"{self.PROPERTY_URL}{result['property_id']}",
                status=result["status"].upper(),
                list_price=result["list_price"],
                list_date=result["list_date"].split("T")[0]
                if result.get("list_date")
                else None,
                prc_sqft=result.get("price_per_sqft"),
                last_sold_date=result.get("last_sold_date"),
                hoa_fee=result["hoa"]["fee"]
                if result.get("hoa") and isinstance(result["hoa"], dict)
                else None,
                latitude=result["location"]["address"]["coordinate"].get("lat")
                if able_to_get_lat_long
                else None,
                longitude=result["location"]["address"]["coordinate"].get("lon")
                if able_to_get_lat_long
                else None,
                address=self._parse_address(result, search_type="general_search"),
                neighborhoods=self._parse_neighborhoods(result),
                description=self._parse_description(result),
            )
            properties.append(realty_property)

        return {
            "total": response_json["data"][search_key]["total"],
            "properties": properties,
        }

    def search(self):
        location_info = self.handle_location()
        location_type = location_info["area_type"]

        search_variables = {
            "offset": 0,
        }

        search_type = "comps" if self.radius and location_type == "address" else "area"
        if location_type == "address":
            if not self.radius:  #: single address search, non comps
                property_id = location_info["mpr_id"]
                search_variables |= {"property_id": property_id}
                return self.handle_address(property_id)

            else:  #: general search, comps (radius)
                coordinates = list(location_info["centroid"].values())
                search_variables |= {
                    "coordinates": coordinates,
                    "radius": "{}mi".format(self.radius),
                }

        else:  #: general search, location
            search_variables |= {
                "city": location_info.get("city"),
                "county": location_info.get("county"),
                "state_code": location_info.get("state_code"),
                "postal_code": location_info.get("postal_code"),
            }

        result = self.general_search(search_variables, search_type=search_type)
        total = result["total"]
        homes = result["properties"]

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(
                    self.general_search,
                    variables=search_variables | {"offset": i},
                    search_type=search_type,
                )
                for i in range(200, min(total, 10000), 200)
            ]

            for future in as_completed(futures):
                homes.extend(future.result()["properties"])

        return homes

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
    def _parse_address(result: dict, search_type):
        if search_type == "general_search":
            return Address(
                street=f"{result['location']['address']['street_number']} {result['location']['address']['street_name']} {result['location']['address']['street_suffix']}",
                unit=result["location"]["address"]["unit"],
                city=result["location"]["address"]["city"],
                state=result["location"]["address"]["state_code"],
                zip=result["location"]["address"]["postal_code"],
            )
        return Address(
            street=f"{result['address']['street_number']} {result['address']['street_name']} {result['address']['street_suffix']}",
            unit=result["address"]["unit"],
            city=result["address"]["city"],
            state=result["address"]["state_code"],
            zip=result["address"]["postal_code"],
        )

    @staticmethod
    def _parse_description(result: dict) -> Description:
        description_data = result.get("description", {})
        return Description(
            style=description_data.get("type", "").upper(),
            beds=description_data.get("beds"),
            baths_full=description_data.get("baths_full"),
            baths_half=description_data.get("baths_half"),
            sqft=description_data.get("sqft"),
            lot_sqft=description_data.get("lot_sqft"),
            sold_price=description_data.get("sold_price"),
            year_built=description_data.get("year_built"),
            garage=description_data.get("garage"),
            stories=description_data.get("stories"),
        )
