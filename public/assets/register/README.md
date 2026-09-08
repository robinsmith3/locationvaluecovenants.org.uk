# Using the LVC register model and UK map scripts

These two Python scripts let you build an illustrative annual postcode register
from your own rental evidence and plot one comparison class on an official UK
boundary:

- `lvc-register.py` builds the register and CSV outputs.
- `make-register-map.py` turns a register CSV into an SVG map.

They use only the Python standard library. Python 3.10 or later is recommended.
Neither script uses property selling prices.

## 1. Put the files in one working directory

Create a working directory containing:

```text
lvc-register.py
make-register-map.py
postcodes.csv
evidence.csv
ons-countries-dec-2024-bgc.geojson
```

Download the generalised, coastline-clipped GeoJSON from the ONS
[Countries (December 2024) Boundaries UK BGC](https://geoportal.statistics.gov.uk/datasets/ons::countries-december-2024-boundaries-uk-bgc-2/about)
page. The boundary file is needed only when generating a map.

## 2. Prepare the postcode spine

`postcodes.csv` must contain one row for every postcode to be included:

```csv
postcode,latitude,longitude,nation,region
OX1 1AA,51.7520,-1.2577,England,Oxford
CF10 1EP,51.4816,-3.1791,Wales,Cardiff
```

Use full unit postcodes. Latitude and longitude must be WGS84 decimal degrees.
For a real national exercise, obtain these from the current ONSPD or NSPL
postcode product and retain a dated copy of the postcode spine used for each
annual release.

## 3. Prepare the rental evidence

`evidence.csv` uses this schema:

```csv
postcode,use_class,property_type,bedroom_band,floor_area_sqm,annual_rent_gbp,year,source,quality_weight
OX1 1AA,residential,semi,3,88,22800,2026,achieved_rent,1
CF10 1EP,residential,flat,2,64,14400,2026,achieved_rent,1
```

Required meanings:

| Column | Meaning |
| --- | --- |
| `postcode` | Full unit postcode matching the postcode spine |
| `use_class` | `residential`, `commercial`, `agriculture` or `forestry` |
| `property_type` | One of the types listed below |
| `bedroom_band` | `1`, `2`, `3` or `4+` for residential; blank otherwise |
| `floor_area_sqm` | Property or land area in square metres |
| `annual_rent_gbp` | Annual rent in pounds, excluding separately identified services |
| `year` | Evidence year |
| `source` | Your source identifier for the audit trail |
| `quality_weight` | Relative weight; use `1` for normal evidence |

Allowed property types:

- Residential: `flat`, `terraced`, `semi`, `detached`
- Commercial: `retail`, `office`, `industrial`, `other`
- Agriculture: `arable`, `pasture`, `mixed`, `horticulture`, `other`
- Forestry: `commercial_woodland`, `amenity_conservation`, `other`

Agricultural or forestry evidence stated per hectare must be converted to an
annual total rent and an area in square metres. One hectare is 10,000 m².

## 4. Test the model with its synthetic demonstration

```bash
python lvc-register.py demo --year 2026 --output-dir demo-output
```

This creates example input files, the register, summary, manifest and two basic
SVG visualisations. Everything produced by `demo` is synthetic.

## 5. Build a register from your own data

```bash
python lvc-register.py build \
  --postcodes postcodes.csv \
  --evidence evidence.csv \
  --year 2026 \
  --output-dir output-2026
```

Important optional parameters and their defaults:

| Parameter | Default | Purpose |
| --- | ---: | --- |
| `--floor-quantile` | `0.10` | Sets the floor location within each comparison class |
| `--ceiling-quantile` | `0.90` | Caps the upper end of each comparison class |
| `--min-direct` | `5` | Observations required for confidence grade A |
| `--neighbours` | `6` | Maximum spatial donor postcodes |
| `--max-distance-km` | `120` | Maximum donor distance |
| `--distance-power` | `1.5` | Strength of distance weighting |

For example:

```bash
python lvc-register.py build \
  --postcodes postcodes.csv \
  --evidence evidence.csv \
  --year 2026 \
  --floor-quantile 0.10 \
  --ceiling-quantile 0.90 \
  --min-direct 8 \
  --neighbours 8 \
  --max-distance-km 80 \
  --distance-power 2 \
  --output-dir output-2026
```

Run `python lvc-register.py build --help` for the complete CLI reference.

## 6. Calculate annual LVC reassessment factors

Supply the previous annual register:

```bash
python lvc-register.py build \
  --postcodes postcodes.csv \
  --evidence evidence.csv \
  --previous-register output-2025/register_2025.csv \
  --year 2026 \
  --output-dir output-2026
```

The new register then includes `reassessment_factor` where a matching previous
postcode and comparison class exists:

```text
new LVC payment = existing LVC payment × reassessment_factor
```

Check postcode changes and class definitions before using a factor. A missing
factor means the script did not find an exact prior-year match.

## 7. Generate an accurate UK map

Map the default residential three-bedroom semi-detached class:

```bash
python make-register-map.py \
  --boundary ons-countries-dec-2024-bgc.geojson \
  --register output-2026/register_2026.csv \
  --output output-2026/map_2026.svg \
  --year 2026
```

Select a different comparison class and colour thresholds:

```bash
python make-register-map.py \
  --boundary ons-countries-dec-2024-bgc.geojson \
  --register output-2026/register_2026.csv \
  --output output-2026/detached-4-plus.svg \
  --year 2026 \
  --use-class residential \
  --property-type detached \
  --bedroom-band "4+" \
  --green-below 140 \
  --amber-below 210 \
  --title "Synthetic four-bedroom detached"
```

For commercial, agricultural or forestry classes, which have no bedroom band,
use `--bedroom-band none`:

```bash
python make-register-map.py \
  --boundary ons-countries-dec-2024-bgc.geojson \
  --register output-2026/register_2026.csv \
  --output output-2026/commercial-office.svg \
  --use-class commercial \
  --property-type office \
  --bedroom-band none \
  --title "Synthetic commercial office"
```

`--tolerance` controls boundary simplification and defaults to `0.012`
degrees. A smaller number preserves more coastline detail and creates a larger
SVG. Run `python make-register-map.py --help` for every option.

## 8. Interpret and check the outputs

The register CSV reports annual rent per m², floor, ceiling, bounded rent,
location excess over the floor, index level, evidence count, confidence grade,
estimation method and donor postcodes.

Before publication:

1. confirm the annual input snapshot and source licences;
2. inspect confidence grades C and D;
3. investigate abrupt changes across postcode boundaries;
4. review exceptional annual movements;
5. confirm map points lie inside the expected country;
6. record officer corrections without overwriting the original model output;
7. publish the model version and file checksum; and
8. label synthetic or provisional data prominently.

This is a transparent policy prototype, not an official valuation system.
Production use requires controlled record-level data, independent statistical
validation, formal governance and an appeals process.
