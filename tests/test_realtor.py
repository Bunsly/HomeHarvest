from homeharvest import scrape_property


def test_realtor():
    results = [
        scrape_property(location="2530 Al Lipscomb Way", site_name="realtor.com"),
        scrape_property(location="Phoenix, AZ", site_name="realtor.com"),  #: does not support "city, state, USA" format
        scrape_property(location="Dallas, TX", site_name="realtor.com"),  #: does not support "city, state, USA" format
        scrape_property(location="85281", site_name="realtor.com"),
    ]

    assert all([result is not None for result in results])
