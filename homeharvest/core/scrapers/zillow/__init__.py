import re
import json
from .. import Scraper
from ....utils import parse_address_two
from ....exceptions import NoResultsFound, PropertyNotFound
from ..models import Property, Address, ListingType, PropertyType, SiteName


class ZillowScraper(Scraper):
    def __init__(self, scraper_input):
        super().__init__(scraper_input)
        self.listing_type = scraper_input.listing_type
        if self.listing_type == ListingType.FOR_SALE:
            self.url = f"https://www.zillow.com/homes/for_sale/{self.location}_rb/"
        elif self.listing_type == ListingType.FOR_RENT:
            self.url = f"https://www.zillow.com/homes/for_rent/{self.location}_rb/"
        else:
            self.url = f"https://www.zillow.com/homes/recently_sold/{self.location}_rb/"

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
                raise BoxBoundsNotFound("Box bounds could not be located.")

        elif "gdpClientCache" in data["props"]["pageProps"]:
            gdp_client_cache = json.loads(data["props"]["pageProps"]["gdpClientCache"])
            main_key = list(gdp_client_cache.keys())[0]

            property_data = gdp_client_cache[main_key]["property"]
            property = self._get_single_property_page(property_data)

            return [property]
        raise PropertyNotFound("Specific property data not found in the response.")

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
        a = resp.json()
        return self._parse_properties(resp.json())

    def _parse_properties(self, property_data: dict):
        mapresults = property_data["cat1"]["searchResults"]["mapResults"]

        properties_list = []

        for result in mapresults:
            if "hdpData" in result:
                home_info = result["hdpData"]["homeInfo"]
                address_data = {
                    "street_address": home_info["streetAddress"],
                    "unit": parse_address_two(home_info["unit"])
                    if "unit" in home_info
                    else None,
                    "city": home_info["city"],
                    "state": home_info["state"],
                    "zip_code": home_info["zipcode"],
                    "country": home_info["country"],
                }
                property_data = {
                    "site_name": self.site_name,
                    "address": Address(**address_data),
                    "property_url": f"https://www.zillow.com{result['detailUrl']}",
                    "beds": int(home_info["bedrooms"])
                    if "bedrooms" in home_info
                    else None,
                    "baths": home_info.get("bathrooms"),
                    "square_feet": int(home_info["livingArea"])
                    if "livingArea" in home_info
                    else None,
                    "currency": home_info["currency"],
                    "price": home_info.get("price"),
                    "square_feet": int(home_info["livingArea"])
                    if "livingArea" in home_info
                    else None,
                    "tax_assessed_value": int(home_info["taxAssessedValue"])
                    if "taxAssessedValue" in home_info
                    else None,
                    "property_type": PropertyType(home_info["homeType"]),
                    "listing_type": ListingType(
                        home_info["statusType"]
                        if "statusType" in home_info
                        else self.listing_type
                    ),
                    "lot_area_value": round(home_info["lotAreaValue"], 2)
                    if "lotAreaValue" in home_info
                    else None,
                    "lot_area_unit": home_info.get("lotAreaUnit"),
                    "latitude": result["latLong"]["latitude"],
                    "longitude": result["latLong"]["longitude"],
                    "status_text": result.get("statusText"),
                    "posted_time": result["variableData"]["text"]
                    if "variableData" in result
                    and "text" in result["variableData"]
                    and result["variableData"]["type"] == "TIME_ON_INFO"
                    else None,
                    "img_src": result.get("imgSrc"),
                    "price_per_sqft": int(home_info["price"] // home_info["livingArea"])
                    if "livingArea" in home_info and "price" in home_info
                    else None,
                }
                property_obj = Property(**property_data)
                properties_list.append(property_obj)

            elif "isBuilding" in result:
                price = result["price"]
                building_data = {
                    "property_url": f"https://www.zillow.com{result['detailUrl']}",
                    "site_name": self.site_name,
                    "property_type": PropertyType("BUILDING"),
                    "listing_type": ListingType(result["statusType"]),
                    "img_src": result["imgSrc"],
                    "price": int(price.replace("From $", "").replace(",", ""))
                    if "From $" in price
                    else None,
                    "apt_min_price": int(
                        price.replace("$", "").replace(",", "").replace("+/mo", "")
                    )
                    if "+/mo" in price
                    else None,
                    "address": self._extract_address(result["address"]),
                    "bldg_min_beds": result["minBeds"],
                    "currency": "USD",
                    "bldg_min_baths": result["minBaths"],
                    "bldg_min_area": result.get("minArea"),
                    "bldg_unit_count": result["unitCount"],
                    "bldg_name": result.get("communityName"),
                    "status_text": result["statusText"],
                    "latitude": result["latLong"]["latitude"],
                    "longitude": result["latLong"]["longitude"],
                }
                building_obj = Property(**building_data)
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
            street_address=address_data["streetAddress"],
            unit=parse_address_two(address_data["streetAddress"]),
            city=address_data["city"],
            state=address_data["state"],
            zip_code=address_data["zipcode"],
            country=property_data.get("country"),
        )
        property_type = property_data.get("homeType", None)
        return Property(
            site_name=self.site_name,
            address=address,
            property_url=url,
            beds=property_data.get("bedrooms", None),
            baths=property_data.get("bathrooms", None),
            year_built=property_data.get("yearBuilt", None),
            price=property_data.get("price", None),
            tax_assessed_value=property_data.get("taxAssessedValue", None),
            latitude=property_data.get("latitude"),
            longitude=property_data.get("longitude"),
            img_src=property_data.get("streetViewTileImageUrlMediumAddress"),
            currency=property_data.get("currency", None),
            lot_area_value=property_data.get("lotAreaValue"),
            lot_area_unit=property_data["lotAreaUnits"].lower()
            if "lotAreaUnits" in property_data
            else None,
            agent_name=property_data.get("attributionInfo", {}).get("agentName", None),
            stories=property_data.get("resoFacts", {}).get("stories", None),
            description=property_data.get("description", None),
            mls_id=property_data.get("attributionInfo", {}).get("mlsId", None),
            price_per_sqft=property_data.get("resoFacts", {}).get(
                "pricePerSquareFoot", None
            ),
            square_feet=property_data.get("livingArea", None),
            property_type=PropertyType(property_type),
            listing_type=self.listing_type,
        )

    def _extract_address(self, address_str):
        """
        Extract address components from a string formatted like '555 Wedglea Dr, Dallas, TX',
        and return an Address object.
        """
        parts = address_str.split(", ")

        if len(parts) != 3:
            raise ValueError(f"Unexpected address format: {address_str}")

        street_address = parts[0].strip()
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
            street_address=street_address,
            city=city,
            unit=parse_address_two(street_address),
            state=state,
            zip_code=zip_code,
            country="USA",
        )

    @staticmethod
    def _get_headers():
        return {
            "authority": "www.zillow.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "cookie": 'zjs_user_id=null; zg_anonymous_id=%220976ab81-2950-4013-98f0-108b15a554d2%22; zguid=24|%246b1bc625-3955-4d1e-a723-e59602e4ed08; g_state={"i_p":1693611172520,"i_l":1}; zgsession=1|d48820e2-1659-4d2f-b7d2-99a8127dd4f3; zjs_anonymous_id=%226b1bc625-3955-4d1e-a723-e59602e4ed08%22; JSESSIONID=82E8274D3DC8AF3AB9C8E613B38CF861; search=6|1697585860120%7Crb%3DDallas%252C-TX%26rect%3D33.016646%252C-96.555516%252C32.618763%252C-96.999347%26disp%3Dmap%26mdm%3Dauto%26sort%3Ddays%26listPriceActive%3D1%26fs%3D1%26fr%3D0%26mmm%3D0%26rs%3D0%26ah%3D0%26singlestory%3D0%26abo%3D0%26garage%3D0%26pool%3D0%26ac%3D0%26waterfront%3D0%26finished%3D0%26unfinished%3D0%26cityview%3D0%26mountainview%3D0%26parkview%3D0%26waterview%3D0%26hoadata%3D1%263dhome%3D0%26commuteMode%3Ddriving%26commuteTimeOfDay%3Dnow%09%0938128%09%7B%22isList%22%3Atrue%2C%22isMap%22%3Atrue%7D%09%09%09%09%09; AWSALB=gAlFj5Ngnd4bWP8k7CME/+YlTtX9bHK4yEkdPHa3VhL6K523oGyysFxBEpE1HNuuyL+GaRPvt2i/CSseAb+zEPpO4SNjnbLAJzJOOO01ipnWN3ZgPaa5qdv+fAki; AWSALBCORS=gAlFj5Ngnd4bWP8k7CME/+YlTtX9bHK4yEkdPHa3VhL6K523oGyysFxBEpE1HNuuyL+GaRPvt2i/CSseAb+zEPpO4SNjnbLAJzJOOO01ipnWN3ZgPaa5qdv+fAki; search=6|1697587741808%7Crect%3D33.37188814545521%2C-96.34484483007813%2C32.260490641365685%2C-97.21001816992188%26disp%3Dmap%26mdm%3Dauto%26p%3D1%26sort%3Ddays%26z%3D1%26listPriceActive%3D1%26fs%3D1%26fr%3D0%26mmm%3D0%26rs%3D0%26ah%3D0%26singlestory%3D0%26housing-connector%3D0%26abo%3D0%26garage%3D0%26pool%3D0%26ac%3D0%26waterfront%3D0%26finished%3D0%26unfinished%3D0%26cityview%3D0%26mountainview%3D0%26parkview%3D0%26waterview%3D0%26hoadata%3D1%26zillow-owned%3D0%263dhome%3D0%26featuredMultiFamilyBuilding%3D0%26commuteMode%3Ddriving%26commuteTimeOfDay%3Dnow%09%09%09%7B%22isList%22%3Atrue%2C%22isMap%22%3Atrue%7D%09%09%09%09%09',
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
