"""
homeharvest.realtor.__init__
~~~~~~~~~~~~

This module implements the scraper for realtor.com
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, Union, Optional

from .. import Scraper
from ..models import Property, Address, ListingType, Description, PropertyType, Agent, Broker


class RealtorScraper(Scraper):
    SEARCH_GQL_URL = "https://www.realtor.com/api/v1/rdc_search_srp?client_id=rdc-search-new-communities&schema=vesta"
    PROPERTY_URL = "https://www.realtor.com/realestateandhomes-detail/"
    PROPERTY_GQL = "https://graph.realtor.com/graphql"
    ADDRESS_AUTOCOMPLETE_URL = "https://parser-external.geo.moveaws.com/suggest"
    NUM_PROPERTY_WORKERS = 20

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

    def handle_listing(self, listing_id: str) -> list[Property]:
        query = """query Listing($listing_id: ID!) {
                    listing(id: $listing_id) {
                        source {
                            id
                            listing_id
                        }
                        address {
                            line
                            street_direction
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
                            sqft
                            beds
                            baths_full
                            baths_half
                            lot_sqft
                            sold_price
                            sold_price
                            type
                            price
                            status
                            sold_date
                            list_date
                        }
                        details {
                            year_built
                            stories
                            garage
                            permalink
                        }
                        media {
                            photos {
                                href
                            }
                        }
                    }
                }"""

        variables = {"listing_id": listing_id}
        payload = {
            "query": query,
            "variables": variables,
        }

        response = self.session.post(self.SEARCH_GQL_URL, json=payload)
        response_json = response.json()

        property_info = response_json["data"]["listing"]

        mls = (
            property_info["source"].get("id")
            if "source" in property_info and isinstance(property_info["source"], dict)
            else None
        )

        able_to_get_lat_long = (
            property_info
            and property_info.get("address")
            and property_info["address"].get("location")
            and property_info["address"]["location"].get("coordinate")
        )
        list_date_str = (
            property_info["basic"]["list_date"].split("T")[0] if property_info["basic"].get("list_date") else None
        )
        last_sold_date_str = (
            property_info["basic"]["sold_date"].split("T")[0] if property_info["basic"].get("sold_date") else None
        )
        pending_date_str = property_info["pending_date"].split("T")[0] if property_info.get("pending_date") else None

        list_date = datetime.strptime(list_date_str, "%Y-%m-%d") if list_date_str else None
        last_sold_date = datetime.strptime(last_sold_date_str, "%Y-%m-%d") if last_sold_date_str else None
        pending_date = datetime.strptime(pending_date_str, "%Y-%m-%d") if pending_date_str else None
        today = datetime.now()

        days_on_mls = None
        status = property_info["basic"]["status"].lower()
        if list_date:
            if status == "sold" and last_sold_date:
                days_on_mls = (last_sold_date - list_date).days
            elif status in ("for_sale", "for_rent"):
                days_on_mls = (today - list_date).days
            if days_on_mls and days_on_mls < 0:
                days_on_mls = None

        property_id = property_info["details"]["permalink"]
        prop_details = self.get_prop_details(property_id)
        listing = Property(
            mls=mls,
            mls_id=(
                property_info["source"].get("listing_id")
                if "source" in property_info and isinstance(property_info["source"], dict)
                else None
            ),
            property_url=f"{self.PROPERTY_URL}{property_id}",
            status=property_info["basic"]["status"].upper(),
            list_price=property_info["basic"]["price"],
            list_date=list_date,
            prc_sqft=(
                property_info["basic"].get("price") / property_info["basic"].get("sqft")
                if property_info["basic"].get("price") and property_info["basic"].get("sqft")
                else None
            ),
            last_sold_date=last_sold_date,
            pending_date=pending_date,
            latitude=property_info["address"]["location"]["coordinate"].get("lat") if able_to_get_lat_long else None,
            longitude=property_info["address"]["location"]["coordinate"].get("lon") if able_to_get_lat_long else None,
            address=self._parse_address(property_info, search_type="handle_listing"),
            description=Description(
                alt_photos=self.process_alt_photos(property_info.get("media", {}).get("photos", [])),
                style=property_info["basic"].get("type", "").upper(),
                beds=property_info["basic"].get("beds"),
                baths_full=property_info["basic"].get("baths_full"),
                baths_half=property_info["basic"].get("baths_half"),
                sqft=property_info["basic"].get("sqft"),
                lot_sqft=property_info["basic"].get("lot_sqft"),
                sold_price=property_info["basic"].get("sold_price"),
                year_built=property_info["details"].get("year_built"),
                garage=property_info["details"].get("garage"),
                stories=property_info["details"].get("stories"),
                text=property_info.get("description", {}).get("text"),
            ),
            days_on_mls=days_on_mls,
            agents=prop_details.get("agents"),
            brokers=prop_details.get("brokers"),
            nearby_schools=prop_details.get("schools"),
            assessed_value=prop_details.get("assessed_value"),
            estimated_value=prop_details.get("estimated_value"),
        )

        return [listing]

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
                            line
                            street_direction
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
                        primary_photo {
                            href
                        }
                        photos {
                            href
                        }
                    }
                }"""

        variables = {"property_id": property_id}
        prop_details = self.get_prop_details(property_id)

        payload = {
            "query": query,
            "variables": variables,
        }

        response = self.session.post(self.SEARCH_GQL_URL, json=payload)
        response_json = response.json()

        property_info = response_json["data"]["property"]

        return [
            Property(
                mls_id=property_id,
                property_url=f"{self.PROPERTY_URL}{property_info['details']['permalink']}",
                address=self._parse_address(property_info, search_type="handle_address"),
                description=self._parse_description(property_info),
                agents=prop_details.get("agents"),
                brokers=prop_details.get("brokers"),
                nearby_schools=prop_details.get("schools"),
                assessed_value=prop_details.get("assessed_value"),
                estimated_value=prop_details.get("estimated_value"),
            )
        ]

    def general_search(self, variables: dict, search_type: str) -> Dict[str, Union[int, list[Property]]]:
        """
        Handles a location area & returns a list of properties
        """
        results_query = """{
                            count
                            total
                            results {
                                pending_date
                                property_id
                                list_date
                                status
                                last_sold_price
                                last_sold_date
                                list_price
                                price_per_sqft
                                flags {
                                    is_contingent
                                    is_pending
                                }
                                description {
                                    type
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
                                    text
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
                                        street_direction
                                        street_number
                                        street_name
                                        street_suffix
                                        line
                                        unit
                                        city
                                        state_code
                                        postal_code
                                        coordinate {
                                            lon
                                            lat
                                        }
                                    }
                                    county {
                                        name
                                        fips_code
                                    }
                                    neighborhoods {
                                        name
                                    }
                                }
                                tax_record {
                                    public_record_id
                                }
                                primary_photo {
                                    href
                                }
                                photos {
                                    href
                                }
                            }
                        }
                    }"""

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
                            }
                            %s
                            limit: 200
                            offset: $offset
                    ) %s""" % (
                is_foreclosure,
                listing_type.value.lower(),
                date_param,
                pending_or_contingent_param,
                sort_param,
                results_query,
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
                                    }
                                    %s
                                    limit: 200
                                    offset: $offset
                                ) %s""" % (
                is_foreclosure,
                listing_type.value.lower(),
                date_param,
                pending_or_contingent_param,
                sort_param,
                results_query,
            )
        else:  #: general search, came from an address
            query = (
                """query Property_search(
                        $property_id: [ID]!
                        $offset: Int!,
                    ) {
                        property_search(
                            query: {
                                property_id: $property_id
                            }
                            limit: 1
                            offset: $offset
                        ) %s"""
                % results_query
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

        def process_property(result: dict) -> Property | None:
            mls = result["source"].get("id") if "source" in result and isinstance(result["source"], dict) else None

            if not mls and self.mls_only:
                return

            able_to_get_lat_long = (
                result
                and result.get("location")
                and result["location"].get("address")
                and result["location"]["address"].get("coordinate")
            )

            is_pending = result["flags"].get("is_pending") or result["flags"].get("is_contingent")

            if is_pending and self.listing_type != ListingType.PENDING:
                return

            property_id = result["property_id"]
            prop_details = self.get_prop_details(property_id)

            realty_property = Property(
                mls=mls,
                mls_id=(
                    result["source"].get("listing_id")
                    if "source" in result and isinstance(result["source"], dict)
                    else None
                ),
                property_url=(
                    f"{self.PROPERTY_URL}{property_id}"
                    if self.listing_type != ListingType.FOR_RENT
                    else f"{self.PROPERTY_URL}M{property_id}?listing_status=rental"
                ),
                status="PENDING" if is_pending else result["status"].upper(),
                list_price=result["list_price"],
                list_date=result["list_date"].split("T")[0] if result.get("list_date") else None,
                prc_sqft=result.get("price_per_sqft"),
                last_sold_date=result.get("last_sold_date"),
                hoa_fee=result["hoa"]["fee"] if result.get("hoa") and isinstance(result["hoa"], dict) else None,
                latitude=result["location"]["address"]["coordinate"].get("lat") if able_to_get_lat_long else None,
                longitude=result["location"]["address"]["coordinate"].get("lon") if able_to_get_lat_long else None,
                address=self._parse_address(result, search_type="general_search"),
                description=self._parse_description(result),
                neighborhoods=self._parse_neighborhoods(result),
                county=result["location"]["county"].get("name") if result["location"]["county"] else None,
                fips_code=result["location"]["county"].get("fips_code") if result["location"]["county"] else None,
                days_on_mls=self.calculate_days_on_mls(result),
                agents=prop_details.get("agents"),
                brokers=prop_details.get("brokers"),
                nearby_schools=prop_details.get("schools"),
                assessed_value=prop_details.get("assessed_value"),
                estimated_value=prop_details.get("estimated_value"),
            )
            return realty_property

        with ThreadPoolExecutor(max_workers=self.NUM_PROPERTY_WORKERS) as executor:
            futures = [
                executor.submit(process_property, result) for result in response_json["data"][search_key]["results"]
            ]

            for future in as_completed(futures):
                result = future.result()
                if result:
                    properties.append(result)

        return {
            "total": response_json["data"][search_key]["total"],
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
                search_variables |= {"property_id": property_id}

                gql_results = self.general_search(search_variables, search_type=search_type)
                if gql_results["total"] == 0:
                    listing_id = self.get_latest_listing_id(property_id)
                    if listing_id is None:
                        return self.handle_address(property_id)
                    else:
                        return self.handle_listing(listing_id)
                else:
                    return gql_results["properties"]

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

    def get_prop_details(self, property_id: str) -> dict:
        if not self.extra_property_data:
            return {}

        #: TODO: migrate "advertisers" and "estimates" to general query

        query = """query GetHome($property_id: ID!) {
                    home(property_id: $property_id) {
                        __typename
                
                        advertisers {
                            __typename
                            type
                            name
                            email
                            phones { number type ext primary }
                        }
                        
                        consumer_advertisers {
                            name
                            phone
                            href
                            type
                        }
                
                        nearbySchools: nearby_schools(radius: 5.0, limit_per_level: 3) { 
                            __typename schools { district { __typename id name } } 
                        }  
                        taxHistory: tax_history { __typename tax year assessment { __typename building land total } }
                        estimates { 
                            __typename 
                            currentValues: current_values { 
                                __typename
                                source { __typename type name } 
                                estimate 
                                estimateHigh: estimate_high
                                estimateLow: estimate_low 
                                date 
                                isBestHomeValue: isbest_homevalue 
                            } 
                        }
                    }
                }"""

        variables = {"property_id": property_id}
        response = self.session.post(self.PROPERTY_GQL, json={"query": query, "variables": variables})
        data = response.json()

        def get_key(keys: list):
            try:
                value = data
                for key in keys:
                    value = value[key]

                return value or {}
            except (KeyError, TypeError, IndexError):
                return {}

        agents = get_key(["data", "home", "advertisers"])
        advertisers = get_key(["data", "home", "consumer_advertisers"])

        schools = get_key(["data", "home", "nearbySchools", "schools"])
        assessed_value = get_key(["data", "home", "taxHistory", 0, "assessment", "total"])
        estimated_value = get_key(["data", "home", "estimates", "currentValues", 0, "estimate"])

        agents = [Agent(
            name=ad["name"],
            email=ad["email"],
            phones=ad["phones"]
        ) for ad in agents]

        brokers = [Broker(
            name=ad["name"],
            phone=ad["phone"],
            website=ad["href"]
        ) for ad in advertisers if ad.get("type") != "Agent"]

        schools = [school["district"]["name"] for school in schools if school['district'].get('name')]
        return {
            "agents": agents if agents else None,
            "brokers": brokers if brokers else None,
            "schools": schools if schools else None,
            "assessed_value": assessed_value if assessed_value else None,
            "estimated_value": estimated_value if estimated_value else None,
        }

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
                part for part in [
                    address.get("street_number"),
                    address.get("street_direction"),
                    address.get("street_name"),
                    address.get("street_suffix"),
                ] if part is not None
            ).strip(),
            unit=address["unit"],
            city=address["city"],
            state=address["state_code"],
            zip=address["postal_code"],
        )

    @staticmethod
    def _parse_description(result: dict) -> Description:
        description_data = result.get("description", {})

        if description_data is None or not isinstance(description_data, dict):
            description_data = {}

        style = description_data.get("type", "")
        if style is not None:
            style = style.upper()

        primary_photo = ""
        if result and "primary_photo" in result:
            primary_photo_info = result["primary_photo"]
            if primary_photo_info and "href" in primary_photo_info:
                primary_photo_href = primary_photo_info["href"]
                primary_photo = primary_photo_href.replace("s.jpg", "od-w480_h360_x2.webp?w=1080&q=75")

        return Description(
            primary_photo=primary_photo,
            alt_photos=RealtorScraper.process_alt_photos(result.get("photos")),
            style=PropertyType(style) if style else None,
            beds=description_data.get("beds"),
            baths_full=description_data.get("baths_full"),
            baths_half=description_data.get("baths_half"),
            sqft=description_data.get("sqft"),
            lot_sqft=description_data.get("lot_sqft"),
            sold_price=description_data.get("sold_price") if result.get('last_sold_date') or result["list_price"] != description_data.get("sold_price") else None,  #: has a sold date or list and sold price are different
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
    def process_alt_photos(photos_info):
        try:
            alt_photos = []
            if photos_info:
                for photo_info in photos_info:
                    href = photo_info.get("href", "")
                    alt_photo_href = href.replace("s.jpg", "od-w480_h360_x2.webp?w=1080&q=75")
                    alt_photos.append(alt_photo_href)
            return alt_photos
        except Exception:
            pass
