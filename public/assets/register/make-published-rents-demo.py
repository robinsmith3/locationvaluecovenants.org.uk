#!/usr/bin/env python3
"""Build the LVC sample from an ONS private-rent snapshot and an ONSPD postcode spine."""
from __future__ import annotations

import argparse
import csv
import math
import subprocess
import sys
from pathlib import Path

SOURCE_URL = (
    "https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/"
    "priceindexofprivaterentsukmonthlypricestatistics"
)

SCOTTISH_RENTAL_MARKET_AREA = {
    "Aberdeen City": "Aberdeen and Shire", "Aberdeenshire": "Aberdeen and Shire",
    "Argyll and Bute": "Argyll and Bute",
    "East Ayrshire": "Ayrshires", "North Ayrshire": "Ayrshires", "South Ayrshire": "Ayrshires",
    "Dumfries and Galloway": "Dumfries and Galloway",
    "Angus": "Dundee and Angus", "Dundee City": "Dundee and Angus",
    "East Dunbartonshire": "East Dunbartonshire", "Fife": "Fife",
    "Clackmannanshire": "Forth Valley", "Falkirk": "Forth Valley", "Stirling": "Forth Valley",
    "East Renfrewshire": "Greater Glasgow", "Glasgow City": "Greater Glasgow",
    "Highland": "Highland and Islands", "Moray": "Highland and Islands", "Na h-Eileanan Siar": "Highland and Islands",
    "Orkney Islands": "Highland and Islands", "Shetland Islands": "Highland and Islands",
    "City of Edinburgh": "Lothian", "East Lothian": "Lothian", "Midlothian": "Lothian",
    "North Lanarkshire": "North Lanarkshire", "Perth and Kinross": "Perth and Kinross",
    "Inverclyde": "Renfrewshire/Inverclyde", "Renfrewshire": "Renfrewshire/Inverclyde",
    "Scottish Borders": "Scottish Borders", "South Lanarkshire": "South Lanarkshire",
    "West Dunbartonshire": "West Dunbartonshire", "West Lothian": "West Lothian",
}


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def number(row, field):
    try:
        return float(row[field])
    except (KeyError, TypeError, ValueError):
        return None


def derived_monthly_rent(row):
    """Estimate the unpublished 3-bed/semi cross-tab from three published marginals."""
    all_rent = number(row, "Rental price")
    three_bed = number(row, "Rental price three bed")
    semi = number(row, "Rental price semidetached")
    if not all((all_rent, three_bed, semi)):
        return None
    return three_bed * semi / all_rent


def quantile(values, q):
    values = sorted(values)
    x = (len(values) - 1) * q
    low, high = math.floor(x), math.ceil(x)
    if low == high:
        return values[low]
    return values[low] * (high - x) + values[high] * (x - low)


def choose_source(postcode, by_code, by_name):
    code = postcode.get("local_authority_code", "")
    if code in by_code:
        return by_code[code], "local authority"
    rental_market_area = SCOTTISH_RENTAL_MARKET_AREA.get(postcode.get("local_authority_name", ""))
    if rental_market_area in by_name:
        return by_name[rental_market_area], "Scottish rental market area"
    region = postcode.get("region", "")
    if region in by_name:
        return by_name[region], "region"
    country_code = {"England": "E92000001", "Wales": "W92000004", "Scotland": "S92000003", "Northern Ireland": "N92000002"}.get(postcode.get("nation", ""))
    if country_code in by_code:
        return by_code[country_code], "country"
    raise ValueError(f"No usable published rent source for {postcode['postcode']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postcodes", default="postcodes-2026.csv")
    parser.add_argument("--rent-source", default="ons-private-rents-source-2026-08.csv")
    parser.add_argument("--model", default="lvc-register.py")
    parser.add_argument("--output-dir", default="published-output")
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--floor-area-sqm", type=float, default=90.0,
                        help="Assumed representative floor area for a three-bedroom semi")
    parser.add_argument("--floor-quantile", type=float, default=0.10)
    parser.add_argument("--ceiling-quantile", type=float, default=0.90)
    args = parser.parse_args()
    if args.floor_area_sqm <= 0:
        raise SystemExit("--floor-area-sqm must be positive")

    postcodes = read_csv(args.postcodes)
    rents = read_csv(args.rent_source)
    by_code = {row["Area code"]: row for row in rents}
    by_name = {row["Area name"]: row for row in rents}
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    evidence = []
    for postcode in postcodes:
        source, geography_level = choose_source(postcode, by_code, by_name)
        estimate = derived_monthly_rent(source)
        if estimate is None:
            raise ValueError(f"Incomplete source measures for {source['Area name']}")
        evidence.append({
            "postcode": postcode["postcode"],
            "use_class": "residential",
            "property_type": "semi",
            "bedroom_band": "3",
            "floor_area_sqm": f"{args.floor_area_sqm:.2f}",
            "annual_rent_gbp": f"{estimate * 12:.2f}",
            "year": args.year,
            "source": "ONS Price Index of Private Rents",
            "quality_weight": "1",
            "confidence_grade_override": "P",
            "method_override": "published_area_modelled_postcode",
            "estimated": "yes",
            "source_release": "19 August 2026",
            "source_period": source["Time period"],
            "source_url": SOURCE_URL,
            "source_geography_code": source["Area code"],
            "source_geography_name": source["Area name"],
            "source_geography_level": geography_level,
            "published_monthly_all_rent_gbp": source["Rental price"],
            "published_monthly_three_bed_rent_gbp": source["Rental price three bed"],
            "published_monthly_semidetached_rent_gbp": source["Rental price semidetached"],
            "estimated_monthly_three_bed_semi_rent_gbp": f"{estimate:.2f}",
            "floor_area_status": "user-adjustable assumption; not observed for this postcode",
            "combination_method": "three-bed rent x semi-detached rent / all-property rent",
        })

    evidence_path = output / f"evidence_{args.year}.csv"
    write_csv(evidence_path, evidence, list(evidence[0]))

    # Set UK thresholds from unique published GB local-authority estimates, plus the
    # latest usable Northern Ireland national estimate. This avoids weighting the
    # threshold by however many sample postcodes happen to be selected in each area.
    population = []
    for row in rents:
        code = row["Area code"]
        if code.startswith(("E06", "E07", "E08", "E09", "W06", "S12")) or code == "N92000002":
            monthly = derived_monthly_rent(row)
            if monthly is not None:
                population.append(monthly * 12 / args.floor_area_sqm)
    floor_value = quantile(population, args.floor_quantile)
    ceiling_value = quantile(population, args.ceiling_quantile)

    command = [
        sys.executable, args.model, "build",
        "--postcodes", args.postcodes,
        "--evidence", str(evidence_path),
        "--year", str(args.year),
        "--floor-value", str(floor_value),
        "--ceiling-value", str(ceiling_value),
        "--output-dir", str(output),
    ]
    subprocess.run(command, check=True)
    print(f"Published-source areas used for thresholds: {len(population)}")
    print(f"Floor £{floor_value:.4f}/m2/year; ceiling £{ceiling_value:.4f}/m2/year")


if __name__ == "__main__":
    main()
