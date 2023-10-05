import argparse
import datetime
from homeharvest import scrape_property


def main():
    parser = argparse.ArgumentParser(description="Home Harvest Property Scraper")
    parser.add_argument(
        "location", type=str, help="Location to scrape (e.g., San Francisco, CA)"
    )

    parser.add_argument(
        "-l",
        "--listing_type",
        type=str,
        default="for_sale",
        choices=["for_sale", "for_rent", "sold", "pending"],
        help="Listing type to scrape",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="excel",
        choices=["excel", "csv"],
        help="Output format",
    )

    parser.add_argument(
        "-f",
        "--filename",
        type=str,
        default=None,
        help="Name of the output file (without extension)",
    )

    parser.add_argument(
        "-p", "--proxy", type=str, default=None, help="Proxy to use for scraping"
    )
    parser.add_argument(
        "-d",
        "--days",
        type=int,
        default=None,
        help="Sold/listed in last _ days filter.",
    )

    parser.add_argument(
        "-r",
        "--radius",
        type=float,
        default=None,
        help="Get comparable properties within _ (eg. 0.0) miles. Only applicable for individual addresses.",
    )
    parser.add_argument(
        "-m",
        "--mls_only",
        action="store_true",
        help="If set, fetches only MLS listings.",
    )

    args = parser.parse_args()

    result = scrape_property(
        args.location,
        args.listing_type,
        radius=args.radius,
        proxy=args.proxy,
        mls_only=args.mls_only,
        past_days=args.days,
    )

    if not args.filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        args.filename = f"HomeHarvest_{timestamp}"

    if args.output == "excel":
        output_filename = f"{args.filename}.xlsx"
        result.to_excel(output_filename, index=False)
        print(f"Excel file saved as {output_filename}")
    elif args.output == "csv":
        output_filename = f"{args.filename}.csv"
        result.to_csv(output_filename, index=False)
        print(f"CSV file saved as {output_filename}")


if __name__ == "__main__":
    main()
