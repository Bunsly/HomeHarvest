from homeharvest import scrape_property
from homeharvest.exceptions import (
    InvalidSite,
    InvalidListingType,
    NoResultsFound,
    GeoCoordsNotFound,
)


def test_zillow():
    results = [
        scrape_property(location="2530 Al Lipscomb Way", site_name="zillow", listing_type="for_sale"),
        scrape_property(location="Phoenix, AZ, USA", site_name=["zillow"], listing_type="for_rent"),
        scrape_property(location="Dallas, TX, USA", site_name="zillow", listing_type="sold"),
        scrape_property(location="85281", site_name="zillow"),
        scrape_property(location="3268 88th st s, Lakewood", site_name="zillow", listing_type="for_rent"),
    ]

    assert all([result is not None for result in results])

    bad_results = []
    try:
        bad_results += [
            scrape_property(
                location="abceefg ju098ot498hh9",
                site_name="zillow",
                listing_type="for_sale",
            )
        ]
    except (InvalidSite, InvalidListingType, NoResultsFound, GeoCoordsNotFound):
        assert True

    assert all([result is None for result in bad_results])
