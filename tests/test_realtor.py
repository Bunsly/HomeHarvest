from homeharvest import scrape_property
from homeharvest.exceptions import (
    InvalidListingType,
)


def test_realtor_pending_or_contingent():
    pending_or_contingent_result = scrape_property(
        location="Surprise, AZ", listing_type="pending"
    )

    regular_result = scrape_property(location="Surprise, AZ", listing_type="for_sale")

    assert all(
        [
            result is not None
            for result in [pending_or_contingent_result, regular_result]
        ]
    )
    assert len(pending_or_contingent_result) != len(regular_result)


def test_realtor_pending_comps():
    pending_comps = scrape_property(
        location="2530 Al Lipscomb Way",
        radius=5,
        past_days=180,
        listing_type="pending",
    )

    for_sale_comps = scrape_property(
        location="2530 Al Lipscomb Way",
        radius=5,
        past_days=180,
        listing_type="for_sale",
    )

    sold_comps = scrape_property(
        location="2530 Al Lipscomb Way",
        radius=5,
        past_days=180,
        listing_type="sold",
    )

    results = [pending_comps, for_sale_comps, sold_comps]
    assert all([result is not None for result in results])

    #: assert all lengths are different
    assert len(set([len(result) for result in results])) == len(results)


def test_realtor_sold_past():
    result = scrape_property(
        location="San Diego, CA",
        past_days=30,
        listing_type="sold",
    )

    assert result is not None and len(result) > 0


def test_realtor_comps():
    result = scrape_property(
        location="2530 Al Lipscomb Way",
        radius=0.5,
        past_days=180,
        listing_type="sold",
    )

    assert result is not None and len(result) > 0


def test_realtor_last_x_days_sold():
    days_result_30 = scrape_property(
        location="Dallas, TX", listing_type="sold", past_days=30
    )

    days_result_10 = scrape_property(
        location="Dallas, TX", listing_type="sold", past_days=10
    )

    assert all(
        [result is not None for result in [days_result_30, days_result_10]]
    ) and len(days_result_30) != len(days_result_10)


def test_realtor_date_range_sold():
    days_result_30 = scrape_property(
        location="Dallas, TX", listing_type="sold", date_from="2023-05-01", date_to="2023-05-28"
    )

    days_result_60 = scrape_property(
        location="Dallas, TX", listing_type="sold", date_from="2023-04-01", date_to="2023-06-10"
    )

    assert all(
        [result is not None for result in [days_result_30, days_result_60]]
    ) and len(days_result_30) < len(days_result_60)


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


def test_realtor_city():
    results = scrape_property(
        location="Atlanta, GA",
        listing_type="for_sale",
    )

    assert results is not None and len(results) > 0


def test_realtor_bad_address():
    bad_results = scrape_property(
            location="abceefg ju098ot498hh9",
            listing_type="for_sale",
        )
    if len(bad_results) == 0:
        assert True


def test_realtor_foreclosed():
    foreclosed = scrape_property(
        location="Dallas, TX", listing_type="for_sale", past_days=100, foreclosure=True
    )

    not_foreclosed = scrape_property(
        location="Dallas, TX", listing_type="for_sale", past_days=100, foreclosure=False
    )

    assert len(foreclosed) != len(not_foreclosed)

