from homeharvest import scrape_property
from datetime import datetime

# Generate filename based on current timestamp
current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"HomeHarvest_{current_timestamp}.csv"

properties = scrape_property(
    location="8134 midway rd dallas tx 75209",
    listing_type="pending",  # or (for_sale, for_rent, pending)
    radius=0.5
    # past_days=30,  # sold in last 30 days - listed in last 30 days if (for_sale, for_rent)

    # date_from="2023-05-01", # alternative to past_days
    # date_to="2023-05-28",

    # mls_only=True,  # only fetch MLS listings
    # proxy="http://user:pass@host:port"  # use a proxy to change your IP address
)
print(f"Number of properties: {len(properties)}")

# Export to csv
properties.to_csv(filename, index=False)
print(properties.head())