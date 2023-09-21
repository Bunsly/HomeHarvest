<img src="https://github.com/ZacharyHampton/HomeHarvest/assets/78247585/d1a2bf8b-09f5-4c57-b33a-0ada8a34f12d" width="400">

**HomeHarvest** is a simple, yet comprehensive, real estate scraping library.

[![Try with Replit](https://replit.com/badge?caption=Try%20with%20Replit)](https://replit.com/@ZacharyHampton/HomeHarvestDemo)

\
**Not technical?** Try out the web scraping tool on our site at [tryhomeharvest.com](https://tryhomeharvest.com).

*Looking to build a data-focused software product?* **[Book a call](https://calendly.com/zachary-products/15min)** *to work with us.*

Check out another project we wrote: ***[JobSpy](https://github.com/cullenwatson/JobSpy)** – a Python package for job scraping*

## Features

- Scrapes properties from **Zillow**, **Realtor.com** & **Redfin** simultaneously
- Aggregates the properties in a Pandas DataFrame

[Video Guide for HomeHarvest](https://youtu.be/JnV7eR2Ve2o) - _updated for release v0.2.7_

![homeharvest](https://github.com/ZacharyHampton/HomeHarvest/assets/78247585/b3d5d727-e67b-4a9f-85d8-1e65fd18620a)

## Installation

```bash
pip install homeharvest
```
  _Python version >= [3.10](https://www.python.org/downloads/release/python-3100/) required_ 

## Usage

### CLI 

```bash
homeharvest "San Francisco, CA" -s zillow realtor.com redfin -l for_rent -o excel -f HomeHarvest
```

This will scrape properties from the specified sites for the given location and listing type, and save the results to an Excel file named `HomeHarvest.xlsx`.

By default:
- If `-s` or `--site_name` is not provided, it will scrape from all available sites.
- If `-l` or `--listing_type` is left blank, the default is `for_sale`. Other options are `for_rent` or `sold`.
- The `-o` or `--output` default format is `excel`. Options are `csv` or `excel`.
- If `-f` or `--filename` is left blank, the default is `HomeHarvest_<current_timestamp>`.
- If `-p` or `--proxy` is not provided, the scraper uses the local IP.
- Use `-k` or `--keep_duplicates` to keep duplicate properties based on address. If not provided, duplicates will be removed.
### Python 

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
                                        property_url site_name listing_type  apt_min_price  apt_max_price   ...  
0  https://www.redfin.com/AZ/Tempe/1003-W-Washing...    redfin     for_rent         1666.0         2750.0   ... 
1  https://www.redfin.com/AZ/Tempe/VELA-at-Town-L...    redfin     for_rent         1665.0         3763.0   ...  
2  https://www.redfin.com/AZ/Tempe/Camden-Tempe/a...    redfin     for_rent         1939.0         3109.0   ...  
3  https://www.redfin.com/AZ/Tempe/Emerson-Park/a...    redfin     for_rent         1185.0         1817.0   ... 
4  https://www.redfin.com/AZ/Tempe/Rio-Paradiso-A...    redfin     for_rent         1470.0         2235.0   ...   
[5 rows x 41 columns]
```

### Parameters for `scrape_properties()`
```plaintext
Required
├── location (str): address in various formats e.g. just zip, full address, city/state, etc.
└── listing_type (enum): for_rent, for_sale, sold
Optional
├── site_name (list[enum], default=all three sites): zillow, realtor.com, redfin
├── proxy (str): in format 'http://user:pass@host:port' or [https, socks]
└── keep_duplicates (bool, default=False): whether to keep or remove duplicate properties based on address
```

### Property Schema
```plaintext
Property
├── Basic Information:
│   ├── property_url (str)
│   ├── site_name (enum): zillow, redfin, realtor.com
│   ├── listing_type (enum): for_sale, for_rent, sold
│   └── property_type (enum): house, apartment, condo, townhouse, single_family, multi_family, building

├── Address Details:
│   ├── street_address (str)
│   ├── city (str)
│   ├── state (str)
│   ├── zip_code (str)
│   ├── unit (str)
│   └── country (str)

├── House for Sale Features:
│   ├── tax_assessed_value (int)
│   ├── lot_area_value (float)
│   ├── lot_area_unit (str)
│   ├── stories (int)
│   ├── year_built (int)
│   └── price_per_sqft (int)

├── Building for Sale and Apartment Details:
│   ├── bldg_name (str)
│   ├── beds_min (int)
│   ├── beds_max (int)
│   ├── baths_min (float)
│   ├── baths_max (float)
│   ├── sqft_min (int)
│   ├── sqft_max (int)
│   ├── price_min (int)
│   ├── price_max (int)
│   ├── area_min (int)
│   └── unit_count (int)

├── Miscellaneous Details:
│   ├── mls_id (str)
│   ├── agent_name (str)
│   ├── img_src (str)
│   ├── description (str)
│   ├── status_text (str)
│   └── posted_time (str)

└── Location Details:
    ├── latitude (float)
    └── longitude (float)
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
- `GeoCoordsNotFound` - if Zillow scraper is not able to derive geo-coordinates from the location you input

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

