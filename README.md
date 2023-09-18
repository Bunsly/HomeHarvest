# HomeHarvest

**HomeHarvest** aims to be the top Python real estate scraping library.

_**Under Consideration**: We're looking into the possibility of an Excel plugin to cater to a broader audience._

## Installation

```bash
pip install --upgrade homeharvest
```

## Example Usage
```
from homeharvest import scrape_property

properties = scrape_property(
    location="85281", site_name="zillow", listing_type="for_rent"
)
print(properties)
```

### Site Name Options

- `zillow`
- `redfin`
- `realtor.com`

### Listing Types

- `for_rent`
- `for_sale`
- `sold`
