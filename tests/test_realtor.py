from homeharvest import scrape_property


def test_realtor():
    results = [
        scrape_property(
            location="85281",
            site_name="realtor.com"
        ),
    ]

    assert all([result is not None for result in results])
