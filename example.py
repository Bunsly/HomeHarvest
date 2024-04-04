from homeharvest import scrape_property
import pandas as pd

properties: pd.DataFrame = scrape_property(
    site_name=["redfin"],
    location="85281",
    listing_type="for_rent" # for_sale / sold
)

print(properties)
properties.to_csv('properties.csv', index=False)
