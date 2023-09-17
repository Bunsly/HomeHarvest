import json
from ..models import Property, Address
from .. import Scraper
from typing import Any


class RealtorScraper(Scraper):
    def __init__(self, scraper_input):
        super().__init__(scraper_input)

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
            "client_id": "for-sale",
            "limit": "1",
            "area_types": "city,state,county,postal_code,address,street,neighborhood,school,school_district,university,park",
        }

        response = self.session.get(
            "https://parser-external.geo.moveaws.com/suggest",
            params=params,
            headers=headers,
        )
        response_json = response.json()

        return response_json["autocomplete"][0]

    def search(self):
        location_info = self.handle_location()
        location_type = location_info["area_type"]

        """
        property types:
        apartment + building + commercial + condo_townhome + condo_townhome_rowhome_coop + condos + coop + duplex_triplex + farm + investment + land + mobile + multi_family + rental + single_family + townhomes
        """
        print("a")
