from homeharvest import scrape_property
from homeharvest.exceptions import (
    InvalidListingType,
    NoResultsFound,
)


def test_realtor_comps():
    result = scrape_property(
        location="2530 Al Lipscomb Way",
        radius=0.5,
        property_younger_than=180,
        listing_type="sold",
    )

    assert result is not None and len(result) > 0


def test_realtor_last_x_days_sold():
    days_result_30 = scrape_property(
        location="Dallas, TX", listing_type="sold", property_younger_than=30
    )

    days_result_10 = scrape_property(
        location="Dallas, TX", listing_type="sold", property_younger_than=10
    )

    assert all(
        [result is not None for result in [days_result_30, days_result_10]]
    ) and len(days_result_30) != len(days_result_10)


def test_realtor_single_property():
    results = [
        scrape_property(
            location="15509 N 172nd Dr, Surprise, AZ 85388",
            listing_type="for_sale",
        ),
        scrape_property(
            location="2530 Al Lipscomb Way",
            listing_type="for_sale",
        ),
    ]

    assert all([result is not None for result in results])


def test_realtor():
    results = [
        scrape_property(
            location="2530 Al Lipscomb Way",
            listing_type="for_sale",
        ),
        scrape_property(
            location="Phoenix, AZ", listing_type="for_rent"
        ),  #: does not support "city, state, USA" format
        scrape_property(
            location="Dallas, TX", listing_type="sold"
        ),  #: does not support "city, state, USA" format
        scrape_property(location="85281"),
    ]

    assert all([result is not None for result in results])

    bad_results = []
    try:
        bad_results += [
            scrape_property(
                location="abceefg ju098ot498hh9",
                listing_type="for_sale",
            )
        ]
    except (InvalidListingType, NoResultsFound):
        assert True

    assert all([result is None for result in bad_results])
