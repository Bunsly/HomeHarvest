# HomeHarvest

**HomeHarvest** aims to be the top Python real estate scraping library.

## RoadMap

- **Supported Sites**: Currently, we support scraping from sites such as `Zillow` and `RedFin`.
- **Output**: Provides the option to return the scraped data as a Pandas dataframe.
- **Under Consideration**: We're looking into the possibility of an Excel plugin to cater to a broader audience.

## Site Name Options

- `zillow`
- `redfin`

## Listing Types

- `for_rent`
- `for_sale`

### Installation

```bash
pip install --upgrade homeharvest
```

### Example Usage
```
from homeharvest import scrape_property

properties = scrape_property(
    location="85281", site_name="zillow", listing_type="for_rent"
)
print(properties)
```
