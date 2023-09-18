# HomeHarvest

**HomeHarvest** aims to be the top Python real estate scraping library.

_**Under Consideration**: We're looking into the possibility of an Excel plugin to cater to a broader audience._

[![Try with Replit](https://replit.com/badge?caption=Try%20with%20Replit)](https://replit.com/@ZacharyHampton/HomeHarvestDemo)

## Installation

```bash
pip install --upgrade homeharvest
```

## Example Usage
```py
>>> from homeharvest import scrape_property
... properties = scrape_property(
...     location="85281", site_name="zillow", listing_type="for_rent"
... )

>>> properties.head()
                           address_one   city  ... mls_id description
0                 420 N  Scottsdale Rd  Tempe  ...    NaN         NaN
1                1255 E  University Dr  Tempe  ...    NaN         NaN
2              1979 E  Rio Salado Pkwy  Tempe  ...    NaN         NaN
3                      548 S Wilson St  Tempe  ...   None        None
4  945 E  Playa Del Norte Dr Unit 4027  Tempe  ...    NaN         NaN
[5 rows x 23 columns]
```

### Site Name Options

- `zillow`
- `redfin`
- `realtor.com`

### Listing Types

- `for_rent`
- `for_sale`
- `sold`
