#!/usr/bin/env python3
"""
convert_ihme.py -- IHME / Lancet 2020 live births -> year,births

Reads the GBD 2017 population-forecast live-births file and writes a
two-column `year,births` series for the Global Reference scenario.

The IHME data file itself is NOT redistributed with this repository:
the Free-of-Charge Non-Commercial User Agreement permits publishing
links to IHME's download facilities but not providing downloads from
your own hosting. Download it yourself, accept the agreement, and run
this script; it reproduces the IHME row of Table 2 exactly.

Usage:
    python3 convert_ihme.py IHME_POP_2017_2100_LIVE_BIRTHS_Y2020M05D01.CSV
    python3 convert_ihme.py <file> --list
"""
import argparse

import pandas as pd

from _common import (END_YEAR, START_YEAR, die, normalise_columns,
                     pick_column, require_nonempty, require_one_row_per_year,
                     summarise, write_series)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--location", default="Global")
    ap.add_argument("--scenario", default="Reference")
    ap.add_argument("--out", default="ihme2020_reference.csv")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="IHME live births are already in persons")
    ap.add_argument("--start", type=int, default=START_YEAR)
    ap.add_argument("--end", type=int, default=END_YEAR)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    df = normalise_columns(pd.read_csv(args.csv, low_memory=False))

    loc_col = pick_column(df, ["location_name", "location"], "location")
    scn_col = pick_column(df, ["scenario_name", "scenario"], "scenario")
    yr_col = pick_column(df, ["year_id", "year"], "year")
    val_col = pick_column(df, ["val", "value", "mean"], "value")
    sex_col = pick_column(df, ["sex_name", "sex"], "sex", required=False)
    age_col = pick_column(df, ["age_group_name", "age_name", "age_group"],
                          "age group", required=False)
    met_col = pick_column(df, ["metric_name", "metric"], "metric",
                          required=False)
    mea_col = pick_column(df, ["measure_name", "measure"], "measure",
                          required=False)

    if args.list:
        for c in (loc_col, scn_col, sex_col, age_col, met_col, mea_col):
            if c:
                vals = sorted(map(str, df[c].dropna().unique()))
                print(f"{c:18s}: {vals[:12]}{' ...' if len(vals) > 12 else ''}")
        print(f"{yr_col:18s}: {df[yr_col].min()} .. {df[yr_col].max()}")
        return

    print(f"read {len(df)} rows from {args.csv}")

    sub = df[df[loc_col].astype(str).str.strip() == args.location]
    require_nonempty(sub, f"{loc_col} == {args.location!r}")
    print(f"  {loc_col} == {args.location!r}: {len(sub)} rows")

    sub = sub[sub[scn_col].astype(str).str.contains(args.scenario, case=False,
                                                    na=False)]
    require_nonempty(sub, f"{scn_col} contains {args.scenario!r}")
    print(f"  {scn_col} contains {args.scenario!r}: {len(sub)} rows")

    # Counts, not rates; and the both-sexes / all-ages aggregate.
    if met_col and sub[met_col].nunique() > 1:
        m = sub[sub[met_col].astype(str).str.contains("number", case=False,
                                                      na=False)]
        if len(m):
            sub = m
            print(f"  {met_col} restricted to counts: {len(sub)} rows")
    for col, keep in ((sex_col, ("both", "both sexes", "total")),
                      (age_col, ("all ages", "all age", "total", "<1 year"))):
        if col and sub[col].nunique() > 1:
            mask = sub[col].astype(str).str.strip().str.lower().isin(keep)
            if mask.any():
                sub = sub[mask]
                print(f"  {col} restricted to the aggregate: {len(sub)} rows")

    require_one_row_per_year(sub, yr_col,
                             [c for c in (sex_col, age_col, met_col, mea_col)
                              if c])

    out = write_series(sub, yr_col, val_col, args.scale, args.out,
                       start=args.start, end=args.end)
    summarise(out, "IHME / Lancet 2020, Reference", args.out,
              start=args.start, end=args.end)


if __name__ == "__main__":
    main()
