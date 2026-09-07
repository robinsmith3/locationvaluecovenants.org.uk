# Method for an annual National Location Rental Value Register

## 1. Purpose and legal object

The register supplies an annual **location-rental index** for reassessing an
LVC payment already agreed and registered. It does not determine the original
property selling price, reconstruct a hypothetical vacant-site sale, or value
the individual plot before the covenant. The initial covenant payment comes
from the transaction or policy that created it; subsequent payments move by the
published index for the property's postcode and comparison class.

For covenant `c` in postcode `p`, comparison class `k` and year `t`:

`payment(c,t) = payment(c,base) × index(p,k,t) / index(p,k,base)`

This preserves the LVC design already used in the Location Value Covenant
briefings: a voluntary, debt-free obligation attached to property whose payment
is subsequently linked to local rental value.

## 2. Statistical unit and classification

The minimum published partition is the live **unit postcode**. A postcode is a
reference key, not a claim that every address within it is identical. Historic
postcode identifiers must be retained because postcodes change and can be
re-used.

Keep the comparison classes deliberately few:

| Schedule | Primary types | Size control |
|---|---|---|
| Residential | flat, terraced, semi, detached | 1, 2, 3, 4+ bedrooms and m² |
| Commercial | retail, office, industrial, other | m² plus use/lease controls |
| Agriculture | arable, pasture, mixed, horticulture, other | m², grade and tenancy |
| Forestry | commercial woodland, amenity/conservation, other | m², species/age/access controls |

All published monetary values use annual pounds per square metre. Agricultural
source data reported per hectare are divided by 10,000. Bedrooms and type are
controls for like-for-like comparison; floor area is the common denominator.

## 3. Why three non-residential schedules need special treatment

Commercial property cannot safely share the residential model: lease length,
rent-free periods, repairing obligations, permitted use, frontage, access and
business-rate valuation conventions materially affect observed rent.

Agriculture and forestry require separate schedules from both residential and
commercial property. Their rent reflects productive capacity, soil/land grade,
water, access, tenancy terms, buildings, subsidy or environmental obligations,
and—in forestry—rotation age and species. A farm or forest may also cross many
postcodes. Allocate it to mapped land parcels, remove dwelling/building rent,
and aggregate parcel results back to the holding. Never infer farmland value
from nearby house rent.

## 4. Source hierarchy

Use lawful record-level data under common definitions, retaining source and
quality weights:

1. **Residential achieved rents:** the rent-officer/agency administrative
   records underpinning ONS PIPR; devolved-nation equivalents; registered
   tenancy/deposit and housing-benefit records where lawful.
2. **Residential attributes:** EPC floor area and age; address/property
   identifiers; council tax and dwelling-stock classifications.
3. **Commercial:** VOA/Scottish Assessors/LPS rating lists and rental evidence;
   leases and public-estate rents; EPC floor area. Rateable value is corroborating
   evidence, not automatically the contract rent.
4. **Agriculture/forestry:** farm-business and agricultural-tenancy surveys,
   rural-estate leases, mapped land classification, crop/soil/access variables,
   and Forestry Commission/devolved forestry inventories.
5. **Geography:** ONSPD/NSPL postcode centroids and geography links, address/UPRN
   and cadastral/GIS parcels where licensed.
6. **Market corroboration:** advertised rents after deduplication and an
   achieved-to-advertised adjustment. Asking prices never outrank achieved rent.

No selling-price series is an input to the index.

## 5. Annual estimation

Freeze a comparison basket once a year. Use the most recent valid observation
per property and a rolling evidence window (default 14 months). Remove
duplicates, non-arm's-length arrangements, bundled service charges and obvious
unit errors. Winsorise only under a published rule; preserve excluded records in
the audit trail.

Within each schedule, estimate log annual rent per m² from property type, size,
bedroom band where relevant, age/condition where available, tenure/lease terms,
time and geography. Predict both the reference year and current year for the
same fixed basket. This double-imputation price-relative design stops a changing
mix of homes from masquerading as location growth.

The prototype uses robust weighted medians rather than fitting the full national
hedonic regression because public record-level inputs are not bundled. Its
interface and outputs are designed so an accredited model can replace that
estimator.

## 6. Postcode completion and confidence

