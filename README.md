<img src="https://github.com/ZacharyHampton/HomeHarvest/assets/78247585/d1a2bf8b-09f5-4c57-b33a-0ada8a34f12d" width="400">

**HomeHarvest** is a real estate scraping library that extracts and formats data in the style of MLS listings.

**Not technical?** Try out the web scraping tool on our site at [tryhomeharvest.com](https://tryhomeharvest.com).

*Looking to build a data-focused software product?* **[Book a call](https://bunsly.com)** *to work with us.*

## HomeHarvest Features

- **Source**: Fetches properties directly from **Realtor.com**.
- **Data Format**: Structures data to resemble MLS listings.
- **Export Flexibility**: Options to save as either CSV or Excel.

[Video Guide for HomeHarvest](https://youtu.be/J1qgNPgmSLI) - _updated for release v0.3.4_

![homeharvest](https://github.com/ZacharyHampton/HomeHarvest/assets/78247585/b3d5d727-e67b-4a9f-85d8-1e65fd18620a)

## Installation

```bash
pip install -U homeharvest
```
  _Python version >= [3.10](https://www.python.org/downloads/release/python-3100/) required_ 

## Usage

### Python

```py
from homeharvest import scrape_property
from datetime import datetime

# Generate filename based on current timestamp
current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"HomeHarvest_{current_timestamp}.csv"

properties = scrape_property(
  location="San Diego, CA",
  listing_type="sold",  # or (for_sale, for_rent, pending)
  past_days=30,  # sold in last 30 days - listed in last 30 days if (for_sale, for_rent)
  
  # date_from="2023-05-01", # alternative to past_days 
  # date_to="2023-05-28", 
  # foreclosure=True
  
  # mls_only=True,  # only fetch MLS listings
)
print(f"Number of properties: {len(properties)}")

# Export to csv
properties.to_csv(filename, index=False)
print(properties.head())
```

## Output
```plaintext
>>> properties.head()
    MLS       MLS # Status          Style  ...     COEDate LotSFApx PrcSqft Stories
0  SDCA   230018348   SOLD         CONDOS  ...  2023-10-03   290110     803       2
1  SDCA   230016614   SOLD      TOWNHOMES  ...  2023-10-03     None     838       3
2  SDCA   230016367   SOLD         CONDOS  ...  2023-10-03    30056     649       1
3  MRCA  NDP2306335   SOLD  SINGLE_FAMILY  ...  2023-10-03     7519     661       2
4  SDCA   230014532   SOLD         CONDOS  ...  2023-10-03     None     752       1
[5 rows x 22 columns]
```

### Parameters for `scrape_property()`
```
Required
├── location (str): The address in various formats - this could be just a zip code, a full address, or city/state, etc.
└── listing_type (option): Choose the type of listing.
    - 'for_rent'
    - 'for_sale'
    - 'sold'
    - 'pending'

Optional
├── radius (decimal): Radius in miles to find comparable properties based on individual addresses.
│    Example: 5.5 (fetches properties within a 5.5-mile radius if location is set to a specific address; otherwise, ignored)
│
├── past_days (integer): Number of past days to filter properties. Utilizes 'last_sold_date' for 'sold' listing types, and 'list_date' for others (for_rent, for_sale).
│    Example: 30 (fetches properties listed/sold in the last 30 days)
│
├── date_from, date_to (string): Start and end dates to filter properties listed or sold, both dates are required.
|    (use this to get properties in chunks as there's a 10k result limit)
│    Format for both must be "YYYY-MM-DD". 
│    Example: "2023-05-01", "2023-05-15" (fetches properties listed/sold between these dates)
│
├── mls_only (True/False): If set, fetches only MLS listings (mainly applicable to 'sold' listings)
│
├── foreclosure (True/False): If set, fetches only foreclosures
│
└── proxy (string): In format 'http://user:pass@host:port'
```

### Property Schema
```plaintext
Property
├── Basic Information:
│ ├── property_url
│ ├── mls
│ ├── mls_id
│ └── status

├── Address Details:
│ ├── street
│ ├── unit
│ ├── city
│ ├── state
│ └── zip_code

├── Property Description:
│ ├── style
│ ├── beds
│ ├── full_baths
│ ├── half_baths
│ ├── sqft
│ ├── year_built
│ ├── stories
│ └── lot_sqft

├── Property Listing Details:
│ ├── days_on_mls
│ ├── list_price
│ ├── list_date
│ ├── pending_date
│ ├── sold_price
│ ├── last_sold_date
│ ├── price_per_sqft
│ └── hoa_fee

├── Location Details:
│ ├── latitude
│ ├── longitude

└── Parking Details:
    └── parking_garage
```

### Exceptions
The following exceptions may be raised when using HomeHarvest:

- `InvalidListingType` - valid options: `for_sale`, `for_rent`, `sold`
- `InvalidDate` - date_from or date_to is not in the format YYYY-MM-DD
  
