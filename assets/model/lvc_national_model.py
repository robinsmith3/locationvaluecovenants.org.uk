#!/usr/bin/env python3
"""Illustrative national scenario model for Location Value Covenant applications.

This is a transparent policy exploration tool, not an official forecast or advice.
It compares an LVC adoption scenario with a no-adoption baseline and writes a CSV
dataset plus a self-contained SVG chart using only Python's standard library.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path


VERSION = "1.2.0"


@dataclass(frozen=True)
class Application:
    number: int
    name: str
    mortgage_replacement: float = 0.0
    covenant_yield: float = 0.012
    additional_homes: float = 0.0
    gdp_multiplier: float = 0.0
    public_revenue_rate: float = 0.0
    inflation_reduction: float = 0.0
    description: str = ""


APPLICATIONS = {
    1: Application(1, "Location Value Mortgage", 0.70, 0.012, 0, 0.10, 0.00, 0.0005,
                   "Replaces part of conventional mortgage credit with LVC funding."),
    2: Application(2, "Location Value Mortgage Rescue", 0.85, 0.014, 0, 0.08, 0.00, 0.0002,
                   "Refinances eligible distressed mortgage balances."),
    3: Application(3, "Homeowner Pension", 0.00, 0.013, 0, 0.16, 0.01, 0.0000,
                   "Releases housing wealth into retirement income under a covenant."),
    4: Application(4, "Paying Inheritance Tax", 0.00, 0.013, 0, 0.08, 0.12, 0.0000,
                   "Uses covenant funding to meet eligible inheritance-tax liabilities."),
    5: Application(5, "Property Tax Substitution", 0.00, 0.014, 0, 0.12, 0.16, 0.0002,
                   "Models substitution of selected property taxes by covenant receipts."),
    6: Application(6, "New Home Covenant", 0.75, 0.012, 18_000, 0.55, 0.01, 0.0003,
                   "Funds new homes while displacing conventional mortgage credit."),
    7: Application(7, "Wider Property Investment and Support", 0.25, 0.013, 7_000, 0.85, 0.04, 0.0002,
                   "Supports property investment, infrastructure and regeneration."),
    8: Application(8, "Monetary Stability and Inflation Control", 1.00, 0.011, 0, 0.08, 0.00, 0.0015,
                   "Replaces mortgage-credit creation with long-term funding from savings."),
}


DEFAULTS = {
    "years": 20,
    "take_up": 25.0,
    "ramp_years": 8,
    "annual_lvc_funding": 25.0,
    "gdp": 2_700.0,
    "gdp_growth": 1.5,
    "mortgage_debt": 1_700.0,
    "mortgage_growth": 2.5,
    "mortgage_rate": 4.5,
    "funding_rate": 3.5,
    "mortgage_runoff": 4.0,
    "mpc": 60.0,
    "administration_rate": 0.3,
    "displacement_rate": 15.0,
    "productive_investment_share": 20.0,
    "capital_output_return": 10.0,
    "capital_depreciation": 5.0,
    "productivity_lag": 3,
    "tax_substitution_share": 50.0,
    "tax_efficiency_gain": 20.0,
    "welfare_linked_share": 25.0,
    "welfare_reduction_rate": 30.0,
    "location_value_capture_rate": 30.0,
    "rental_value_growth": 1.0,
    "covenant_reinvestment_share": 10.0,
    "inflation": 2.0,
    "baseline_homes": 180_000,
    "funding_growth": 2.0,
    "discount_rate": 3.5,
}


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def prompt_text(label: str, default: str) -> str:
    answer = input(f"{label} [{default}]: ").strip()
    return answer or default


def prompt_float(label: str, default: float, low: float | None = None) -> float:
    while True:
        raw = prompt_text(label, f"{default:g}")
        try:
            value = float(raw)
            if low is not None and value < low:
                raise ValueError
            return value
        except ValueError:
            print(f"Please enter a number{f' of at least {low:g}' if low is not None else ''}.")


def parse_apps(raw: str) -> list[int]:
    raw = raw.strip().lower()
    if raw in {"all", "*"}:
        return list(APPLICATIONS)
    try:
        apps = sorted(set(int(part.strip()) for part in raw.split(",") if part.strip()))
    except ValueError as exc:
        raise ValueError("Applications must be comma-separated numbers, or 'all'.") from exc
    invalid = [number for number in apps if number not in APPLICATIONS]
    if not apps or invalid:
        raise ValueError(f"Choose one or more applications from 1 to 8; invalid: {invalid}")
    return apps


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Compare illustrative national LVC adoption with a no-adoption baseline.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--apps", default="all", help="comma-separated application numbers, or all")
    p.add_argument("--years", type=int, default=DEFAULTS["years"], help="projection years")
    p.add_argument("--take-up", type=float, default=DEFAULTS["take_up"], help="eventual take-up percent")
    p.add_argument("--ramp-years", type=int, default=DEFAULTS["ramp_years"], help="years to reach take-up")
    p.add_argument("--annual-lvc-funding", type=float, default=DEFAULTS["annual_lvc_funding"], help="annual funding capacity, £bn at full take-up")
    p.add_argument("--gdp", type=float, default=DEFAULTS["gdp"], help="starting real GDP at today's prices, £bn")
    p.add_argument("--gdp-growth", type=float, default=DEFAULTS["gdp_growth"], help="baseline real GDP growth percent")
    p.add_argument("--mortgage-debt", type=float, default=DEFAULTS["mortgage_debt"], help="starting mortgage debt, £bn")
    p.add_argument("--mortgage-growth", type=float, default=DEFAULTS["mortgage_growth"], help="baseline mortgage-credit growth percent")
    p.add_argument("--mortgage-rate", type=float, default=DEFAULTS["mortgage_rate"], help="average mortgage interest rate percent")
    p.add_argument("--funding-rate", type=float, default=DEFAULTS["funding_rate"], help="public LVC funding cost percent")
    p.add_argument("--mortgage-runoff", type=float, default=DEFAULTS["mortgage_runoff"], help="annual repayment or exit from the LVC-funded stock percent")
    p.add_argument("--mpc", type=float, default=DEFAULTS["mpc"], help="percent of net household cash-flow change spent in the economy")
    p.add_argument("--administration-rate", type=float, default=DEFAULTS["administration_rate"], help="annual programme administration cost as percent of outstanding LVC funding")
    p.add_argument("--displacement-rate", type=float, default=DEFAULTS["displacement_rate"], help="percent of gross direct GDP effect displaced elsewhere")
    p.add_argument("--productive-investment-share", type=float, default=DEFAULTS["productive_investment_share"], help="percent of displaced mortgage credit redirected into productive investment")
    p.add_argument("--capital-output-return", type=float, default=DEFAULTS["capital_output_return"], help="annual additional output as percent of productive capital")
    p.add_argument("--capital-depreciation", type=float, default=DEFAULTS["capital_depreciation"], help="annual depreciation of productive capital percent")
    p.add_argument("--productivity-lag", type=int, default=DEFAULTS["productivity_lag"], help="years before new productive investment adds to output")
    p.add_argument("--tax-substitution-share", type=float, default=DEFAULTS["tax_substitution_share"], help="percent of covenant receipts and prior welfare savings used to replace taxes on production")
    p.add_argument("--tax-efficiency-gain", type=float, default=DEFAULTS["tax_efficiency_gain"], help="additional annual output per £1 of productive tax replaced, percent")
    p.add_argument("--welfare-linked-share", type=float, default=DEFAULTS["welfare_linked_share"], help="percent of structural output reaching people or firms receiving economy-related support")
    p.add_argument("--welfare-reduction-rate", type=float, default=DEFAULTS["welfare_reduction_rate"], help="reduction in compensatory welfare per £1 of relevant additional output, percent")
    p.add_argument("--location-value-capture-rate", type=float, default=DEFAULTS["location_value_capture_rate"], help="percent of structural productivity growth reflected in location rental values")
    p.add_argument("--rental-value-growth", type=float, default=DEFAULTS["rental_value_growth"], help="underlying annual real location-rental-value growth percent")
    p.add_argument("--covenant-reinvestment-share", type=float, default=DEFAULTS["covenant_reinvestment_share"], help="percent of covenant receipts and prior welfare savings reinvested productively")
    p.add_argument("--inflation", type=float, default=DEFAULTS["inflation"], help="baseline inflation percent")
    p.add_argument("--baseline-homes", type=int, default=DEFAULTS["baseline_homes"], help="annual baseline new homes")
    p.add_argument("--funding-growth", type=float, default=DEFAULTS["funding_growth"], help="annual growth of LVC funding capacity percent")
    p.add_argument("--discount-rate", type=float, default=DEFAULTS["discount_rate"], help="discount rate for present values percent")
    p.add_argument("--output-dir", default="lvc_model_output", help="output directory")
    p.add_argument("--interactive", action=argparse.BooleanOptionalAction, default=None, help="prompt for inputs")
    p.add_argument("--list-apps", action="store_true", help="show available applications and exit")
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return p


def collect_inputs(args: argparse.Namespace) -> argparse.Namespace:
    interactive = args.interactive if args.interactive is not None else sys.stdin.isatty()
    if not interactive:
        return args
    print("\nLVC National Modelling Tool")
    print("Press Enter to accept each default. Amounts are in £bn unless stated.\n")
    print("Available applications:")
    for number, app in APPLICATIONS.items():
        print(f"  {number:02d}  {app.name}")
    args.apps = prompt_text("Applications (comma-separated or all)", args.apps)
    args.years = int(prompt_float("Years active", args.years, 1))
    args.take_up = prompt_float("Eventual take-up (%)", args.take_up, 0)
    args.ramp_years = int(prompt_float("Years to reach take-up", args.ramp_years, 1))
    args.annual_lvc_funding = prompt_float("Annual LVC funding at full take-up (£bn)", args.annual_lvc_funding, 0)
    args.gdp = prompt_float("Starting real GDP at today's prices (£bn)", args.gdp, 0)
    args.gdp_growth = prompt_float("Baseline real GDP growth (%)", args.gdp_growth)
    args.mortgage_debt = prompt_float("Starting mortgage debt (£bn)", args.mortgage_debt, 0)
    args.mortgage_growth = prompt_float("Baseline mortgage-credit growth (%)", args.mortgage_growth)
    args.mortgage_rate = prompt_float("Average mortgage interest rate (%)", args.mortgage_rate, 0)
    args.funding_rate = prompt_float("Public LVC funding cost (%)", args.funding_rate, 0)
    args.mortgage_runoff = prompt_float("Annual repayment or exit from funded stock (%)", args.mortgage_runoff, 0)
    args.mpc = prompt_float("Share of household cash-flow change spent (%)", args.mpc, 0)
    args.administration_rate = prompt_float("Programme administration rate (%)", args.administration_rate, 0)
    args.displacement_rate = prompt_float("Displacement of gross GDP effect (%)", args.displacement_rate, 0)
    args.productive_investment_share = prompt_float("Displaced mortgage credit redirected to productive investment (%)", args.productive_investment_share, 0)
    args.capital_output_return = prompt_float("Annual output from productive capital (%)", args.capital_output_return, 0)
    args.capital_depreciation = prompt_float("Annual productive-capital depreciation (%)", args.capital_depreciation, 0)
    args.productivity_lag = int(prompt_float("Years before investment raises output", args.productivity_lag, 0))
    args.tax_substitution_share = prompt_float("Receipts and welfare savings used to replace productive taxes (%)", args.tax_substitution_share, 0)
    args.tax_efficiency_gain = prompt_float("Output gained per £1 of productive tax replaced (%)", args.tax_efficiency_gain, 0)
    args.welfare_linked_share = prompt_float("Structural output reaching support recipients (%)", args.welfare_linked_share, 0)
    args.welfare_reduction_rate = prompt_float("Compensatory welfare reduction per £1 of relevant output (%)", args.welfare_reduction_rate, 0)
    args.location_value_capture_rate = prompt_float("Productivity growth reflected in location rental values (%)", args.location_value_capture_rate, 0)
    args.rental_value_growth = prompt_float("Underlying real location-rental-value growth (%)", args.rental_value_growth)
    args.covenant_reinvestment_share = prompt_float("Receipts and welfare savings reinvested productively (%)", args.covenant_reinvestment_share, 0)
    args.inflation = prompt_float("Baseline inflation (%)", args.inflation)
    args.baseline_homes = int(prompt_float("Annual baseline new homes", args.baseline_homes, 0))
    args.funding_growth = prompt_float("Annual funding-capacity growth (%)", args.funding_growth)
    args.discount_rate = prompt_float("Discount rate for present values (%)", args.discount_rate, 0)
    args.output_dir = prompt_text("Output directory", args.output_dir)
    return args


def validate(args: argparse.Namespace) -> list[int]:
    apps = parse_apps(args.apps)
    if not 1 <= args.years <= 100:
        raise ValueError("Years must be between 1 and 100.")
    if not 0 <= args.take_up <= 100:
        raise ValueError("Take-up must be between 0 and 100 percent.")
    if not 1 <= args.ramp_years <= 100:
        raise ValueError("Ramp years must be between 1 and 100.")
    for name in ("annual_lvc_funding", "gdp", "mortgage_debt", "mortgage_rate", "funding_rate", "baseline_homes", "discount_rate", "administration_rate"):
        if getattr(args, name) < 0:
            raise ValueError(f"{name.replace('_', ' ')} cannot be negative.")
    for name in ("mortgage_runoff", "mpc", "displacement_rate", "productive_investment_share",
                 "capital_output_return", "capital_depreciation", "tax_substitution_share",
                 "tax_efficiency_gain", "welfare_linked_share", "welfare_reduction_rate",
                 "location_value_capture_rate", "covenant_reinvestment_share"):
        if not 0 <= getattr(args, name) <= 100:
            raise ValueError(f"{name.replace('_', ' ')} must be between 0 and 100 percent.")
    if not 0 <= args.productivity_lag <= 50:
        raise ValueError("productivity lag must be between 0 and 50 years.")
    if args.rental_value_growth <= -100:
        raise ValueError("rental value growth must be greater than -100 percent.")
    if args.tax_substitution_share + args.covenant_reinvestment_share > 100:
        raise ValueError("tax substitution and covenant reinvestment shares cannot total more than 100 percent.")
    return apps


def simulate(args: argparse.Namespace, selected: list[int]) -> list[dict[str, float | int]]:
    apps = [APPLICATIONS[number] for number in selected]
    weight = 1.0 / len(apps)
    take_up_target = args.take_up / 100.0
    gdp_growth = args.gdp_growth / 100.0
    mortgage_growth = args.mortgage_growth / 100.0
    funding_growth = args.funding_growth / 100.0
    discount_rate = args.discount_rate / 100.0
    mortgage_rate = args.mortgage_rate / 100.0
    funding_rate = args.funding_rate / 100.0
    runoff_rate = args.mortgage_runoff / 100.0
    mpc = args.mpc / 100.0
    administration_rate = args.administration_rate / 100.0
    displacement_rate = args.displacement_rate / 100.0
    productive_investment_share = args.productive_investment_share / 100.0
    capital_output_return = args.capital_output_return / 100.0
    capital_depreciation = args.capital_depreciation / 100.0
    tax_substitution_share = args.tax_substitution_share / 100.0
    tax_efficiency_gain = args.tax_efficiency_gain / 100.0
    welfare_linked_share = args.welfare_linked_share / 100.0
    welfare_reduction_rate = args.welfare_reduction_rate / 100.0
    location_value_capture_rate = args.location_value_capture_rate / 100.0
    rental_value_growth = args.rental_value_growth / 100.0
    covenant_reinvestment_share = args.covenant_reinvestment_share / 100.0

    baseline_gdp = policy_gdp = args.gdp
    baseline_mortgage = policy_mortgage = args.mortgage_debt
    outstanding_lvc = outstanding_replaced = 0.0
    cumulative_lvc = cumulative_receipts = cumulative_homes_delta = 0.0
    cumulative_net_household_cashflow = cumulative_public_cashflow = 0.0
    productive_capital = previous_welfare_saving = cumulative_welfare_saving = 0.0
    cumulative_productive_investment = cumulative_tax_substitution = 0.0
    location_value_index = 1.0
    investment_pipeline = [0.0] * args.productivity_lag
    rows: list[dict[str, float | int]] = []

    for year in range(0, args.years + 1):
        if year == 0:
            adoption = annual_lvc = annual_replacement = annual_receipts = 0.0
            gross_interest_avoided = net_household_cashflow = consumption_effect = 0.0
            funding_cost = administration_cost = annual_public_cashflow = annual_extra_homes = 0.0
            gross_direct_gdp_effect = displaced_gdp_effect = net_annual_gdp_effect = 0.0
            redirected_investment = receipt_reinvestment = productive_investment = 0.0
            capital_output = taxes_substituted = tax_productivity_output = 0.0
            structural_output = welfare_saving = fiscal_capacity = 0.0
            endogenous_rental_growth = effective_rental_growth = 0.0
            policy_inflation = baseline_inflation = args.inflation
        else:
            baseline_gdp *= 1.0 + gdp_growth
            baseline_mortgage *= 1.0 + mortgage_growth
            adoption = take_up_target * min(1.0, year / args.ramp_years)
            capacity = args.annual_lvc_funding * ((1.0 + funding_growth) ** (year - 1))
            annual_lvc = capacity * adoption
            annual_replacement = annual_lvc * sum(a.mortgage_replacement * weight for a in apps)
            outstanding_lvc = outstanding_lvc * (1.0 - runoff_rate) + annual_lvc
            outstanding_replaced = outstanding_replaced * (1.0 - runoff_rate) + annual_replacement
            annual_receipts = (outstanding_lvc * sum(a.covenant_yield * weight for a in apps)
                               * location_value_index)
            gross_interest_avoided = outstanding_replaced * mortgage_rate
            net_household_cashflow = gross_interest_avoided - annual_receipts
            consumption_effect = net_household_cashflow * mpc
            funding_cost = outstanding_lvc * funding_rate
            administration_cost = outstanding_lvc * administration_rate
            fiscal_capacity = annual_receipts + previous_welfare_saving
            taxes_substituted = fiscal_capacity * tax_substitution_share
            receipt_reinvestment = fiscal_capacity * covenant_reinvestment_share
            redirected_investment = annual_replacement * productive_investment_share
            productive_investment = redirected_investment + receipt_reinvestment
            productive_capital *= 1.0 - capital_depreciation
            if args.productivity_lag == 0:
                productive_capital += productive_investment
            else:
                productive_capital += investment_pipeline.pop(0)
                investment_pipeline.append(productive_investment)
            capital_output = productive_capital * capital_output_return
            tax_productivity_output = taxes_substituted * tax_efficiency_gain
            structural_output = capital_output + tax_productivity_output
            welfare_saving = structural_output * welfare_linked_share * welfare_reduction_rate
            annual_public_cashflow = (annual_lvc * sum(a.public_revenue_rate * weight for a in apps)
                                      + annual_receipts + welfare_saving - funding_cost
                                      - administration_cost - taxes_substituted - receipt_reinvestment)
            annual_extra_homes = adoption * sum(a.additional_homes for a in apps)
            gross_direct_gdp_effect = annual_lvc * sum(a.gdp_multiplier * weight for a in apps)
            displaced_gdp_effect = gross_direct_gdp_effect * displacement_rate
            net_annual_gdp_effect = (gross_direct_gdp_effect - displaced_gdp_effect
                                     + consumption_effect + structural_output)
            growth_impulse = net_annual_gdp_effect / max(policy_gdp, 1.0)
            endogenous_rental_growth = (structural_output / max(baseline_gdp, 1.0)
                                         * location_value_capture_rate)
            effective_rental_growth = rental_value_growth + endogenous_rental_growth
            location_value_index *= max(0.0, 1.0 + effective_rental_growth)
            inflation_cut = adoption * sum(a.inflation_reduction for a in apps) * 100.0
            baseline_inflation = args.inflation
            policy_inflation = max(-1.0, baseline_inflation - inflation_cut)
            policy_gdp *= 1.0 + gdp_growth + growth_impulse
            policy_mortgage = max(0.0, policy_mortgage * (1.0 + mortgage_growth) - annual_replacement)
            cumulative_lvc += annual_lvc
            cumulative_receipts += annual_receipts
            cumulative_net_household_cashflow += net_household_cashflow
            cumulative_public_cashflow += annual_public_cashflow
            cumulative_homes_delta += annual_extra_homes
            cumulative_welfare_saving += welfare_saving
            cumulative_productive_investment += productive_investment
            cumulative_tax_substitution += taxes_substituted
            previous_welfare_saving = welfare_saving

        pv_factor = (1.0 + discount_rate) ** year
        rows.append({
            "year": year,
            "adoption_percent": adoption * 100.0 if year else 0.0,
            "baseline_real_gdp_gbp_bn": baseline_gdp,
            "lvc_real_gdp_gbp_bn": policy_gdp,
            "gdp_delta_gbp_bn": policy_gdp - baseline_gdp,
            "baseline_mortgage_debt_gbp_bn": baseline_mortgage,
            "lvc_mortgage_debt_gbp_bn": policy_mortgage,
            "mortgage_debt_delta_gbp_bn": policy_mortgage - baseline_mortgage,
            "annual_lvc_funding_gbp_bn": annual_lvc,
            "cumulative_lvc_funding_gbp_bn": cumulative_lvc,
            "annual_mortgage_credit_replaced_gbp_bn": annual_replacement,
            "outstanding_mortgage_credit_replaced_gbp_bn": outstanding_replaced,
            "gross_mortgage_interest_avoided_gbp_bn": gross_interest_avoided,
            "annual_covenant_payments_gbp_bn": annual_receipts,
            "net_household_cashflow_change_gbp_bn": net_household_cashflow,
            "cumulative_net_household_cashflow_change_gbp_bn": cumulative_net_household_cashflow,
            "household_consumption_effect_gbp_bn": consumption_effect,
            "annual_covenant_receipts_gbp_bn": annual_receipts,
            "cumulative_covenant_receipts_gbp_bn": cumulative_receipts,
            "annual_public_funding_cost_gbp_bn": funding_cost,
            "annual_administration_cost_gbp_bn": administration_cost,
            "net_public_cashflow_after_allocations_gbp_bn": annual_public_cashflow,
            "cumulative_net_public_cashflow_after_allocations_gbp_bn": cumulative_public_cashflow,
            "productive_investment_gbp_bn": productive_investment,
            "cumulative_productive_investment_gbp_bn": cumulative_productive_investment,
            "productive_capital_stock_gbp_bn": productive_capital,
            "baseline_model_attributed_productive_capital_gbp_bn": 0.0,
            "output_from_productive_capital_gbp_bn": capital_output,
            "productive_taxes_substituted_gbp_bn": taxes_substituted,
            "cumulative_productive_taxes_substituted_gbp_bn": cumulative_tax_substitution,
            "output_from_tax_substitution_gbp_bn": tax_productivity_output,
            "compensatory_welfare_reduction_gbp_bn": welfare_saving,
            "cumulative_compensatory_welfare_reduction_gbp_bn": cumulative_welfare_saving,
            "location_value_index": location_value_index,
            "underlying_rental_value_growth_percent": rental_value_growth * 100.0,
            "productivity_related_rental_growth_percent": endogenous_rental_growth * 100.0,
            "effective_rental_value_growth_percent": effective_rental_growth * 100.0,
            "gross_direct_gdp_effect_gbp_bn": gross_direct_gdp_effect,
            "displaced_gdp_effect_gbp_bn": displaced_gdp_effect,
            "net_annual_gdp_effect_gbp_bn": net_annual_gdp_effect,
            "baseline_new_homes": args.baseline_homes,
            "lvc_new_homes": args.baseline_homes + annual_extra_homes,
            "additional_homes": annual_extra_homes,
            "cumulative_additional_homes": cumulative_homes_delta,
            "baseline_inflation_percent": baseline_inflation,
            "lvc_inflation_percent": policy_inflation,
            "inflation_delta_percentage_points": policy_inflation - baseline_inflation,
            "discounted_gdp_delta_gbp_bn": (policy_gdp - baseline_gdp) / pv_factor,
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, float | int]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: f"{value:.6f}" if isinstance(value, float) else value for key, value in row.items()})


def svg_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_svg(path: Path, rows: list[dict[str, float | int]], selected: list[int]) -> None:
    width, height = 1200, 1160
    panels = [
        ("Real GDP (£bn)", "baseline_real_gdp_gbp_bn", "lvc_real_gdp_gbp_bn"),
        ("Mortgage debt (£bn)", "baseline_mortgage_debt_gbp_bn", "lvc_mortgage_debt_gbp_bn"),
        ("Annual new homes", "baseline_new_homes", "lvc_new_homes"),
        ("Inflation (%)", "baseline_inflation_percent", "lvc_inflation_percent"),
        ("Additional productive capital (£bn)", "baseline_model_attributed_productive_capital_gbp_bn", "productive_capital_stock_gbp_bn"),
        ("Annual covenant receipts (£bn)", "baseline_model_attributed_productive_capital_gbp_bn", "annual_covenant_receipts_gbp_bn"),
    ]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="#f7faf7"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#183028}.title{font-size:26px;font-weight:700}.sub{font-size:13px;fill:#53655e}.pt{font-size:16px;font-weight:700}.axis{font-size:11px;fill:#53655e}.grid{stroke:#d9e3dd;stroke-width:1}.base{stroke:#6b7280;stroke-width:3;fill:none}.lvc{stroke:#15803d;stroke-width:3;fill:none}</style>',
           '<text x="45" y="42" class="title">LVC national scenario: adoption versus baseline</text>',
           f'<text x="45" y="66" class="sub">Applications: {svg_escape(", ".join(f"{n:02d}" for n in selected))} · Illustrative assumptions, not a forecast</text>',
           '<line x1="810" y1="38" x2="850" y2="38" class="base"/><text x="860" y="42" class="sub">No-adoption baseline</text>',
           '<line x1="1010" y1="38" x2="1050" y2="38" class="lvc"/><text x="1060" y="42" class="sub">LVC scenario</text>']
    for index, (title, baseline_key, policy_key) in enumerate(panels):
        col, row_no = index % 2, index // 2
        x0, y0 = 55 + col * 585, 105 + row_no * 345
        pw, ph = 510, 255
        values = [float(r[baseline_key]) for r in rows] + [float(r[policy_key]) for r in rows]
        lo, hi = min(values), max(values)
        if math.isclose(lo, hi):
            lo, hi = lo - 1.0, hi + 1.0
        pad = (hi - lo) * 0.08
        lo, hi = lo - pad, hi + pad
        out.append(f'<text x="{x0}" y="{y0 - 18}" class="pt">{svg_escape(title)}</text>')
        for tick in range(5):
            y = y0 + ph * tick / 4
            value = hi - (hi - lo) * tick / 4
            out.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0+pw}" y2="{y:.1f}" class="grid"/>')
            out.append(f'<text x="{x0-8}" y="{y+4:.1f}" text-anchor="end" class="axis">{value:,.1f}</text>')
        def points(key: str) -> str:
            pts = []
            for i, record in enumerate(rows):
                x = x0 + pw * i / max(1, len(rows) - 1)
                y = y0 + ph * (hi - float(record[key])) / (hi - lo)
                pts.append(f"{x:.1f},{y:.1f}")
            return " ".join(pts)
        out.append(f'<polyline points="{points(baseline_key)}" class="base"/>')
        out.append(f'<polyline points="{points(policy_key)}" class="lvc"/>')
        out.append(f'<text x="{x0}" y="{y0+ph+20}" class="axis">Year 0</text>')
        out.append(f'<text x="{x0+pw}" y="{y0+ph+20}" text-anchor="end" class="axis">Year {len(rows)-1}</text>')
    out.append('</svg>')
    path.write_text("\n".join(out), encoding="utf-8")


def write_assumptions(path: Path, args: argparse.Namespace, selected: list[int]) -> None:
    lines = [
        "LVC NATIONAL MODEL — RUN ASSUMPTIONS",
        "Illustrative scenario only; not an official forecast, financial advice or policy costing.",
        "",
        f"Applications: {', '.join(f'{n:02d} {APPLICATIONS[n].name}' for n in selected)}",
        f"Years: {args.years}",
        f"Eventual take-up: {args.take_up:g}%",
        f"Ramp period: {args.ramp_years} years",
        f"Annual LVC funding at full take-up: £{args.annual_lvc_funding:g}bn",
        f"Starting real GDP at today's prices: £{args.gdp:g}bn; baseline real growth: {args.gdp_growth:g}%",
        f"Starting mortgage debt: £{args.mortgage_debt:g}bn; baseline growth: {args.mortgage_growth:g}%",
        f"Average mortgage interest rate: {args.mortgage_rate:g}%",
        f"Public LVC funding cost: {args.funding_rate:g}%",
        f"Annual repayment or exit from funded stock: {args.mortgage_runoff:g}%",
        f"Share of household cash-flow change spent: {args.mpc:g}%",
        f"Programme administration rate: {args.administration_rate:g}%",
        f"Displacement of gross direct GDP effect: {args.displacement_rate:g}%",
        f"Displaced mortgage credit redirected to productive investment: {args.productive_investment_share:g}%",
        f"Annual output from productive capital: {args.capital_output_return:g}%",
        f"Productive-capital depreciation: {args.capital_depreciation:g}%",
        f"Productivity lag: {args.productivity_lag} years",
        f"Receipts and prior welfare savings used for productive-tax substitution: {args.tax_substitution_share:g}%",
        f"Output gain per £1 of productive tax replaced: {args.tax_efficiency_gain:g}%",
        f"Structural output reaching support recipients: {args.welfare_linked_share:g}%",
        f"Compensatory welfare reduction per £1 of relevant output: {args.welfare_reduction_rate:g}%",
        f"Structural productivity growth reflected in rental values: {args.location_value_capture_rate:g}%",
        f"Underlying real location-rental-value growth: {args.rental_value_growth:g}%",
        f"Receipts and prior welfare savings reinvested productively: {args.covenant_reinvestment_share:g}%",
        f"Baseline inflation: {args.inflation:g}%",
        f"Baseline annual new homes: {args.baseline_homes:,}",
        f"Discount rate: {args.discount_rate:g}%",
        "",
        "HOW TO INTERPRET",
        "The baseline compounds the supplied GDP and mortgage-credit growth rates.",
        "The LVC scenario applies take-up gradually, divides funding equally among selected applications,",
        "and applies the editable coefficients in APPLICATIONS. Effects are deliberately simple and",
        "should be replaced with evidenced estimates before the results are used in public material.",
        "GDP impacts combine an application-specific direct effect with household consumption arising",
        "from avoided mortgage interest less covenant payments, then deduct the selected displacement.",
        "Funding cost, administration and portfolio run-off are included. Defaults, detailed regional",
        "valuation changes and a full monetary-policy response are not. Inflation effects are indicative.",
        "The structural module redirects a selected share of displaced mortgage credit into productive",
        "capital after a lag. Covenant receipts and prior welfare savings can replace taxes on production",
        "or finance more productive investment. Resulting structural output reduces only the selected",
        "economy-related share of welfare and raises rental values by the selected capture rate.",
        "Applications may overlap; selecting several can double-count eligible households or funding unless",
        "the user adjusts funding and coefficients accordingly.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(rows: list[dict[str, float | int]], selected: list[int], output_dir: Path) -> None:
    final = rows[-1]
    print("\nScenario complete")
    print(f"Applications: {', '.join(f'{n:02d}' for n in selected)}")
    print(f"Final-year GDP difference: £{float(final['gdp_delta_gbp_bn']):,.2f}bn")
    print(f"Final-year mortgage-debt difference: £{float(final['mortgage_debt_delta_gbp_bn']):,.2f}bn")
    print(f"Cumulative additional homes: {float(final['cumulative_additional_homes']):,.0f}")
    print(f"Final-year inflation difference: {float(final['inflation_delta_percentage_points']):,.2f} percentage points")
    print(f"Final-year productive capital created: £{float(final['productive_capital_stock_gbp_bn']):,.2f}bn")
    print(f"Final-year productive taxes substituted: £{float(final['productive_taxes_substituted_gbp_bn']):,.2f}bn")
    print(f"Final-year compensatory welfare reduction: £{float(final['compensatory_welfare_reduction_gbp_bn']):,.2f}bn")
    print(f"Outputs: {output_dir.resolve()}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.list_apps:
        for number, app in APPLICATIONS.items():
            print(f"{number:02d}  {app.name}\n    {app.description}")
        return 0
    try:
        args = collect_inputs(args)
        selected = validate(args)
    except (ValueError, EOFError, KeyboardInterrupt) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = simulate(args, selected)
    write_csv(output_dir / "lvc_national_scenario.csv", rows)
    write_svg(output_dir / "lvc_national_scenario.svg", rows, selected)
    write_assumptions(output_dir / "assumptions.txt", args, selected)
    print_summary(rows, selected, output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
