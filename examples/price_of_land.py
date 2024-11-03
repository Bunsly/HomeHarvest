"""
This script scrapes sold and pending sold land listings in past year for a list of zip codes and saves the data to individual Excel files.
It adds two columns to the data: 'lot_acres' and 'ppa' (price per acre) for user to analyze average price of land in a zip code.
"""

import os
import pandas as pd
from homeharvest import scrape_property


def get_property_details(zip: str, listing_type):
    properties = scrape_property(location=zip, listing_type=listing_type, property_type=["land"], past_days=365)
    if not properties.empty:
        properties["lot_acres"] = properties["lot_sqft"].apply(lambda x: x / 43560 if pd.notnull(x) else None)

        properties = properties[properties["sqft"].isnull()]
        properties["ppa"] = properties.apply(
            lambda row: (
                int(
                    (
                        row["sold_price"]
                        if (pd.notnull(row["sold_price"]) and row["status"] == "SOLD")
                        else row["list_price"]
                    )
                    / row["lot_acres"]
                )
                if pd.notnull(row["lot_acres"])
                and row["lot_acres"] > 0
                and (pd.notnull(row["sold_price"]) or pd.notnull(row["list_price"]))
                else None
            ),
            axis=1,
        )
        properties["ppa"] = properties["ppa"].astype("Int64")
        selected_columns = [
            "property_url",
            "property_id",
            "style",
            "status",
            "street",
            "city",
            "state",
            "zip_code",
            "county",
            "list_date",
            "last_sold_date",
            "list_price",
            "sold_price",
            "lot_sqft",
            "lot_acres",
            "ppa",
        ]
        properties = properties[selected_columns]
    return properties


def output_to_excel(zip_code, sold_df, pending_df):
    root_folder = os.getcwd()
    zip_folder = os.path.join(root_folder, "zips", zip_code)

    # Create zip code folder if it doesn't exist
    os.makedirs(zip_folder, exist_ok=True)

    # Define file paths
    sold_file = os.path.join(zip_folder, f"{zip_code}_sold.xlsx")
    pending_file = os.path.join(zip_folder, f"{zip_code}_pending.xlsx")

    # Save individual sold and pending files
    sold_df.to_excel(sold_file, index=False)
    pending_df.to_excel(pending_file, index=False)


zip_codes = map(
    str,
    [
        22920,
        77024,
        78028,
        24553,
        22967,
        22971,
        22922,
        22958,
        22969,
        22949,
        22938,
        24599,
        24562,
        22976,
        24464,
        22964,
        24581,
    ],
)

combined_df = pd.DataFrame()
for zip in zip_codes:
    sold_df = get_property_details(zip, "sold")
    pending_df = get_property_details(zip, "pending")
    combined_df = pd.concat([combined_df, sold_df, pending_df], ignore_index=True)
    output_to_excel(zip, sold_df, pending_df)

combined_file = os.path.join(os.getcwd(), "zips", "combined.xlsx")
combined_df.to_excel(combined_file, index=False)
