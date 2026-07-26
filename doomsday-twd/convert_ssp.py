#!/usr/bin/env python3
"""
convert_ssp.py -- IIASA SSP population -> reconstructed year,births

The SSP database publishes population by five-year age group and
five-year period, not annual births. This script reconstructs a birth
series from the 0-4 FEMALE population:

    annual female births over (t-5, t]  ~=  P_female(0-4, t) / 5
    annual total  births                ~=  that x (1 + SRB)

with SRB = 1.05 male births per female birth, so the factor is 2.05.

Two approximations, both stated in the caption of Table 2:

  1. NO UNDER-FIVE MORTALITY CORRECTION. Children who died before
     being counted in the 0-4 group were still born, so this
     UNDERCOUNTS by a few percent (global under-five mortality is
     about 3.7% today and falling).

  2. TIME STAMP. The 0-4 population at t reflects births over
     (t-5, t], whose midpoint is t-2.5. Assigning the average to
     t-2.5 (the default, --midpoint) is the more faithful choice;
     --no-midpoint reproduces the naive assignment to t. On a
     declining birth series the naive version reads about 1% high,
     which offsets part of approximation 1. The script reports both
     so the difference can be stated rather than hidden.

Usage:
    python3 convert_ssp.py ssp_snapshot_*.csv --list
    python3 convert_ssp.py ssp_snapshot_*.csv --region World \\
        --variable "Population|Female|Aged0-4"
"""
import argparse

import numpy as np
import pandas as pd

from _common import (END_YEAR, START_YEAR, die, normalise_columns,
                     pick_column, require_nonempty, summarise)

SRB_FACTOR = 1.0 + 1.05      # female births -> total births


def series_for_row(row, year_cols, unit_scale, midpoint, start=START_YEAR, end=END_YEAR):
    years = np.array([int(c) for c in year_cols], dtype=float)
    pop = np.array([float(row[c]) for c in year_cols], dtype=float)
    annual = (pop / 5.0) * SRB_FACTOR * unit_scale
    stamps = years - 2.5 if midpoint else years
    grid = np.arange(start, end + 1)
    if grid.min() < stamps.min() or grid.max() > stamps.max():
        print(f"    note: the SSP grid spans {stamps.min():.1f}-{stamps.max():.1f}; "
              f"values outside it are held flat, not extrapolated")
    return grid, np.interp(grid, stamps, annual)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--region", default="World")
    ap.add_argument("--variable", default=None,
                    help="exact or substring match; required if the file "
                         "holds more than one variable")
    ap.add_argument("--unit-scale", type=float, default=1e6,
                    help="SSP population is in millions by default")
    ap.add_argument("--midpoint", dest="midpoint", action="store_true",
                    default=True)
    ap.add_argument("--no-midpoint", dest="midpoint", action="store_false")
    ap.add_argument("--prefix", default="ssp")
    ap.add_argument("--start", type=int, default=START_YEAR)
    ap.add_argument("--end", type=int, default=END_YEAR)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    df = normalise_columns(pd.read_csv(args.csv))
    scn_col = pick_column(df, ["scenario"], "scenario")
    reg_col = pick_column(df, ["region", "location"], "region")
    var_col = pick_column(df, ["variable"], "variable", required=False)
    year_cols = [c for c in df.columns if c.strip().isdigit()]
    if not year_cols:
        die("no year columns found; expected wide format with columns "
            "like 2020, 2025, ...")

    if args.list:
        for c in (scn_col, reg_col, var_col):
            if c:
                print(f"{c:10s}: {sorted(map(str, df[c].dropna().unique()))}")
        print(f"years     : {year_cols}")
        return

    print(f"read {len(df)} rows from {args.csv}")
    sub = df[df[reg_col].astype(str).str.strip() == args.region]
    require_nonempty(sub, f"{reg_col} == {args.region!r}")
    print(f"  {reg_col} == {args.region!r}: {len(sub)} rows")

    if var_col:
        if args.variable:
            sub = sub[sub[var_col].astype(str).str.contains(
                args.variable, case=False, na=False, regex=False)]
            require_nonempty(sub, f"{var_col} contains {args.variable!r}")
            print(f"  {var_col} contains {args.variable!r}: {len(sub)} rows")
        elif sub[var_col].nunique() > 1:
            die(f"this file holds {sub[var_col].nunique()} variables:\n"
                f"       {sorted(map(str, sub[var_col].unique()))}\n"
                f"       Pass --variable to choose the 0-4 female population.\n"
                f"       Without it the loop would overwrite one scenario "
                f"with another.")

    dup = sub[sub.duplicated(scn_col, keep=False)]
    if len(dup):
        die(f"{len(dup)} rows share a scenario after filtering. Writing them "
            f"in a loop would silently keep only the last one.\n"
            f"       Narrow --region / --variable further.")

    print(f"\ntime stamp: {'interval midpoint (t-2.5)' if args.midpoint else 'interval endpoint (t)'}")
    for _, row in sub.iterrows():
        scn = str(row[scn_col]).strip()
        grid, births = series_for_row(row, year_cols, args.unit_scale,
                                      args.midpoint, args.start, args.end)
        path = f"{args.prefix}_{scn.lower().replace(' ', '')}.csv"
        pd.DataFrame({"year": grid, "births": births}).to_csv(path, index=False)
        out = pd.DataFrame({"year": grid, "births": births})
        total, _ = summarise(out, f"IIASA {scn} (reconstructed)", path,
                             start=args.start, end=args.end)

        _, alt = series_for_row(row, year_cols, args.unit_scale,
                                not args.midpoint, args.start, args.end)
        print(f"    other time stamp would give B = {alt.sum():.4g} "
              f"({(alt.sum() / total - 1) * 100:+.1f}%)")

    print("\nreminder: these series are reconstructed, not summed from an "
          "annual series,\nand they are not corrected for under-five "
          "mortality. Say so in the caption.")


if __name__ == "__main__":
    main()
