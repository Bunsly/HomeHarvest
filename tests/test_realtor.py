from homeharvest import scrape_property
from homeharvest.exceptions import (
    InvalidSite,
    InvalidListingType,
    NoResultsFound,
    GeoCoordsNotFound,
)


def test_realtor_comps():
    result = scrape_property(
            location="2530 Al Lipscomb Way",
            site_name="realtor.com",
            radius=0.5,
    )

    assert result is not None and len(result) > 0


def test_realtor_last_x_days_sold():
    days_result_30 = scrape_property(
        location="Dallas, TX", site_name="realtor.com", listing_type="sold", sold_last_x_days=30
    )

    days_result_10 = scrape_property(
        location="Dallas, TX", site_name="realtor.com", listing_type="sold", sold_last_x_days=10
    )

    assert all([result is not None for result in [days_result_30, days_result_10]]) and len(days_result_30) != len(days_result_10)


def test_realtor():
    results = [
        scrape_property(
            location="2530 Al Lipscomb Way",
            site_name="realtor.com",
            listing_type="for_sale",
        ),
        scrape_property(
            location="Phoenix, AZ", site_name=["realtor.com"], listing_type="for_rent"
        ),  #: does not support "city, state, USA" format
        scrape_property(
            location="Dallas, TX", site_name="realtor.com", listing_type="sold"
        ),  #: does not support "city, state, USA" format
        scrape_property(location="85281", site_name="realtor.com"),
    ]

    assert all([result is not None for result in results])

    bad_results = []
    try:
        bad_results += [
            scrape_property(
                location="abceefg ju098ot498hh9",
                site_name="realtor.com",
                listing_type="for_sale",
            )
        ]
    except (InvalidSite, InvalidListingType, NoResultsFound, GeoCoordsNotFound):
        assert True

    assert all([result is None for result in bad_results])
