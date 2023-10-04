"""
homeharvest.realtor.__init__
~~~~~~~~~~~~

This module implements the scraper for relator.com
"""
from typing import Dict, Union
from ..models import Property, Address
from .. import Scraper
from ....exceptions import NoResultsFound
from concurrent.futures import ThreadPoolExecutor, as_completed


class RealtorScraper(Scraper):
    def __init__(self, scraper_input):
        self.counter = 1
        super().__init__(scraper_input)
        self.endpoint = "https://www.realtor.com/api/v1/rdc_search_srp?client_id=rdc-search-new-communities&schema=vesta"

    def handle_location(self):
        headers = {
            "authority": "parser-external.geo.moveaws.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://www.realtor.com",
            "referer": "https://www.realtor.com/",
            "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        }

        params = {
            "input": self.location,
            "client_id": self.listing_type.lower().replace("_", "-"),
            "limit": "1",
            "area_types": "city,state,county,postal_code,address,street,neighborhood,school,school_district,university,park",
        }

        response = self.session.get(
            "https://parser-external.geo.moveaws.com/suggest",
            params=params,
            headers=headers,
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
                        }
                        address {
                            address_validation_code
                            city
                            country
                            county
                            line
                            postal_code
                            state_code
                            street_direction
                            street_name
                            street_number
                            street_suffix
                            street_post_direction
                            unit_value
                            unit
                            unit_descriptor
                            zip
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

        response = self.session.post(self.endpoint, json=payload)
        response_json = response.json()

        property_info = response_json["data"]["property"]

        return [
            Property(
                property_url="https://www.realtor.com/realestateandhomes-detail/"
                + property_info["details"]["permalink"],
                address=Address(
                    street=f"{property_info['address']['street_number']} {property_info['address']['street_name']} {property_info['address']['street_suffix']}",
                    unit=property_info["address"]["unit_value"],
                    city=property_info["address"]["city"],
                    state=property_info["address"]["state_code"],
                    zip=property_info["address"]["postal_code"],
                ),
                yr_blt=property_info["details"]["year_built"],
                prc_sqft=property_info["basic"]["price"]
                // property_info["basic"]["sqft"]
                if property_info["basic"]["sqft"] is not None
                and property_info["basic"]["price"] is not None
                else None,
                status=self.status.upper(),
                beds=property_info["basic"]["beds"],
                baths_full=property_info["basic"]["baths"],
                lot_sf=property_info["basic"]["lot_sqft"],
                est_sf=property_info["basic"]["sqft"],
                list_price=property_info["basic"]["price"],
                sold_price=property_info["basic"]["sold_price"],
            )
        ]

    def handle_area(self, variables: dict) -> Dict[str, Union[int, list[Property]]]:
        """
        Handles a location area & returns a list of properties
        """
        query = """query Home_search(
                            $city: String,
                            $county: [String],
                            $state_code: String,
                            $postal_code: String,
                            $offset: Int
                        ) {
                            home_search(
                                query: {
                                    city: $city
                                    county: $county
                                    postal_code: $postal_code
                                    state_code: $state_code
                                    status: %s
                                    sold_date: {
                                        min: %s
                                    }
                                }
                                limit: 200
                                offset: $offset
                                sort: [
                        {
                            field: sold_date,
                            direction: desc 
                        }
                    ]
                            ) {
                                count
                                total
                                results {
                                    property_id
                                    list_date
                                    status
                                    last_sold_price
                                    last_sold_date
                                    hoa {
                                    fee
                                    }
                                    description {
                                        baths_full
                                        baths_half
                                        beds
                                        lot_sqft
                                        sqft
                                        sold_price
                                        year_built
                                        garage
                                        sold_price
                                        type
                                        sub_type
                                        name
                                        stories
                                    }
                                    source {
                                        raw {
                                            area
                                            status
                                            style
                                        }
                                        last_update_date
                                        contract_date
                                        id
                                        listing_id
                                        name
                                        type
                                        listing_href
                                        community_id
                                        management_id
                                        corporation_id
                                        subdivision_status
                                        spec_id
                                        plan_id
                                        tier_rank
                                        feed_type
                                    }
                                    location {
                                        address {
                                            city
                                            country
                                            line
                                            postal_code
                                            state_code
                                            state
                                            coordinate {
                                                lon
                                                lat
                                            }
                                            street_direction
                                            street_name
                                            street_number
                                            street_post_direction
                                            street_suffix
                                            unit
                                        }
                                        neighborhoods {
                                        name
                                        }
                                    }
                                    list_price
                                    price_per_sqft
                                                                        style_category_tags {
                                                                        exterior}

                                    source {
                                        id
                                    }
                                }
                            }
                        }""" % (
            self.status,
            f'"$nowUTC-{self.timeframe}"',
        )
        payload = {
            "query": self.get_query(),
            "variables": variables,
        }
        response = self.session.post(self.endpoint, json=payload)
        response.raise_for_status()
        response_json = response.json()

        properties: list[Property] = []

        if (
            response_json is None
            or "data" not in response_json
            or response_json["data"] is None
            or "home_search" not in response_json["data"]
            or response_json["data"]["home_search"] is None
            or "results" not in response_json["data"]["home_search"]
        ):
            return {"total": 0, "properties": []}

        for result in response_json["data"]["home_search"]["results"]:
            self.counter += 1
            mls = (
                result["source"].get("id")
                if "source" in result and isinstance(result["source"], dict)
                else None
            )
            mls_id = (
                result["source"].get("listing_id")
                if "source" in result and isinstance(result["source"], dict)
                else None
            )

            if not mls_id:
                continue
                # not type

            neighborhoods_list = []
            neighborhoods = result["location"].get("neighborhoods", [])

            if neighborhoods:
                for neighborhood in neighborhoods:
                    name = neighborhood.get("name")
                    if name:
                        neighborhoods_list.append(name)

            neighborhoods_str = (
                ", ".join(neighborhoods_list) if neighborhoods_list else None
            )

            realty_property = Property(
                property_url="https://www.realtor.com/realestateandhomes-detail/"
                + result["property_id"],
                mls=mls,
                mls_id=mls_id,
                status=result["status"].upper(),
                style=result["description"]["type"].upper(),
                beds=result["description"]["beds"],
                baths_full=result["description"]["baths_full"],
                baths_half=result["description"]["baths_half"],
                est_sf=result["description"]["sqft"],
                lot_sf=result["description"]["lot_sqft"],
                list_price=result["list_price"],
                list_date=result["list_date"].split("T")[0]
                if result["list_date"]
                else None,
                sold_price=result["description"]["sold_price"],
                prc_sqft=result["price_per_sqft"],
                last_sold_date=result["last_sold_date"],
                hoa_fee=result["hoa"]["fee"]
                if result.get("hoa") and isinstance(result["hoa"], dict)
                else None,
                address=Address(
                    street=f"{result['location']['address']['street_number']} {result['location']['address']['street_name']} {result['location']['address']['street_suffix']}",
                    unit=result["location"]["address"]["unit"],
                    city=result["location"]["address"]["city"],
                    state=result["location"]["address"]["state_code"],
                    zip=result["location"]["address"]["postal_code"],
                ),
                yr_blt=result["description"]["year_built"],
                latitude=result["location"]["address"]["coordinate"]["lat"]
                if result
                and result.get("location")
                and result["location"].get("address")
                and result["location"]["address"].get("coordinate")
                and "lat" in result["location"]["address"]["coordinate"]
                else None,
                longitude=result["location"]["address"]["coordinate"]["lon"]
                if result
                and result.get("location")
                and result["location"].get("address")
                and result["location"]["address"].get("coordinate")
                and "lon" in result["location"]["address"]["coordinate"]
                else None,
                prkg_gar=result["description"]["garage"],
                stories=result["description"]["stories"],
                neighborhoods=neighborhoods_str,
            )
            properties.append(realty_property)

        return {
            "total": response_json["data"]["home_search"]["total"],
            "properties": properties,
        }

    def get_query(self):
        if self.status == "sold":
            return """query Home_search(
                                    $city: String,
                                    $county: [String],
                                    $state_code: String,
                                    $postal_code: String,
                                    $offset: Int
                                ) {
                                    home_search(
                                        query: {
                                            city: $city
                                            county: $county
                                            postal_code: $postal_code
                                            state_code: $state_code
                                            status: %s
                                            sold_date: {
                                                min: %s
                                            }
                                        }
                                        limit: 200
                                        offset: $offset
                                        sort: [
                                {
                                    field: sold_date,
                                    direction: desc 
                                }
                            ]
                                    ) {
                                        count
                                        total
                                        results {
                                            property_id
                                            list_date
                                            status
                                            last_sold_price
                                            last_sold_date
                                            hoa {
                                            fee
                                            }
                                            description {
                                                baths_full
                                                baths_half
                                                beds
                                                lot_sqft
                                                sqft
                                                sold_price
                                                year_built
                                                garage
                                                sold_price
                                                type
                                                sub_type
                                                name
                                                stories
                                            }
                                            source {
                                                raw {
                                                    area
                                                    status
                                                    style
                                                }
                                                last_update_date
                                                contract_date
                                                id
                                                listing_id
                                                name
                                                type
                                                listing_href
                                                community_id
                                                management_id
                                                corporation_id
                                                subdivision_status
                                                spec_id
                                                plan_id
                                                tier_rank
                                                feed_type
                                            }
                                            location {
                                                address {
                                                    city
                                                    country
                                                    line
                                                    postal_code
                                                    state_code
                                                    state
                                                    coordinate {
                                                        lon
                                                        lat
                                                    }
                                                    street_direction
                                                    street_name
                                                    street_number
                                                    street_post_direction
                                                    street_suffix
                                                    unit
                                                }
                                                neighborhoods {
                                                name
                                                }
                                            }
                                            list_price
                                            price_per_sqft
                                                                                style_category_tags {
                                                                                exterior}

                                            source {
                                                id
                                            }
                                        }
                                    }
                                }""" % (
                self.status,
                f'"$nowUTC-{self.timeframe}"',
            )
        else:
            return """query Home_search(
                                    $city: String,
                                    $county: [String],
                                    $state_code: String,
                                    $postal_code: String,
                                    $offset: Int
                                ) {
                                    home_search(
                                        query: {
                                            city: $city
                                            county: $county
                                            postal_code: $postal_code
                                            state_code: $state_code
                                            status: %s
                                        }
                                        limit: 200
                                        offset: $offset
                                        sort: [
                                {
                                    field: sold_date,
                                    direction: desc 
                                }
                            ]
                                    ) {
                                        count
                                        total
                                        results {
                                            property_id
                                            list_date
                                            status
                                            last_sold_price
                                            last_sold_date
                                            hoa {
                                            fee
                                            }
                                            description {
                                                baths_full
                                                baths_half
                                                beds
                                                lot_sqft
                                                sqft
                                                sold_price
                                                year_built
                                                garage
                                                sold_price
                                                type
                                                sub_type
                                                name
                                                stories
                                            }
                                            source {
                                                raw {
                                                    area
                                                    status
                                                    style
                                                }
                                                last_update_date
                                                contract_date
                                                id
                                                listing_id
                                                name
                                                type
                                                listing_href
                                                community_id
                                                management_id
                                                corporation_id
                                                subdivision_status
                                                spec_id
                                                plan_id
                                                tier_rank
                                                feed_type
                                            }
                                            location {
                                                address {
                                                    city
                                                    country
                                                    line
                                                    postal_code
                                                    state_code
                                                    state
                                                    coordinate {
                                                        lon
                                                        lat
                                                    }
                                                    street_direction
                                                    street_name
                                                    street_number
                                                    street_post_direction
                                                    street_suffix
                                                    unit
                                                }
                                                neighborhoods {
                                                name
                                                }
                                            }
                                            list_price
                                            price_per_sqft
                                                                                style_category_tags {
                                                                                exterior}

                                            source {
                                                id
                                            }
                                        }
                                    }
                                }""" % (
                self.status,
            )

    def search(self):
        location_info = self.handle_location()
        location_type = location_info["area_type"]
        is_for_comps = self.radius is not None and location_type == "address"

        if location_type == "address" and not is_for_comps:
            property_id = location_info["mpr_id"]
            return self.handle_address(property_id)

        offset = 0

        if not is_for_comps:
            search_variables = {
                "city": location_info.get("city"),
                "county": location_info.get("county"),
                "state_code": location_info.get("state_code"),
                "postal_code": location_info.get("postal_code"),
                "offset": offset,
            }
        else:
            coordinates = list(location_info["centroid"].values())
            search_variables = {
                "coordinates": coordinates,
                "radius": "{}mi".format(self.radius),
                "offset": offset,
            }

        result = self.handle_area(search_variables)
        total = result["total"]
        homes = result["properties"]

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(
                    self.handle_area,
                    variables=search_variables | {"offset": i},
                )
                for i in range(200, min(total, 10000), 200)
            ]

            for future in as_completed(futures):
                homes.extend(future.result()["properties"])

        return homes
