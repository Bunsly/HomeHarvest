from homeharvest import scrape_property
from datetime import datetime

# Generate filename based on current timestamp
current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"HomeHarvest_{current_timestamp}.csv"

properties = scrape_property(
    location="San Diego, CA",
    listing_type="sold",  # or (for_sale, for_rent)
    past_days=30,  # sold in last 30 days - listed in last x days if (for_sale, for_rent)
    # pending_or_contingent=True # use on for_sale listings to find pending / contingent listings
    # mls_only=True,  # only fetch MLS listings
    # proxy="http://user:pass@host:port"  # use a proxy to change your IP address
)
print(f"Number of properties: {len(properties)}")

# Export to csv
properties.to_csv(filename, index=False)
print(properties.head())
