import json
from ..types import Home, Address
from .. import Scraper
from typing import Any


class RedfinScraper(Scraper):
    def __init__(self, scraper_input):
        super().__init__(scraper_input)

    def handle_location(self):
        url = 'https://www.redfin.com/stingray/do/location-autocomplete?v=2&al=1&location={}'.format(self.location)

        response = self.session.get(url)
        response_json = json.loads(response.text.replace('{}&&', ''))

        if response_json['payload']['exactMatch'] is not None:
            return response_json['payload']['exactMatch']['id'].split('_')[1]
        else:
            return response_json['payload']['sections'][0]['rows'][0].split('_')[1]

    @staticmethod
    def parse_home(home: dict) -> Home:
        address = Address(
            address_one=home['streetLine']['value'],
            city=home['city'],
            state=home['state'],
            zip_code=home['zip']
        )

        url = 'https://www.redfin.com{}'.format(home['url'])

        def get_value(key: str) -> Any | None:
            if key in home and 'value' in home[key]:
                return home[key]['value']

        return Home(
            address=address,
            url=url,
            beds=home['beds'] if 'beds' in home else None,
            baths=home['baths'] if 'baths' in home else None,
            stories=home['stories'] if 'stories' in home else None,
            agent_name=get_value('listingAgent'),
            description=home['listingRemarks'] if 'listingRemarks' in home else None,
            year_built=get_value('yearBuilt'),
            square_feet=get_value('sqFt'),
            price_per_square_foot=get_value('pricePerSqFt'),
            price=get_value('price'),
            mls_id=get_value('mlsId')
        )

    def search(self):
        region_id = self.handle_location()

        url = 'https://www.redfin.com/stingray/api/gis?al=1&region_id={}&region_type=2'.format(region_id)

        response = self.session.get(url)
        response_json = json.loads(response.text.replace('{}&&', ''))

        homes = [self.parse_home(home) for home in response_json['payload']['homes']]
        return homes


