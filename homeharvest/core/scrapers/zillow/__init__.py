"""
homeharvest.zillow.__init__
~~~~~~~~~~~~

This module implements the scraper for zillow.com
"""
import re
import json

import tls_client

from .. import Scraper
from requests.exceptions import HTTPError
from ....exceptions import GeoCoordsNotFound, NoResultsFound
from ..models import Property, Address, Status
import urllib.parse
from datetime import datetime, timedelta


class ZillowScraper(Scraper):
    def __init__(self, scraper_input):
        session = tls_client.Session(
            client_identifier="chrome112", random_tls_extension_order=True
        )

        super().__init__(scraper_input, session)

        self.session.headers.update(
            {
                "authority": "www.zillow.com",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "max-age=0",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            }
        )

        if not self.is_plausible_location(self.location):
            raise NoResultsFound("Invalid location input: {}".format(self.location))

        listing_type_to_url_path = {
            Status.FOR_SALE: "for_sale",
            Status.FOR_RENT: "for_rent",
            Status.SOLD: "recently_sold",
        }

        self.url = f"https://www.zillow.com/homes/{listing_type_to_url_path[self.listing_type]}/{self.location}_rb/"

    def is_plausible_location(self, location: str) -> bool:
        url = (
            "https://www.zillowstatic.com/autocomplete/v3/suggestions?q={"
            "}&abKey=6666272a-4b99-474c-b857-110ec438732b&clientId=homepage-render"
        ).format(urllib.parse.quote(location))

        resp = self.session.get(url)

        return resp.json()["results"] != []

    def search(self):
        resp = self.session.get(self.url)
        if resp.status_code != 200:
            raise HTTPError(f"bad response status code: {resp.status_code}")
        content = resp.text

        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            content,
            re.DOTALL,
        )
        if not match:
            raise NoResultsFound(
                "No results were found for Zillow with the given Location."
            )

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
            if self.listing_type == Status.FOR_RENT
            else filter_state_for_sale
            if self.listing_type == Status.FOR_SALE
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
        resp = self.session.put(url, json=payload)
        if resp.status_code != 200:
            raise HTTPError(f"bad response status code: {resp.status_code}")
        return self._parse_properties(resp.json())

    @staticmethod
    def parse_posted_time(time: str) -> datetime:
        int_time = int(time.split(" ")[0])

        if "hour" in time:
            return datetime.now() - timedelta(hours=int_time)

        if "day" in time:
            return datetime.now() - timedelta(days=int_time)

    def _parse_properties(self, property_data: dict):
        mapresults = property_data["cat1"]["searchResults"]["mapResults"]

        properties_list = []

        for result in mapresults:
            if "hdpData" in result:
                home_info = result["hdpData"]["homeInfo"]
                address_data = {
                    "streeet": home_info.get("streetAddress"),
                    "city": home_info.get("city"),
                    "state": home_info.get("state"),
                    "zip": home_info.get("zipcode"),
                }
                property_obj = Property(
                    address=Address(**address_data),
                    property_url=f"https://www.zillow.com{result['detailUrl']}",
                    style=home_info.get("homeType"),
                    status=home_info["statusType"].upper()
                    if "statusType" in home_info
                    else self.status,
                    list_price=home_info.get("price"),
                    beds=int(home_info["bedrooms"])
                    if "bedrooms" in home_info
                    else None,
                    baths_full=home_info.get("bathrooms"),
                    est_sf=int(home_info["livingArea"])
                    if "livingArea" in home_info
                    else None,
                    prc_sqft=int(home_info["price"] // home_info["livingArea"])
                    if "livingArea" in home_info
                    and home_info["livingArea"] != 0
                    and "price" in home_info
                    else None,
                    latitude=result["latLong"]["latitude"],
                    longitude=result["latLong"]["longitude"],
                    lot_sf=round(home_info["lotAreaValue"], 2)
                    if "lotAreaValue" in home_info
                    else None,
                )

                properties_list.append(property_obj)

            elif "isBuilding" in result:
                price_string = (
                    result["price"]
                    .replace("$", "")
                    .replace(",", "")
                    .replace("+/mo", "")
                )

                match = re.search(r"(\d+)", price_string)
                price_value = int(match.group(1)) if match else None
                building_obj = Property(
                    property_url=f"https://www.zillow.com{result['detailUrl']}",
                    style="BUILDING",
                    address=self._extract_address(result["address"]),
                    baths_full=result.get("minBaths"),
                    neighborhoods=result.get("communityName"),
                    list_price=price_value if "+/mo" in result.get("price") else None,
                    latitude=result.get("latLong", {}).get("latitude"),
                    longitude=result.get("latLong", {}).get("longitude"),
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
        address = Address(
            street=address_data["streetAddress"],
            city=address_data["city"],
            state=address_data["state"],
            zip=address_data["zipcode"],
        )
        property_type = property_data.get("homeType", None)
        return Property(
            property_url=url,
            status=self.status,
            address=address,
            yr_blt=property_data.get("yearBuilt"),
            lot_sf=property_data.get("lotAreaValue"),
            stories=property_data.get("resoFacts", {}).get("stories"),
            mls_id=property_data.get("attributionInfo", {}).get("mlsId"),
            beds=property_data.get("bedrooms"),
            baths_full=property_data.get("bathrooms"),
            list_price=property_data.get("price"),
            est_sf=property_data.get("livingArea"),
            prc_sqft=property_data.get("resoFacts", {}).get("pricePerSquareFoot"),
            latitude=property_data.get("latitude"),
            longitude=property_data.get("longitude"),
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

        return Address(
            street=address_one,
            city=city,
            state=state,
            zip=zip_code,
        )
