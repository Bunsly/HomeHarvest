# HomeHarvest

**HomeHarvest** is a simple but comprehensive real estate scraping library.

[![Try with Replit](https://replit.com/badge?caption=Try%20with%20Replit)](https://replit.com/@ZacharyHampton/HomeHarvestDemo)


*Looking to build a data-focused software product?* **[Book a call](https://calendly.com/zachary-products/15min)** *to work with us.*
## Features


- Scrapes properties from **Zillow**, **Realtor.com** & **Redfin** simultaneously
- Aggregates the properties in a Pandas DataFrame

## Installation

```bash
pip install --upgrade homeharvest
```
  _Python version >= [3.10](https://www.python.org/downloads/release/python-3100/) required_ 
  
## Usage
```py
from homeharvest import scrape_property
import pandas as pd

properties: pd.DataFrame = scrape_property(
    site_name=["zillow", "realtor.com", "redfin"],
    location="85281",
    listing_type="for_rent" # for_sale / sold
)

#: Note, to export to CSV or Excel, use properties.to_csv() or properties.to_excel().
print(properties)


```
## Output
```py
>>> properties.head()
                           street   city  ... mls_id description
0                 420 N  Scottsdale Rd  Tempe  ...    NaN         NaN
1                1255 E  University Dr  Tempe  ...    NaN         NaN
2              1979 E  Rio Salado Pkwy  Tempe  ...    NaN         NaN
3                      548 S Wilson St  Tempe  ...   None        None
4  945 E  Playa Del Norte Dr Unit 4027  Tempe  ...    NaN         NaN
[5 rows x 23 columns]
```

### Parameters for `scrape_properties()`
```plaintext
Required
├── location (str): address in various formats e.g. just zip, full address, city/state, etc.
└── listing_type (enum): for_rent, for_sale, sold
Optional
├── site_name (List[enum], default=all three sites): zillow, realtor.com, redfin
```

### Property Schema
```plaintext
Property
├── Basic Information:
│   ├── property_url (str)
│   ├── site_name (enum): zillow, redfin, realtor.com
│   ├── listing_type (enum: ListingType)
│   └── property_type (enum): house, apartment, condo, townhouse, single_family, multi_family, building

├── Address Details:
│   ├── street_address (str)
│   ├── city (str)
│   ├── state (str)
│   ├── zip_code (str)
│   ├── unit (str)
│   └── country (str)

├── Property Features:
│   ├── price (int)
│   ├── tax_assessed_value (int)
│   ├── currency (str)
│   ├── square_feet (int)
│   ├── beds (int)
│   ├── baths (float)
│   ├── lot_area_value (float)
│   ├── lot_area_unit (str)
│   ├── stories (int)
│   └── year_built (int)

├── Miscellaneous Details:
│   ├── price_per_sqft (int)
│   ├── mls_id (str)
│   ├── agent_name (str)
│   ├── img_src (str)
│   ├── description (str)
│   ├── status_text (str)
│   ├── latitude (float)
│   ├── longitude (float)
│   └── posted_time (str) [Only for Zillow]

├── Building Details (for property_type: building):
│   ├── bldg_name (str)
│   ├── bldg_unit_count (int)
│   ├── bldg_min_beds (int)
│   ├── bldg_min_baths (float)
│   └── bldg_min_area (int)

└── Apartment Details (for property type: apartment):
    └── apt_min_price (int)
```
## Supported Countries for Property Scraping

* **Zillow**: contains listings in the **US** & **Canada** 
* **Realtor.com**: mainly from the **US** but also has international listings
* **Redfin**: listings mainly in the **US**, **Canada**, & has expanded to some areas in **Mexico**

### Exceptions
The following exceptions may be raised when using HomeHarvest:

- `InvalidSite` - valid options: `zillow`, `redfin`, `realtor.com`
- `InvalidListingType` - valid options: `for_sale`, `for_rent`, `sold`
- `NoResultsFound` - no properties found from your input
- `GeoCoordsNotFound` - if Zillow scraper is not able to create geo-coordinates from the location you input

## Frequently Asked Questions

---

**Q: Encountering issues with your queries?**  
**A:** Try a single site and/or broaden the location. If problems persist, [submit an issue](https://github.com/ZacharyHampton/HomeHarvest/issues).

---

**Q: Received a Forbidden 403 response code?**  
**A:** This indicates that you have been blocked by the real estate site for sending too many requests. Currently, **Zillow** is particularly aggressive with blocking. We recommend:

- Waiting a few seconds between requests.
- Trying a VPN to change your IP address.

---

