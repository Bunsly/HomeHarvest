from .core.scrapers.models import Property
import pandas as pd

ordered_properties = [
    "PropertyURL",
    "MLS",
    "MLS #",
    "Status",
    "Style",
    "Street",
    "Unit",
    "City",
    "State",
    "Zip",
    "Beds",
    "FB",
    "NumHB",
    "EstSF",
    "YrBlt",
    "ListPrice",
    "Lst Date",
    "Sold Price",
    "COEDate",
    "LotSFApx",
    "PrcSqft",
    "LATITUDE",
    "LONGITUDE",
    "Stories",
    "HOAFee",
    "PrkgGar",
    "Community",
]


def process_result(result: Property) -> pd.DataFrame:
    prop_data = {prop: None for prop in ordered_properties}
    prop_data.update(result.__dict__)
    prop_data["PropertyURL"] = prop_data["property_url"]
    prop_data["MLS"] = prop_data["mls"]
    prop_data["MLS #"] = prop_data["mls_id"]
    prop_data["Status"] = prop_data["status"]
    prop_data["Style"] = prop_data["style"]

    if "address" in prop_data:
        address_data = prop_data["address"]
        prop_data["Street"] = address_data.street
        prop_data["Unit"] = address_data.unit
        prop_data["City"] = address_data.city
        prop_data["State"] = address_data.state
        prop_data["Zip"] = address_data.zip

    prop_data["Community"] = prop_data["neighborhoods"]
    prop_data["Beds"] = prop_data["beds"]
    prop_data["FB"] = prop_data["baths_full"]
    prop_data["NumHB"] = prop_data["baths_half"]
    prop_data["EstSF"] = prop_data["est_sf"]
    prop_data["ListPrice"] = prop_data["list_price"]
    prop_data["Lst Date"] = prop_data["list_date"]
    prop_data["Sold Price"] = prop_data["sold_price"]
    prop_data["COEDate"] = prop_data["last_sold_date"]
    prop_data["LotSFApx"] = prop_data["lot_sf"]
    prop_data["HOAFee"] = prop_data["hoa_fee"]

    if prop_data.get("prc_sqft") is not None:
        prop_data["PrcSqft"] = round(prop_data["prc_sqft"], 2)

    prop_data["YrBlt"] = prop_data["yr_blt"]
    prop_data["LATITUDE"] = prop_data["latitude"]
    prop_data["LONGITUDE"] = prop_data["longitude"]
    prop_data["Stories"] = prop_data["stories"]
    prop_data["PrkgGar"] = prop_data["prkg_gar"]

    properties_df = pd.DataFrame([prop_data])
    properties_df = properties_df.reindex(columns=ordered_properties)

    return properties_df[ordered_properties]