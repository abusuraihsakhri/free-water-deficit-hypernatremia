#!/usr/bin/env python3
"""Adult hypernatremia free-water deficit estimates (standard library only).

Estimates are not a prescription: assess volume status, ongoing losses,
hyperglycemia, duration, and serial sodium measurements clinically.
"""
import argparse
import csv
import json
import math
from pathlib import Path


def _number(name, value, low, high):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number")
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}")
    return value


def calculate_metrics(*, weight_kg, serum_sodium, tbw_fraction,
                      target_sodium=140.0, fluid_sodium=0.0, fluid_potassium=0.0):
    """Compute TBW, deficit to target, and Adrogué–Madias Na change per litre.

    Sodium and potassium concentrations are in mmol/L; weight is in kg.
    TBW fractions are chosen by the user (e.g. 0.6 adult male, 0.5
    adult female/older male, 0.45 older female). For adults only.
    """
    weight = _number("weight_kg", weight_kg, 1, 500)
    sodium = _number("serum_sodium", serum_sodium, 100, 250)
    fraction = _number("tbw_fraction", tbw_fraction, 0.3, 0.8)
    target = _number("target_sodium", target_sodium, 120, 200)
    na_fluid = _number("fluid_sodium", fluid_sodium, 0, 600)
    k_fluid = _number("fluid_potassium", fluid_potassium, 0, 200)
    if sodium <= 145:
        raise ValueError("serum_sodium must exceed 145 mmol/L (hypernatremia)")
    if target > sodium:
        raise ValueError("target_sodium cannot exceed serum_sodium")

    tbw = weight * fraction
    deficit = tbw * (sodium / target - 1.0)
    delta_per_litre = (na_fluid + k_fluid - sodium) / (tbw + 1.0)
    return {
        "weight_kg": weight,
        "serum_sodium_mmol_l": sodium,
        "target_sodium_mmol_l": target,
        "tbw_fraction": fraction,
        "total_body_water_l": tbw,
        "free_water_deficit_l": max(0.0, deficit),
        "fluid_sodium_mmol_l": na_fluid,
        "fluid_potassium_mmol_l": k_fluid,
        "estimated_sodium_change_per_l_mmol_l": delta_per_litre,
    }


def _spreadsheet_safe(value):
    """Prevent a text cell becoming a spreadsheet formula on CSV open."""
    value = str(value)
    if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


def process_batch(input_csv, output_csv):
    """Validate an entire CSV before writing an output; no partial output."""
    required = {"weight_kg", "serum_sodium", "tbw_fraction"}
    results = []
    with open(input_csv, encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        names = list(reader.fieldnames or [])
        if len(names) != len(set(names)) or not required.issubset(names):
            raise ValueError("CSV requires unique headers: weight_kg, serum_sodium, tbw_fraction")
        for line, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"Row {line}: extra CSV fields")
            try:
                values = calculate_metrics(
                    **{key: row[key] for key in
                       ("weight_kg", "serum_sodium", "tbw_fraction",
                        "target_sodium", "fluid_sodium", "fluid_potassium")
                       if key in row and row[key] not in ("", None)}
                )
            except ValueError as exc:
                raise ValueError(f"Row {line}: {exc}") from exc
            results.append({**{key: _spreadsheet_safe(value) for key, value in row.items()},
                            "total_body_water_l": round(values["total_body_water_l"], 4),
                            "free_water_deficit_l": round(values["free_water_deficit_l"], 4),
                            "estimated_sodium_change_per_l_mmol_l":
                                round(values["estimated_sodium_change_per_l_mmol_l"], 4)})
    result_fields = ("total_body_water_l", "free_water_deficit_l",
                     "estimated_sodium_change_per_l_mmol_l")
    fieldnames = names + [name for name in result_fields if name not in names]
    with open(output_csv, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[_spreadsheet_safe(n) for n in fieldnames])
        writer.writeheader()
        for row in results:
            writer.writerow({_spreadsheet_safe(k): v for k, v in row.items()})
    return len(results)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Adult hypernatremia free-water deficit estimator")
    sub = parser.add_subparsers(dest="command", required=True)
    single = sub.add_parser("single", help="Compute one estimate as JSON")
    for flag in ("weight-kg", "serum-sodium", "tbw-fraction"):
        single.add_argument("--" + flag, type=float, required=True)
    for flag, default in (("target-sodium", 140.0),
                          ("fluid-sodium", 0.0), ("fluid-potassium", 0.0)):
        single.add_argument("--" + flag, type=float, default=default)
    batch = sub.add_parser("batch", help="Compute CSV rows without transmitting data")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            values = vars(args).copy()
            values.pop("command")
            print(json.dumps(calculate_metrics(**values), indent=2))
        else:
            count = process_batch(args.input, args.output)
            print(f"Processed {count} rows into {args.output}")
        return 0
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