Publish every live postcode/class combination, but distinguish:

- `A — direct`: adequate recent observations in the postcode/class;
- `B — modelled-local`: fewer direct observations, supported by adjacent
  postcodes and higher-level effects;
- `C — spatial`: no direct evidence; inverse-distance estimate from comparable
  neighbours;
- `D — even-spread`: no usable local neighbours; provisional value assigned at
  an evenly spaced rank between the national floor and ceiling.

For sparse postcodes, shrink the direct estimate toward an inverse-distance
blend of the nearest comparable postcodes and its region. The weight on direct
evidence rises with effective sample size. Do not silently copy one neighbour.
Record donor postcodes, distance, sample size and uncertainty.

The requested even-spread assumption is suitable only for completing a model.
It must carry grade D and cannot become an appeal-proof statutory value merely
because the CSV has no blanks.

## 7. Floor, ceiling and base location

For each schedule/class/year, calculate the weighted distribution of completed
annual rent per m²:

- floor `F(k,t)` = 10th percentile by default;
- ceiling `C(k,t)` = 90th percentile by default;
- bounded rent `R*(p,k,t) = min(max(Rhat,F),C)`;
- location excess `L(p,k,t) = R* - F`;
- register level `I(p,k,t) = 100 × R* / F`.

Thus the floor location is always index 100 and every other location is stated
relative to it. The comparable location-rental difference between Y and the
floor is `L(Y,k,t)` pounds per m² per year. Comparing X with Y uses
`R*(X,k,t) - R*(Y,k,t)` for the same class.

The 10th/90th percentiles are a transparent interpretation of “no lower than
the lowest 10% and no higher than the highest 90%”. If the policy intention was
instead literally 10% of the single lowest rent and 90% of the single highest,
the CLI permits different quantiles, but single extrema are too unstable for a
national statutory series.

## 8. Annual determination, anomalies and appeals

Run a shadow estimate, council review and final determination on a fixed annual
timetable. Automated GIS/AI flags should include discontinuities across
postcode boundaries, implausible year-on-year movements, rent/m² extremes,
unusual property mix, mapped nuisances/amenities, new developments and donors
too far away. A council officer reviews the evidence before publication.

AI may prioritise cases; it must not be the legal reason for the value. Store
input lineage, model version, coefficients, donors, officer decision and change
reason. Give the owner the evidence summary, a correction route for facts, and
an independent appeal. Appeals correct data or model application; they do not
turn the process into a sale-price valuation of the plot.

Stability controls should be set in legislation: publication lag, exceptional
revision policy, treatment of postcode changes, and possibly a symmetrical
annual movement corridor. Any corridor must defer rather than erase measured
movement and must be visible in the register.

## 9. Future synchronisation

Create a persistent property/parcel key beneath the postcode layer (UPRN plus
title/parcel identifiers), while continuing to publish at postcode level.
Require machine-readable rent returns at tenancy/lease creation and variation;
standardise service-charge and incentive fields; connect EPC, planning,
building-control, rating and tenancy events; issue quarterly postcode-spine
updates; and use a common annual snapshot date across the four nations.

A national data service should expose signed annual releases, versioned schemas,
restatement files and an API returning current and historic postcode/class
indices. Independent statisticians should reproduce each release from escrowed
microdata.

## 10. Primary methodological references

- [ONS Price Index of Private Rents detailed methodology](https://www.ons.gov.uk/economy/inflationandpriceindices/methodologies/priceindexofprivaterentsdetailedmethodology)
- [ONS postcode products (ONSPD and NSPL)](https://www.ons.gov.uk/methodology/geography/geographicalproducts/postcodeproducts)
- [ONS postal geography limitations](https://www.ons.gov.uk/methodology/geography/ukgeographies/postalgeography)
- [Natural England agricultural land classification guidance](https://publications.naturalengland.org.uk/publication/6257050620264448)
- [Open Government Licence 3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)

ONS PIPR is especially relevant: it uses rental rather than selling prices, a
fixed basket, log-linear hedonic regression, floor area, bedrooms, property type
and geography, and double imputation. It also demonstrates the present limit:
published geography is generally local authority/BRMA rather than unit postcode,
so statutory postcode outputs would require controlled access to microdata and
additional sources.
