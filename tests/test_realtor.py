from homeharvest import scrape_property


def test_realtor_pending_or_contingent():
    pending_or_contingent_result = scrape_property(location="Surprise, AZ", listing_type="pending")

    regular_result = scrape_property(location="Surprise, AZ", listing_type="for_sale", exclude_pending=True)

    assert all([result is not None for result in [pending_or_contingent_result, regular_result]])
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
    days_result_30 = scrape_property(location="Dallas, TX", listing_type="sold", past_days=30)

    days_result_10 = scrape_property(location="Dallas, TX", listing_type="sold", past_days=10)

    assert all([result is not None for result in [days_result_30, days_result_10]]) and len(days_result_30) != len(
        days_result_10
    )


def test_realtor_date_range_sold():
    days_result_30 = scrape_property(
        location="Dallas, TX", listing_type="sold", date_from="2023-05-01", date_to="2023-05-28"
    )

    days_result_60 = scrape_property(
        location="Dallas, TX", listing_type="sold", date_from="2023-04-01", date_to="2023-06-10"
    )

    assert all([result is not None for result in [days_result_30, days_result_60]]) and len(days_result_30) < len(
        days_result_60
    )


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
            location="Phoenix, AZ", listing_type="for_rent", limit=1000
        ),  #: does not support "city, state, USA" format
        scrape_property(
            location="Dallas, TX", listing_type="sold", limit=1000
        ),  #: does not support "city, state, USA" format
        scrape_property(location="85281"),
    ]

    assert all([result is not None for result in results])


def test_realtor_city():
    results = scrape_property(location="Atlanta, GA", listing_type="for_sale", limit=1000)

    assert results is not None and len(results) > 0


def test_realtor_land():
    results = scrape_property(location="Atlanta, GA", listing_type="for_sale", property_type=["land"], limit=1000)

    assert results is not None and len(results) > 0


def test_realtor_bad_address():
    bad_results = scrape_property(
        location="abceefg ju098ot498hh9",
        listing_type="for_sale",
    )

    if len(bad_results) == 0:
        assert True


def test_realtor_foreclosed():
    foreclosed = scrape_property(location="Dallas, TX", listing_type="for_sale", past_days=100, foreclosure=True)

    not_foreclosed = scrape_property(location="Dallas, TX", listing_type="for_sale", past_days=100, foreclosure=False)

    assert len(foreclosed) != len(not_foreclosed)


def test_realtor_agent():
    scraped = scrape_property(location="Detroit, MI", listing_type="for_sale", limit=1000, extra_property_data=False)
    assert scraped["agent_name"].nunique() > 1


def test_realtor_without_extra_details():
    results = [
        scrape_property(
            location="00741",
            listing_type="sold",
            limit=10,
            extra_property_data=False,
        ),
        scrape_property(
            location="00741",
            listing_type="sold",
            limit=10,
            extra_property_data=True,
        ),
    ]

    assert not results[0].equals(results[1])


def test_pr_zip_code():
    results = scrape_property(
        location="00741",
        listing_type="for_sale",
    )

    assert results is not None and len(results) > 0


def test_exclude_pending():
    results = scrape_property(
        location="33567",
        listing_type="pending",
        exclude_pending=True,
    )

    assert results is not None and len(results) > 0


def test_style_value_error():
    results = scrape_property(
        location="Alaska, AK",
        listing_type="sold",
        extra_property_data=False,
        limit=1000,
    )

    assert results is not None and len(results) > 0


def test_primary_image_error():
    results = scrape_property(
        location="Spokane, PA",
        listing_type="for_rent",  # or (for_sale, for_rent, pending)
        past_days=360,
        radius=3,
        extra_property_data=False,
    )

    assert results is not None and len(results) > 0


def test_limit():
    over_limit = 876
    extra_params = {"limit": over_limit}

    over_results = scrape_property(
        location="Waddell, AZ",
        listing_type="for_sale",
        **extra_params,
    )

    assert over_results is not None and len(over_results) <= over_limit

    under_limit = 1
    under_results = scrape_property(
        location="Waddell, AZ",
        listing_type="for_sale",
        limit=under_limit,
    )

    assert under_results is not None and len(under_results) == under_limit


def test_apartment_list_price():
    results = scrape_property(
        location="Spokane, WA",
        listing_type="for_rent",  # or (for_sale, for_rent, pending)
        extra_property_data=False,
    )

    assert results is not None

    results = results[results["style"] == "APARTMENT"]

    #: get percentage of results with atleast 1 of any column not none, list_price, list_price_min, list_price_max
    assert (
        len(results[results[["list_price", "list_price_min", "list_price_max"]].notnull().any(axis=1)]) / len(results)
        > 0.5
    )


def test_builder_exists():
    listing = scrape_property(
        location="18149 W Poston Dr, Surprise, AZ 85387",
        extra_property_data=False,
    )

    assert listing is not None
    assert listing["builder_name"].nunique() > 0


def test_phone_number_matching():
    searches = [
        scrape_property(
            location="Phoenix, AZ",
            listing_type="for_sale",
            limit=100,
        ),
        scrape_property(
            location="Phoenix, AZ",
            listing_type="for_sale",
            limit=100,
        ),
    ]

    assert all([search is not None for search in searches])

    #: random row
    row = searches[0][searches[0]["agent_phones"].notnull()].sample()

    #: find matching row
    matching_row = searches[1].loc[searches[1]["property_url"] == row["property_url"].values[0]]

    #: assert phone numbers are the same
    assert row["agent_phones"].values[0] == matching_row["agent_phones"].values[0]
