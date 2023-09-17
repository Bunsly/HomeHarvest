import re
import json
from ..models import Property, Address, Building, ListingType
from ....exceptions import NoResultsFound, PropertyNotFound
from .. import Scraper


class ZillowScraper(Scraper):
    listing_type: ListingType.FOR_SALE

    def __init__(self, scraper_input):
        super().__init__(scraper_input)
        if self.listing_type == ListingType.FOR_SALE:
            self.url = f"https://www.zillow.com/homes/for_sale/{self.location}_rb/"
        elif self.listing_type == ListingType.FOR_RENT:
            self.url = f"https://www.zillow.com/homes/for_rent/{self.location}_rb/"

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
            houses = data["props"]["pageProps"]["searchPageState"]["cat1"][
                "searchResults"
            ]["listResults"]
            return [self._parse_home(house) for house in houses]
        elif "gdpClientCache" in data["props"]["pageProps"]:
            gdp_client_cache = json.loads(data["props"]["pageProps"]["gdpClientCache"])
            main_key = list(gdp_client_cache.keys())[0]

            property_data = gdp_client_cache[main_key]["property"]
            property = self._get_single_property_page(property_data)

            return [property]
        raise PropertyNotFound("Specific property data not found in the response.")

    @classmethod
    def _parse_home(cls, home: dict):
        """
        This method is used when a user enters a generic location & zillow returns more than one property
        """
        url = (
            f"https://www.zillow.com{home['detailUrl']}"
            if "zillow.com" not in home["detailUrl"]
            else home["detailUrl"]
        )

        if "hdpData" in home and "homeInfo" in home["hdpData"]:
            price_data = cls._extract_price(home)
            address = cls._extract_address(home)
            agent_name = cls._extract_agent_name(home)
            beds = home["hdpData"]["homeInfo"]["bedrooms"]
            baths = home["hdpData"]["homeInfo"]["bathrooms"]
            listing_type = home["hdpData"]["homeInfo"].get("homeType")

            return Property(
                address=address,
                agent_name=agent_name,
                url=url,
                beds=beds,
                baths=baths,
                listing_type=listing_type,
                **price_data,
            )
        else:
            keys = ("addressStreet", "addressCity", "addressState", "addressZipcode")
            address_one, city, state, zip_code = (home[key] for key in keys)
            address_one, address_two = cls._parse_address_two(address_one)
            address = Address(address_one, city, state, zip_code, address_two)

            building_info = cls._extract_building_info(home)
            return Building(address=address, url=url, **building_info)

    @classmethod
    def _get_single_property_page(cls, property_data: dict):
        """
        This method is used when a user enters the exact location & zillow returns just one property
        """
        url = (
            f"https://www.zillow.com{property_data['hdpUrl']}"
            if "zillow.com" not in property_data["hdpUrl"]
            else property_data["hdpUrl"]
        )
        address_data = property_data["address"]
        address_one, address_two = cls._parse_address_two(address_data["streetAddress"])
        address = Address(
            address_one=address_one,
            address_two=address_two,
            city=address_data["city"],
            state=address_data["state"],
            zip_code=address_data["zipcode"],
        )

        return Property(
            address=address,
            url=url,
            beds=property_data.get("bedrooms", None),
            baths=property_data.get("bathrooms", None),
            year_built=property_data.get("yearBuilt", None),
            price=property_data.get("price", None),
            lot_size=property_data.get("lotSize", None),
            agent_name=property_data.get("attributionInfo", {}).get("agentName", None),
            stories=property_data.get("resoFacts", {}).get("stories", None),
            description=property_data.get("description", None),
            mls_id=property_data.get("attributionInfo", {}).get("mlsId", None),
            price_per_square_foot=property_data.get("resoFacts", {}).get(
                "pricePerSquareFoot", None
            ),
            square_feet=property_data.get("livingArea", None),
            listing_type=property_data.get("homeType", None),
        )

    @classmethod
    def _extract_building_info(cls, home: dict) -> dict:
        num_units = len(home["units"])
        prices = [
            int(unit["price"].replace("$", "").replace(",", "").split("+")[0])
            for unit in home["units"]
        ]
        return {
            "listing_type": cls.listing_type,
            "num_units": len(home["units"]),
            "min_unit_price": min(
                (
                    int(unit["price"].replace("$", "").replace(",", "").split("+")[0])
                    for unit in home["units"]
                )
            ),
            "max_unit_price": max(
                (
                    int(unit["price"].replace("$", "").replace(",", "").split("+")[0])
                    for unit in home["units"]
                )
            ),
            "avg_unit_price": sum(prices) // len(prices) if num_units else None,
        }

    @staticmethod
    def _extract_price(home: dict) -> dict:
        price = int(home["hdpData"]["homeInfo"]["priceForHDP"])
        square_feet = home["hdpData"]["homeInfo"].get("livingArea")

        lot_size = home["hdpData"]["homeInfo"].get("lotAreaValue")
        price_per_square_foot = price // square_feet if square_feet and price else None

        return {
            k: v
            for k, v in locals().items()
            if k in ["price", "square_feet", "lot_size", "price_per_square_foot"]
        }

    @staticmethod
    def _extract_agent_name(home: dict) -> str | None:
        broker_str = home.get("brokerName", "")
        match = re.search(r"Listing by: (.+)", broker_str)
        return match.group(1) if match else None

    @staticmethod
    def _parse_address_two(address_one: str):
        apt_match = re.search(r"(APT\s*.+|#[\s\S]+)$", address_one, re.I)
        address_two = apt_match.group().strip() if apt_match else None
        address_one = (
            address_one.replace(address_two, "").strip() if address_two else address_one
        )
        return address_one, address_two

    @staticmethod
    def _extract_address(home: dict) -> Address:
        keys = ("streetAddress", "city", "state", "zipcode")
        address_one, city, state, zip_code = (
            home["hdpData"]["homeInfo"][key] for key in keys
        )
        address_one, address_two = ZillowScraper._parse_address_two(address_one)
        return Address(address_one, city, state, zip_code, address_two=address_two)

    @staticmethod
    def _get_headers():
        return {
            "authority": "parser-external.geo.moveaws.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://www.zillow.com",
            "referer": "https://www.zillow.com/",
            "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        }
