from homeharvest import scrape_property


def test_redfin():
    result = scrape_property(
        location="85001"
    )

    assert result is not None
