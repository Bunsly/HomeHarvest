"""
homeharvest.redfin.__init__
~~~~~~~~~~~~

This module implements the scraper for redfin.com
"""
import json
from typing import Any
from .. import Scraper
from ....utils import parse_address_two, parse_address_one
from ..models import Property, Address, PropertyType, ListingType, SiteName
from ....exceptions import NoResultsFound


class RedfinScraper(Scraper):
    def __init__(self, scraper_input):
        super().__init__(scraper_input)
        self.listing_type = scraper_input.listing_type

    def _handle_location(self):
        url = "https://www.redfin.com/stingray/do/location-autocomplete?v=2&al=1&location={}".format(self.location)

        response = self.session.get(url)
        response_json = json.loads(response.text.replace("{}&&", ""))

        def get_region_type(match_type: str):
            if match_type == "4":
                return "2"  #: zip
            elif match_type == "2":
                return "6"  #: city
            elif match_type == "1":
                return "address"  #: address, needs to be handled differently

        if "exactMatch" not in response_json["payload"]:
            raise NoResultsFound("No results found for location: {}".format(self.location))

        if response_json["payload"]["exactMatch"] is not None:
            target = response_json["payload"]["exactMatch"]
        else:
            target = response_json["payload"]["sections"][0]["rows"][0]

        return target["id"].split("_")[1], get_region_type(target["type"])

    def _parse_home(self, home: dict, single_search: bool = False) -> Property:
        def get_value(key: str) -> Any | None:
            if key in home and "value" in home[key]:
                return home[key]["value"]

        if not single_search:
            address = Address(
                address_one=parse_address_one(get_value("streetLine"))[0],
                address_two=parse_address_one(get_value("streetLine"))[1],
                city=home.get("city"),
                state=home.get("state"),
                zip_code=home.get("zip"),
            )
        else:
            address_info = home.get("streetAddress")
            address_one, address_two = parse_address_one(address_info.get("assembledAddress"))

            address = Address(
                address_one=address_one,
                address_two=address_two,
                city=home.get("city"),
                state=home.get("state"),
                zip_code=home.get("zip"),
            )

        url = "https://www.redfin.com{}".format(home["url"])
        lot_size_data = home.get("lotSize")

        if not isinstance(lot_size_data, int):
            lot_size = lot_size_data.get("value", None) if isinstance(lot_size_data, dict) else None
        else:
            lot_size = lot_size_data

        return Property(
            site_name=self.site_name,
            listing_type=self.listing_type,
            address=address,
            property_url=url,
            beds_min=home["beds"] if "beds" in home else None,
            beds_max=home["beds"] if "beds" in home else None,
            baths_min=home["baths"] if "baths" in home else None,
            baths_max=home["baths"] if "baths" in home else None,
            price_min=get_value("price"),
            price_max=get_value("price"),
            sqft_min=get_value("sqFt"),
            sqft_max=get_value("sqFt"),
            stories=home["stories"] if "stories" in home else None,
            agent_name=get_value("listingAgent"),
            description=home["listingRemarks"] if "listingRemarks" in home else None,
            year_built=get_value("yearBuilt") if not single_search else home.get("yearBuilt"),
            lot_area_value=lot_size,
            property_type=PropertyType.from_int_code(home.get("propertyType")),
            price_per_sqft=get_value("pricePerSqFt") if type(home.get("pricePerSqFt")) != int else home.get("pricePerSqFt"),
            mls_id=get_value("mlsId"),
            latitude=home["latLong"]["latitude"] if "latLong" in home and "latitude" in home["latLong"] else None,
            longitude=home["latLong"]["longitude"] if "latLong" in home and "longitude" in home["latLong"] else None,
        )

    def _handle_rentals(self, region_id, region_type):
        url = f"https://www.redfin.com/stingray/api/v1/search/rentals?al=1&isRentals=true&region_id={region_id}&region_type={region_type}&num_homes=100000"

        response = self.session.get(url)
        response.raise_for_status()
        homes = response.json()

        properties_list = []

        for home in homes["homes"]:
            home_data = home["homeData"]
            rental_data = home["rentalExtension"]

            property_url = f"https://www.redfin.com{home_data.get('url', '')}"
            address_info = home_data.get("addressInfo", {})
            centroid = address_info.get("centroid", {}).get("centroid", {})
            address = Address(
                address_one=parse_address_one(address_info.get("formattedStreetLine"))[0],
                city=address_info.get("city"),
                state=address_info.get("state"),
                zip_code=address_info.get("zip"),
            )

            price_range = rental_data.get("rentPriceRange", {"min": None, "max": None})
            bed_range = rental_data.get("bedRange", {"min": None, "max": None})
            bath_range = rental_data.get("bathRange", {"min": None, "max": None})
            sqft_range = rental_data.get("sqftRange", {"min": None, "max": None})

            property_ = Property(
                property_url=property_url,
                site_name=SiteName.REDFIN,
                listing_type=ListingType.FOR_RENT,
                address=address,
                description=rental_data.get("description"),
                latitude=centroid.get("latitude"),
                longitude=centroid.get("longitude"),
                baths_min=bath_range.get("min"),
                baths_max=bath_range.get("max"),
                beds_min=bed_range.get("min"),
                beds_max=bed_range.get("max"),
                price_min=price_range.get("min"),
                price_max=price_range.get("max"),
                sqft_min=sqft_range.get("min"),
                sqft_max=sqft_range.get("max"),
                img_src=home_data.get("staticMapUrl"),
                posted_time=rental_data.get("lastUpdated"),
                bldg_name=rental_data.get("propertyName"),
            )

            properties_list.append(property_)

        if not properties_list:
            raise NoResultsFound("No rentals found for the given location.")

        return properties_list

    def _parse_building(self, building: dict) -> Property:
        street_address = " ".join(
            [
                building["address"]["streetNumber"],
                building["address"]["directionalPrefix"],
                building["address"]["streetName"],
                building["address"]["streetType"],
            ]
        )
        return Property(
            site_name=self.site_name,
            property_type=PropertyType("BUILDING"),
            address=Address(
                address_one=parse_address_one(street_address)[0],
                city=building["address"]["city"],
                state=building["address"]["stateOrProvinceCode"],
                zip_code=building["address"]["postalCode"],
                address_two=parse_address_two(
                    " ".join(
                        [
                            building["address"]["unitType"],
                            building["address"]["unitValue"],
                        ]
                    )
                ),
            ),
            property_url="https://www.redfin.com{}".format(building["url"]),
            listing_type=self.listing_type,
            unit_count=building.get("numUnitsForSale"),
        )

    def handle_address(self, home_id: str):
        """
        EPs:
        https://www.redfin.com/stingray/api/home/details/initialInfo?al=1&path=/TX/Austin/70-Rainey-St-78701/unit-1608/home/147337694
        https://www.redfin.com/stingray/api/home/details/mainHouseInfoPanelInfo?propertyId=147337694&accessLevel=3
        https://www.redfin.com/stingray/api/home/details/aboveTheFold?propertyId=147337694&accessLevel=3
        https://www.redfin.com/stingray/api/home/details/belowTheFold?propertyId=147337694&accessLevel=3
        """
        url = "https://www.redfin.com/stingray/api/home/details/aboveTheFold?propertyId={}&accessLevel=3".format(
            home_id
        )

        response = self.session.get(url)
        response_json = json.loads(response.text.replace("{}&&", ""))

        parsed_home = self._parse_home(response_json["payload"]["addressSectionInfo"], single_search=True)
        return [parsed_home]

    def search(self):
        region_id, region_type = self._handle_location()

        if region_type == "address":
            home_id = region_id
            return self.handle_address(home_id)

        if self.listing_type == ListingType.FOR_RENT:
            return self._handle_rentals(region_id, region_type)
        else:
            if self.listing_type == ListingType.FOR_SALE:
                url = f"https://www.redfin.com/stingray/api/gis?al=1&region_id={region_id}&region_type={region_type}&num_homes=100000"
            else:
                url = f"https://www.redfin.com/stingray/api/gis?al=1&region_id={region_id}&region_type={region_type}&sold_within_days=30&num_homes=100000"
            response = self.session.get(url)
            response_json = json.loads(response.text.replace("{}&&", ""))

            if "payload" in response_json:
                homes_list = response_json["payload"].get("homes", [])
                buildings_list = response_json["payload"].get("buildings", {}).values()

                homes = [self._parse_home(home) for home in homes_list] + [
                    self._parse_building(building) for building in buildings_list
                ]
                return homes
            else:
                return []
