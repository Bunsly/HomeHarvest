<img src="https://github.com/ZacharyHampton/HomeHarvest/assets/78247585/d1a2bf8b-09f5-4c57-b33a-0ada8a34f12d" width="400">

**HomeHarvest** is a simple, yet comprehensive, real estate scraping library that extracts and formats data in the style of MLS listings.

[![Try with Replit](https://replit.com/badge?caption=Try%20with%20Replit)](https://replit.com/@ZacharyHampton/HomeHarvestDemo)

**Not technical?** Try out the web scraping tool on our site at [tryhomeharvest.com](https://tryhomeharvest.com).

*Looking to build a data-focused software product?* **[Book a call](https://calendly.com/zachary-products/15min)** *to work with us.*

Check out another project we wrote: ***[JobSpy](https://github.com/cullenwatson/JobSpy)** – a Python package for job scraping*

## HomeHarvest Features

- **Source**: Fetches properties directly from **Realtor.com**.
- **Data Format**: Structures data to resemble MLS listings.
- **Export Flexibility**: Options to save as either CSV or Excel.
- **Usage Modes**:
  - **Python**: For those who'd like to integrate scraping into their Python scripts.
  - **CLI**: For users who prefer command-line operations.


[Video Guide for HomeHarvest](https://youtu.be/J1qgNPgmSLI) - _updated for release v0.3.4_

![homeharvest](https://github.com/ZacharyHampton/HomeHarvest/assets/78247585/b3d5d727-e67b-4a9f-85d8-1e65fd18620a)

## Installation

```bash
pip install homeharvest
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
  past_days=30,  # sold in last 30 days - listed in last x days if (for_sale, for_rent)
  # mls_only=True,  # only fetch MLS listings
  # proxy="http://user:pass@host:port"  # use a proxy to change your IP address
)
print(f"Number of properties: {len(properties)}")

# Export to csv
properties.to_csv(filename, index=False)
print(properties.head())
```

### CLI 

```
usage: homeharvest [-l {for_sale,for_rent,sold}] [-o {excel,csv}] [-f FILENAME] [-p PROXY] [-d DAYS] [-r RADIUS] [-m] [-c] location
                                                                                                                             
Home Harvest Property Scraper                                                                                                 
                                                                                                                             
positional arguments:                                                                                                         
  location              Location to scrape (e.g., San Francisco, CA)                                                          
                                                                                                                             
options:                                                                                                                      
  -l {for_sale,for_rent,sold,pending}, --listing_type {for_sale,for_rent,sold,pending}                                                        
                        Listing type to scrape                                                                                
  -o {excel,csv}, --output {excel,csv}                                                                                        
                        Output format                                                                                         
  -f FILENAME, --filename FILENAME                                                                                            
                        Name of the output file (without extension)                                                           
  -p PROXY, --proxy PROXY                                                                                                     
                        Proxy to use for scraping                                                                             
  -d DAYS, --days DAYS  Sold/listed in last _ days filter.                                                                           
  -r RADIUS, --radius RADIUS                                                                                                  
                        Get comparable properties within _ (e.g., 0.0) miles. Only applicable for individual addresses.        
  -m, --mls_only        If set, fetches only MLS listings.                                                                    
```
```bash
homeharvest "San Francisco, CA" -l for_rent -o excel -f HomeHarvest
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
├── mls_only (True/False): If set, fetches only MLS listings (mainly applicable to 'sold' listings)
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
- `NoResultsFound` - no properties found from your search
  
  
## Frequently Asked Questions
---

**Q: Encountering issues with your searches?**  
**A:** Try to broaden the parameters you're using. If problems persist, [submit an issue](https://github.com/ZacharyHampton/HomeHarvest/issues).

---

**Q: Received a Forbidden 403 response code?**  
**A:** This indicates that you have been blocked by Realtor.com for sending too many requests. We recommend:

- Waiting a few seconds between requests.
- Trying a VPN or useing a proxy as a parameter to scrape_property() to change your IP address.

---

