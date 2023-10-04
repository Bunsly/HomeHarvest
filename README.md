<img src="https://github.com/ZacharyHampton/HomeHarvest/assets/78247585/d1a2bf8b-09f5-4c57-b33a-0ada8a34f12d" width="400">

**HomeHarvest** is a simple, yet comprehensive, real estate scraping library that extracts and formats data in the style of MLS listings.

[![Try with Replit](https://replit.com/badge?caption=Try%20with%20Replit)](https://replit.com/@ZacharyHampton/HomeHarvestDemo)

\
**Not technical?** Try out the web scraping tool on our site at [tryhomeharvest.com](https://tryhomeharvest.com).

*Looking to build a data-focused software product?* **[Book a call](https://calendly.com/zachary-products/15min)** *to work with us.*

Check out another project we wrote: ***[JobSpy](https://github.com/cullenwatson/JobSpy)** – a Python package for job scraping*

## HomeHarvest Features

- **Source**: Fetches properties directly from **Realtor.com**.
- **Data Format**: Structures data to resemble MLS listings.
- **Export Flexibility**: Options to save as either CSV or Excel.
- **Usage Modes**:
  - **CLI**: For users who prefer command-line operations.
  - **Python**: For those who'd like to integrate scraping into their Python scripts.

[Video Guide for HomeHarvest](https://youtu.be/JnV7eR2Ve2o) - _updated for release v0.2.7_

![homeharvest](https://github.com/ZacharyHampton/HomeHarvest/assets/78247585/b3d5d727-e67b-4a9f-85d8-1e65fd18620a)

## Installation

```bash
pip install homeharvest
```
  _Python version >= [3.10](https://www.python.org/downloads/release/python-3100/) required_ 

## Usage

### CLI 

```
usage: homeharvest [-h] [-l {for_sale,for_rent,sold}] [-o {excel,csv}] [-f FILENAME] [-p PROXY] [-d DAYS] [-r RADIUS] location
                                                                                                                              
Home Harvest Property Scraper                                                                                                 
                                                                                                                              
positional arguments:                                                                                                         
  location              Location to scrape (e.g., San Francisco, CA)                                                          
                                                                                                                              
options:                                                                                                                      
  -l {for_sale,for_rent,sold}, --listing_type {for_sale,for_rent,sold}                                                        
                        Listing type to scrape                                                                                
  -o {excel,csv}, --output {excel,csv}                                                                                        
                        Output format                                                                                         
  -f FILENAME, --filename FILENAME                                                                                            
                        Name of the output file (without extension)                                                           
  -p PROXY, --proxy PROXY                                                                                                     
                        Proxy to use for scraping                                                                             
  -d DAYS, --days DAYS  Sold in last _ days filter.                                                                           
  -r RADIUS, --radius RADIUS                                                                                                  
                        Get comparable properties within _ (eg. 0.0) miles. Only applicable for individual addresses.
```
```bash
> homeharvest "San Francisco, CA" -l for_rent -o excel -f HomeHarvest
```

### Python 

```py
from homeharvest import scrape_property
from datetime import datetime

# Generate filename based on current timestamp
current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"output/{current_timestamp}.csv"

properties = scrape_property(
    location="San Diego, CA",
    listing_type="sold", # for_sale, for_rent
)
print(f"Number of properties: {len(properties)}")
properties.to_csv(filename, index=False)
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
├── location (str): address in various formats e.g. just zip, full address, city/state, etc.
└── listing_type (enum): for_rent, for_sale, sold
Optional
├── radius_for_comps (float): Radius in miles to find comparable properties based on individual addresses.
├── sold_last_x_days (int): Number of past days to filter sold properties.
├── proxy (str): in format 'http://user:pass@host:port'
```
### Property Schema
```plaintext
Property
├── Basic Information:
│ ├── property_url (str)
│ ├── mls (str)
│ ├── mls_id (str)
│ └── status (str)

├── Address Details:
│ ├── street (str)
│ ├── unit (str)
│ ├── city (str)
│ ├── state (str)
│ └── zip (str)

├── Property Description:
│ ├── style (str)
│ ├── beds (int)
│ ├── baths_full (int)
│ ├── baths_half (int)
│ ├── sqft (int)
│ ├── lot_sqft (int)
│ ├── sold_price (int)
│ ├── year_built (int)
│ ├── garage (float)
│ └── stories (int)

├── Property Listing Details:
│ ├── list_price (int)
│ ├── list_date (str)
│ ├── last_sold_date (str)
│ ├── prc_sqft (int)
│ └── hoa_fee (int)

├── Location Details:
│ ├── latitude (float)
│ ├── longitude (float)
│ └── neighborhoods (str)
```
## Supported Countries for Property Scraping

* **Realtor.com**: mainly from the **US** but also has international listings

### Exceptions
The following exceptions may be raised when using HomeHarvest:

- `InvalidListingType` - valid options: `for_sale`, `for_rent`, `sold`
- `NoResultsFound` - no properties found from your input

## Frequently Asked Questions
---

**Q: Encountering issues with your searches?**  
**A:** Try to broaden the location. If problems persist, [submit an issue](https://github.com/ZacharyHampton/HomeHarvest/issues).

---

**Q: Received a Forbidden 403 response code?**  
**A:** This indicates that you have been blocked by Realtor.com for sending too many requests. We recommend:

- Waiting a few seconds between requests.
- Trying a VPN to change your IP address.

---

