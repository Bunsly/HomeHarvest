import json
from ..types import Home, Address
from .. import Scraper


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
    def parse_home(home) -> Home:
        ...

    def search(self):
        region_id = self.handle_location()

        url = 'https://www.redfin.com/stingray/api/gis?al=1&region_id={}&region_type=2'.format(region_id)

        response = self.session.get(url)
        response_json = json.loads(response.text.replace('{}&&', ''))

        homes = [self.parse_home(home) for home in response_json['payload']['homes']]
        return homes


