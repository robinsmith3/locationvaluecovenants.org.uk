#!/usr/bin/env python3
"""Render the synthetic LVC points over an official ONS UK country boundary."""
from __future__ import annotations

import argparse
import csv
import html
import json
import math
from pathlib import Path

SOURCE_TITLE = "Countries (December 2024) Boundaries UK BGC"
SOURCE_URL = "https://geoportal.statistics.gov.uk/datasets/ons::countries-december-2024-boundaries-uk-bgc-2/about"


def perpendicular_distance(point, start, end):
    if start == end:
        return math.dist(point, start)
    x, y = point
    x1, y1 = start
    x2, y2 = end
    return abs((y2-y1)*x-(x2-x1)*y+x2*y1-y2*x1) / math.hypot(y2-y1, x2-x1)


def simplify(points, tolerance):
    if len(points) <= 2:
        return points
    furthest, index = 0.0, 0
    for i in range(1, len(points)-1):
        distance = perpendicular_distance(points[i], points[0], points[-1])
        if distance > furthest:
            furthest, index = distance, i
    if furthest > tolerance:
        return simplify(points[:index+1], tolerance)[:-1] + simplify(points[index:], tolerance)
    return [points[0], points[-1]]


def rings(geometry):
    coordinates = geometry["coordinates"]
    polygons = coordinates if geometry["type"] == "MultiPolygon" else [coordinates]
    for polygon in polygons:
        for ring in polygon:
            yield [(float(lon), float(lat)) for lon, lat, *_ in ring]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--boundary", required=True)
    parser.add_argument("--register", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--tolerance", type=float, default=0.012)
    parser.add_argument("--use-class", default="residential")
    parser.add_argument("--property-type", default="semi")
    parser.add_argument("--bedroom-band", default="3",
                        help="Use 'none' for schedules without bedrooms")
    parser.add_argument("--green-below", type=float, default=150)
    parser.add_argument("--amber-below", type=float, default=225)
    parser.add_argument("--title",
                        help="Map title; defaults to the selected comparison class")
    args = parser.parse_args()

    boundary = json.loads(Path(args.boundary).read_text(encoding="utf-8"))
    features = [f for f in boundary["features"] if f["properties"]["CTRY24CD"] in {
        "E92000001", "N92000002", "S92000003", "W92000004"
    }]

    min_lon, max_lon, min_lat, max_lat = -8.75, 1.85, 49.75, 60.92
    width, height = 650, 820
    left, top, plot_w, plot_h = 54, 58, 500, 680
    lon_scale = math.cos(math.radians(55))

    def project(lon, lat):
        scaled_min = min_lon * lon_scale
        scaled_max = max_lon * lon_scale
        x = left + (lon*lon_scale-scaled_min)/(scaled_max-scaled_min)*plot_w
        y = top + (max_lat-lat)/(max_lat-min_lat)*plot_h
        return x, y

    country_paths = []
    for feature in features:
        name = feature["properties"]["CTRY24NM"]
        commands = []
        for ring in rings(feature["geometry"]):
            reduced = simplify(ring, args.tolerance)
            if len(reduced) < 3:
                continue
            projected = [project(*point) for point in reduced]
            # Ignore sub-pixel rocks while retaining inhabited and recognisable islands.
            xs, ys = zip(*projected)
            if (max(xs)-min(xs))*(max(ys)-min(ys)) < 0.6:
                continue
            commands.append("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in projected) + " Z")
        country_paths.append(
            f'<path d="{" ".join(commands)}" fill="#dfe9e3" stroke="#617b70" '
            f'stroke-width="1.1" vector-effect="non-scaling-stroke"><title>{html.escape(name)}</title></path>'
        )

    selected_bedroom = "" if args.bedroom_band.lower() == "none" else args.bedroom_band
    if args.title:
        map_title = args.title
    elif args.use_class == "residential":
        type_label = {
            "semi": "semi-detached",
            "detached": "detached",
            "terraced": "terraced",
            "flat": "flat",
        }.get(args.property_type, args.property_type.replace("_", " "))
        map_title = f"Synthetic {selected_bedroom}-bedroom {type_label}"
    else:
        map_title = f"Synthetic {args.property_type.replace('_', ' ')} {args.use_class}"

    points = []
    with open(args.register, newline="", encoding="utf-8-sig") as source:
        for row in csv.DictReader(source):
            if not (
                row["use_class"] == args.use_class
                and row["property_type"] == args.property_type
                and row["bedroom_band"] == selected_bedroom
            ):
                continue
            lon, lat = float(row["longitude"]), float(row["latitude"])
            index = float(row["index_level"])
            colour = "#1b5e20" if index < args.green_below else "#d98900" if index < args.amber_below else "#b71c1c"
            x, y = project(lon, lat)
            label = html.escape(f'{row["postcode"]}: index {index:.1f}')
            points.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.2" fill="{colour}" '
                f'stroke="#ffffff" stroke-width="1.4"><title>{label}</title></circle>'
            )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
<title id="title">{html.escape(map_title)} location index</title>
<desc id="description">Synthetic postcode index points plotted on official ONS December 2024 boundaries for England, Wales, Scotland and Northern Ireland. The floor location is index 100.</desc>
<metadata>Boundary source: Office for National Statistics, Countries (December 2024) Boundaries UK BGC. Contains public sector information licensed under the Open Government Licence v3.0.</metadata>
<rect width="100%" height="100%" fill="#f7faf8"/>
<text x="28" y="29" font-family="system-ui,sans-serif" font-size="18" font-weight="700" fill="#162b31">{html.escape(map_title)}</text>
<text x="28" y="49" font-family="system-ui,sans-serif" font-size="14" fill="#53676c">location-rental index — {args.year}</text>
<g>{"".join(country_paths)}</g>
<g>{"".join(points)}</g>
<g font-family="system-ui,sans-serif" font-size="12" fill="#31484d">
  <circle cx="48" cy="775" r="5" fill="#1b5e20"/><text x="61" y="779">Below {args.green_below:g}</text>
  <circle cx="157" cy="775" r="5" fill="#d98900"/><text x="170" y="779">{args.green_below:g}–{args.amber_below-1:g}</text>
  <circle cx="275" cy="775" r="5" fill="#b71c1c"/><text x="288" y="779">{args.amber_below:g} or above</text>
  <text x="48" y="801" fill="#66787b">Floor location = 100 · synthetic values, not actual postcode assessments</text>
</g>
</svg>'''
    if not points:
        raise SystemExit("No register rows matched the requested comparison class")
    Path(args.output).write_text(svg, encoding="utf-8")
    print(f"Wrote {args.output} using {SOURCE_TITLE}")


if __name__ == "__main__":
    main()
