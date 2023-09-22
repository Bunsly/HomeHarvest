"""
homeharvest.zillow.__init__
~~~~~~~~~~~~

This module implements the scraper for zillow.com
"""
import re
import json
from .. import Scraper
from ....utils import parse_address_one, parse_address_two
from ....exceptions import GeoCoordsNotFound, NoResultsFound
from ..models import Property, Address, ListingType, PropertyType


class ZillowScraper(Scraper):
    def __init__(self, scraper_input):
        super().__init__(scraper_input)
        self.cookies = None

        if not self.is_plausible_location(self.location):
            raise NoResultsFound("Invalid location input: {}".format(self.location))

        listing_type_to_url_path = {
            ListingType.FOR_SALE: "for_sale",
            ListingType.FOR_RENT: "for_rent",
            ListingType.SOLD: "recently_sold",
        }

        self.url = f"https://www.zillow.com/homes/{listing_type_to_url_path[self.listing_type]}/{self.location}_rb/"

    def is_plausible_location(self, location: str) -> bool:
        url = (
            "https://www.zillowstatic.com/autocomplete/v3/suggestions?q={"
            "}&abKey=6666272a-4b99-474c-b857-110ec438732b&clientId=homepage-render"
        ).format(location)

        response = self.session.get(url)

        return response.json()["results"] != []

    def search(self):
        resp = self.session.get(self.url, headers=self._get_headers())
        resp.raise_for_status()
        content = resp.text

        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            content,
            re.DOTALL,
        )
        if not match:
            raise NoResultsFound("No results were found for Zillow with the given Location.")

        json_str = match.group(1)
        data = json.loads(json_str)

        if "searchPageState" in data["props"]["pageProps"]:
            pattern = r'window\.mapBounds = \{\s*"west":\s*(-?\d+\.\d+),\s*"east":\s*(-?\d+\.\d+),\s*"south":\s*(-?\d+\.\d+),\s*"north":\s*(-?\d+\.\d+)\s*\};'

            match = re.search(pattern, content)

            if match:
                coords = [float(coord) for coord in match.groups()]
                return self._fetch_properties_backend(coords)

            else:
                raise GeoCoordsNotFound("Box bounds could not be located.")

        elif "gdpClientCache" in data["props"]["pageProps"]:
            gdp_client_cache = json.loads(data["props"]["pageProps"]["gdpClientCache"])
            main_key = list(gdp_client_cache.keys())[0]

            property_data = gdp_client_cache[main_key]["property"]
            property = self._get_single_property_page(property_data)

            return [property]
        raise NoResultsFound("Specific property data not found in the response.")

    def _fetch_properties_backend(self, coords):
        url = "https://www.zillow.com/async-create-search-page-state"

        filter_state_for_sale = {
            "sortSelection": {
                # "value": "globalrelevanceex"
                "value": "days"
            },
            "isAllHomes": {"value": True},
        }

        filter_state_for_rent = {
            "isForRent": {"value": True},
            "isForSaleByAgent": {"value": False},
            "isForSaleByOwner": {"value": False},
            "isNewConstruction": {"value": False},
            "isComingSoon": {"value": False},
            "isAuction": {"value": False},
            "isForSaleForeclosure": {"value": False},
            "isAllHomes": {"value": True},
        }

        filter_state_sold = {
            "isRecentlySold": {"value": True},
            "isForSaleByAgent": {"value": False},
            "isForSaleByOwner": {"value": False},
            "isNewConstruction": {"value": False},
            "isComingSoon": {"value": False},
            "isAuction": {"value": False},
            "isForSaleForeclosure": {"value": False},
            "isAllHomes": {"value": True},
        }

        selected_filter = (
            filter_state_for_rent
            if self.listing_type == ListingType.FOR_RENT
            else filter_state_for_sale
            if self.listing_type == ListingType.FOR_SALE
            else filter_state_sold
        )

        payload = {
            "searchQueryState": {
                "pagination": {},
                "isMapVisible": True,
                "mapBounds": {
                    "west": coords[0],
                    "east": coords[1],
                    "south": coords[2],
                    "north": coords[3],
                },
                "filterState": selected_filter,
                "isListVisible": True,
                "mapZoom": 11,
            },
            "wants": {"cat1": ["mapResults"]},
            "isDebugRequest": False,
        }
        resp = self.session.put(url, headers=self._get_headers(), json=payload)
        resp.raise_for_status()
        self.cookies = resp.cookies
        a = resp.json()
        return self._parse_properties(resp.json())

    def _parse_properties(self, property_data: dict):
        mapresults = property_data["cat1"]["searchResults"]["mapResults"]

        properties_list = []

        for result in mapresults:
            if "hdpData" in result:
                home_info = result["hdpData"]["homeInfo"]
                address_data = {
                    "address_one": parse_address_one(home_info.get("streetAddress"))[0],
                    "address_two": parse_address_two(home_info["unit"]) if "unit" in home_info else "#",
                    "city": home_info.get("city"),
                    "state": home_info.get("state"),
                    "zip_code": home_info.get("zipcode"),
                }
                property_obj = Property(
                    site_name=self.site_name,
                    address=Address(**address_data),
                    property_url=f"https://www.zillow.com{result['detailUrl']}",
                    tax_assessed_value=int(home_info["taxAssessedValue"]) if "taxAssessedValue" in home_info else None,
                    property_type=PropertyType(home_info.get("homeType")),
                    listing_type=ListingType(
                        home_info["statusType"] if "statusType" in home_info else self.listing_type
                    ),
                    status_text=result.get("statusText"),
                    posted_time=result["variableData"]["text"]
                    if "variableData" in result
                    and "text" in result["variableData"]
                    and result["variableData"]["type"] == "TIME_ON_INFO"
                    else None,
                    price_min=home_info.get("price"),
                    price_max=home_info.get("price"),
                    beds_min=int(home_info["bedrooms"]) if "bedrooms" in home_info else None,
                    beds_max=int(home_info["bedrooms"]) if "bedrooms" in home_info else None,
                    baths_min=home_info.get("bathrooms"),
                    baths_max=home_info.get("bathrooms"),
                    sqft_min=int(home_info["livingArea"]) if "livingArea" in home_info else None,
                    sqft_max=int(home_info["livingArea"]) if "livingArea" in home_info else None,
                    price_per_sqft=int(home_info["price"] // home_info["livingArea"])
                    if "livingArea" in home_info and home_info["livingArea"] != 0 and "price" in home_info
                    else None,
                    latitude=result["latLong"]["latitude"],
                    longitude=result["latLong"]["longitude"],
                    lot_area_value=round(home_info["lotAreaValue"], 2) if "lotAreaValue" in home_info else None,
                    lot_area_unit=home_info.get("lotAreaUnit"),
                    img_src=result.get("imgSrc"),
                )

                properties_list.append(property_obj)

            elif "isBuilding" in result:
                price_string = result["price"].replace("$", "").replace(",", "").replace("+/mo", "")

                match = re.search(r"(\d+)", price_string)
                price_value = int(match.group(1)) if match else None
                building_obj = Property(
                    property_url=f"https://www.zillow.com{result['detailUrl']}",
                    site_name=self.site_name,
                    property_type=PropertyType("BUILDING"),
                    listing_type=ListingType(result["statusType"]),
                    img_src=result.get("imgSrc"),
                    address=self._extract_address(result["address"]),
                    baths_min=result.get("minBaths"),
                    area_min=result.get("minArea"),
                    bldg_name=result.get("communityName"),
                    status_text=result.get("statusText"),
                    price_min=price_value if "+/mo" in result.get("price") else None,
                    price_max=price_value if "+/mo" in result.get("price") else None,
                    latitude=result.get("latLong", {}).get("latitude"),
                    longitude=result.get("latLong", {}).get("longitude"),
                    unit_count=result.get("unitCount"),
                )

                properties_list.append(building_obj)

        return properties_list

    def _get_single_property_page(self, property_data: dict):
        """
        This method is used when a user enters the exact location & zillow returns just one property
        """
        url = (
            f"https://www.zillow.com{property_data['hdpUrl']}"
            if "zillow.com" not in property_data["hdpUrl"]
            else property_data["hdpUrl"]
        )
        address_data = property_data["address"]
        address_one, address_two = parse_address_one(address_data["streetAddress"])
        address = Address(
            address_one=address_one,
            address_two=address_two if address_two else "#",
            city=address_data["city"],
            state=address_data["state"],
            zip_code=address_data["zipcode"],
        )
        property_type = property_data.get("homeType", None)
        return Property(
            site_name=self.site_name,
            property_url=url,
            property_type=PropertyType(property_type),
            listing_type=self.listing_type,
            address=address,
            year_built=property_data.get("yearBuilt"),
            tax_assessed_value=property_data.get("taxAssessedValue"),
            lot_area_value=property_data.get("lotAreaValue"),
            lot_area_unit=property_data["lotAreaUnits"].lower() if "lotAreaUnits" in property_data else None,
            agent_name=property_data.get("attributionInfo", {}).get("agentName"),
            stories=property_data.get("resoFacts", {}).get("stories"),
            mls_id=property_data.get("attributionInfo", {}).get("mlsId"),
            beds_min=property_data.get("bedrooms"),
            beds_max=property_data.get("bedrooms"),
            baths_min=property_data.get("bathrooms"),
            baths_max=property_data.get("bathrooms"),
            price_min=property_data.get("price"),
            price_max=property_data.get("price"),
            sqft_min=property_data.get("livingArea"),
            sqft_max=property_data.get("livingArea"),
            price_per_sqft=property_data.get("resoFacts", {}).get("pricePerSquareFoot"),
            latitude=property_data.get("latitude"),
            longitude=property_data.get("longitude"),
            img_src=property_data.get("streetViewTileImageUrlMediumAddress"),
            description=property_data.get("description"),
        )

    def _extract_address(self, address_str):
        """
        Extract address components from a string formatted like '555 Wedglea Dr, Dallas, TX',
        and return an Address object.
        """
        parts = address_str.split(", ")

        if len(parts) != 3:
            raise ValueError(f"Unexpected address format: {address_str}")

        address_one = parts[0].strip()
        city = parts[1].strip()
        state_zip = parts[2].split(" ")

        if len(state_zip) == 1:
            state = state_zip[0].strip()
            zip_code = None
        elif len(state_zip) == 2:
            state = state_zip[0].strip()
            zip_code = state_zip[1].strip()
        else:
            raise ValueError(f"Unexpected state/zip format in address: {address_str}")

        address_one, address_two = parse_address_one(address_one)
        return Address(
            address_one=address_one,
            address_two=address_two if address_two else "#",
            city=city,
            state=state,
            zip_code=zip_code,
        )

    def _get_headers(self):
        headers = {
            "authority": "www.zillow.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.zillow.com",
            "referer": "https://www.zillow.com",
            "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        }
        if self.cookies:
            headers['Cookie'] = self.cookies
        return headers
