from homeharvest import scrape_property


def test_realtor():
    result = scrape_property(
        location="85281",
        site_name="realtor.com"
    )

    assert result is not None
