"""
homeharvest.realtor.__init__
~~~~~~~~~~~~

This module implements the scraper for relator.com
"""
from ..models import Property, Address, ListingType
from .. import Scraper
from ....exceptions import NoResultsFound
from concurrent.futures import ThreadPoolExecutor, as_completed


class RealtorScraper(Scraper):
    def __init__(self, scraper_input):
        self.counter = 1
        super().__init__(scraper_input)
        self.search_url = (
            "https://www.realtor.com/api/v1/rdc_search_srp?client_id=rdc-search-new-communities&schema=vesta"
        )

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
            "client_id": self.listing_type.value.lower().replace("_", "-"),
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
                            stories
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

        response = self.session.post(self.search_url, json=payload)
        response_json = response.json()

        property_info = response_json["data"]["property"]

        return [
            Property(
                property_url="https://www.realtor.com/realestateandhomes-detail/"
                             + property_info["details"]["permalink"],
                stories=property_info["details"]["stories"],
                mls_id=property_id,
            )
        ]

    def handle_area(self, variables: dict, is_for_comps: bool = False, return_total: bool = False) -> list[
                                                                                                          Property] | int:
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
                                    exterior
                                }
                                source {
                                    id
                                }
                            }
                        }
                    }"""

        sold_date_param = ('sold_date: { min: "$today-%sD" }' % self.sold_last_x_days
                           if self.listing_type == ListingType.SOLD and self.sold_last_x_days is not None
                           else "")

        if not is_for_comps:
            query = (
                    """query Home_search(
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
                                    limit: 200
                                    offset: $offset
                                ) %s"""
                    % (
                        self.listing_type.value.lower(),
                        sold_date_param,
                        results_query
                    )
            )
        else:
            query = (
                    """query Property_search(
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
                            %s
                        }
                        limit: 200
                        offset: $offset
                    ) %s""" % (sold_date_param, results_query))

        payload = {
            "query": query,
            "variables": variables,
        }

        response = self.session.post(self.search_url, json=payload)
        response.raise_for_status()
        response_json = response.json()
        search_key = "home_search" if not is_for_comps else "property_search"

        if return_total:
            return response_json["data"][search_key]["total"]

        properties: list[Property] = []

        if (
                response_json is None
                or "data" not in response_json
                or response_json["data"] is None
                or search_key not in response_json["data"]
                or response_json["data"][search_key] is None
                or "results" not in response_json["data"][search_key]
        ):
            return []

        for result in response_json["data"][search_key]["results"]:
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

            able_to_get_lat_long = result and result.get("location") and result["location"].get("address") and result["location"]["address"].get("coordinate")

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
                hoa_fee=result["hoa"]["fee"] if result.get("hoa") and isinstance(result["hoa"], dict) else None,
                address=Address(
                    street=f"{result['location']['address']['street_number']} {result['location']['address']['street_name']} {result['location']['address']['street_suffix']}",
                    unit=result["location"]["address"]["unit"],
                    city=result["location"]["address"]["city"],
                    state=result["location"]["address"]["state_code"],
                    zip=result["location"]["address"]["postal_code"],
                ),
                yr_blt=result["description"]["year_built"],
                latitude=result["location"]["address"]["coordinate"].get("lat") if able_to_get_lat_long else None,
                longitude=result["location"]["address"]["coordinate"].get("lon") if able_to_get_lat_long else None,
                prkg_gar=result["description"]["garage"],
                stories=result["description"]["stories"],
                neighborhoods=neighborhoods_str,
            )
            properties.append(realty_property)

        return properties

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

        total = self.handle_area(search_variables, return_total=True, is_for_comps=is_for_comps)

        homes = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(
                    self.handle_area,
                    variables=search_variables | {"offset": i},
                    return_total=False,
                    is_for_comps=is_for_comps,
                )
                for i in range(0, total, 200)
            ]

            for future in as_completed(futures):
                homes.extend(future.result())

        return homes
