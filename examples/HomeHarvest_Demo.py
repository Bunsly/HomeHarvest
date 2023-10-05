from homeharvest import scrape_property
from datetime import datetime

# Generate filename based on current timestamp
current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"output/{current_timestamp}.csv"

properties = scrape_property(
    location="San Diego, CA",
    listing_type="sold", # for_sale, for_rent
    property_younger_than=30, # sold/listed in last 30 days
    mls_only=True, # only fetch MLS listings
)
print(f"Number of properties: {len(properties)}")

# Export to csv
properties.to_csv(filename, index=False)
print(properties.head())