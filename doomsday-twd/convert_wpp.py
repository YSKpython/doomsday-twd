#!/usr/bin/env python3
"""
convert_wpp.py -- UN World Population Prospects 2024 -> year,births

Reads a UN Data Portal export of the "Total births by sex" indicator and
writes one two-column `year,births` file per fertility variant.

TWO THINGS THAT DIFFER BETWEEN UN DOWNLOADS
-------------------------------------------
Units. The Data Portal returns births in PERSONS (Afghanistan 2026 comes
back as 1520756). The bulk WPP "Demographic Indicators" files return
THOUSANDS. The default here is 1.0; pass --scale 1000 for the bulk files.
Either way the script checks the implied mean annual birth rate against
the world total of about 1.3e8 and warns if it is implausible.

Variant labels. The Data Portal labels the central projection "Median",
while the WPP reports call it the "medium" variant. Both spellings are
accepted; output files are named low / medium / high regardless.

World aggregate. Data Portal exports are often country-level with no
"World" row. If a World row is present it is used. Otherwise the script
sums countries -- but first drops any location in the UN aggregate id
range (>= 900, e.g. "World", "Less developed regions"), because summing
those alongside countries double-counts. It reports what it dropped.

Usage:
    python3 convert_wpp.py export.csv --list
    python3 convert_wpp.py export.csv
    python3 convert_wpp.py bulk_indicators.csv --scale 1000
"""
import argparse

import pandas as pd

from _common import (die, normalise_columns, pick_column, require_nonempty,
                     require_one_row_per_year, summarise, write_series)

SLUG = {"median": "medium", "medium": "medium",
        "low": "low", "low-fertility": "low", "low fertility": "low",
        "high": "high", "high-fertility": "high", "high fertility": "high"}
UN_AGGREGATE_ID = 900          # UN convention: real countries/areas are below this


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--variants", default="Median,Low-fertility,High-fertility")
    ap.add_argument("--indicator", default="births")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="1.0 for Data Portal exports (persons); "
                         "1000 for bulk WPP files (thousands)")
    ap.add_argument("--prefix", default="wpp2024")
    ap.add_argument("--start", type=int, default=None)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    df = normalise_columns(pd.read_csv(args.csv, low_memory=False))

    loc_col = pick_column(df, ["location", "locationname", "location_name"], "location")
    lid_col = pick_column(df, ["locationid", "location_id"], "location id",
                          required=False)
    var_col = pick_column(df, ["variant", "variantlabel", "variantname"], "variant")
    yr_col = pick_column(df, ["time", "timelabel", "year"], "year")
    val_col = pick_column(df, ["value", "val"], "value")
    ind_col = pick_column(df, ["indicatorname", "indicator",
                               "indicatorshortname"], "indicator", required=False)
    sex_col = pick_column(df, ["sex", "sexname"], "sex", required=False)
    age_col = pick_column(df, ["age", "agelabel"], "age", required=False)

    if args.list:
        for c in (loc_col, var_col, ind_col, sex_col, age_col):
            if c:
                v = sorted(map(str, df[c].dropna().unique()))
                print(f"{c:14s}: {v[:12]}{' ...' if len(v) > 12 else ''} ({len(v)} distinct)")
        print(f"{yr_col:14s}: {df[yr_col].min()} .. {df[yr_col].max()}")
        if lid_col:
            print(f"{'aggregates':14s}: "
                  f"{(df[lid_col] >= UN_AGGREGATE_ID).sum()} rows with id >= {UN_AGGREGATE_ID}")
        return

    print(f"read {len(df)} rows from {args.csv}")
    print(f"years present: {df[yr_col].min()} .. {df[yr_col].max()}")
    if args.start and df[yr_col].min() > args.start:
        print(f"  *** the export starts at {df[yr_col].min()}, after the "
              f"requested {args.start}; re-download with the earlier start ***")

    sub = df
    if ind_col:
        sub = sub[sub[ind_col].astype(str).str.contains(args.indicator,
                                                        case=False, na=False)]
        require_nonempty(sub, f"{ind_col} contains {args.indicator!r}")
    for col, keep in ((sex_col, ("both sexes", "both", "total")),
                      (age_col, ("total", "all ages", "all"))):
        if col and sub[col].nunique() > 1:
            m = sub[col].astype(str).str.strip().str.lower().isin(keep)
            if m.any():
                sub = sub[m]
                print(f"  {col} restricted to the aggregate: {len(sub)} rows")

    world = sub[sub[loc_col].astype(str).str.strip().str.lower() == "world"]
    if len(world):
        print("  using the 'World' rows directly")
        sub = world
        aggregate = False
    else:
        n_before = sub[loc_col].nunique()
        if lid_col:
            dropped = sorted(map(str, sub.loc[sub[lid_col] >= UN_AGGREGATE_ID,
                                              loc_col].unique()))
            if dropped:
                sub = sub[sub[lid_col] < UN_AGGREGATE_ID]
                print(f"  dropped {len(dropped)} aggregate location(s) to avoid "
                      f"double counting: {dropped[:6]}"
                      f"{' ...' if len(dropped) > 6 else ''}")
            else:
                print(f"  no aggregate ids present; all {n_before} locations are "
                      f"countries or areas")
        else:
            print(f"  *** no location-id column: cannot verify that the "
                  f"{n_before} locations exclude regional aggregates. "
                  f"Check this by hand. ***")
        print(f"  no 'World' row -- summing {sub[loc_col].nunique()} countries/areas")
        aggregate = True

    written = []
    for raw in [v.strip() for v in args.variants.split(",")]:
        vs = sub[sub[var_col].astype(str).str.strip().str.lower() == raw.lower()]
        if len(vs) == 0:
            present = sorted(map(str, sub[var_col].dropna().unique()))
            die(f"variant {raw!r} matched 0 rows. Present: {present}")
        if aggregate:
            vs = (vs.groupby(yr_col, as_index=False)[val_col].sum())
        require_one_row_per_year(vs, yr_col,
                                 [c for c in (sex_col, age_col, loc_col) if c])
        slug = SLUG.get(raw.lower(), raw.lower().replace(" ", "_"))
        path = f"{args.prefix}_{slug}.csv"
        out = write_series(vs, yr_col, val_col, args.scale, path,
                           start=args.start or 0)
        summarise(out, f"UN WPP 2024, {raw}", path,
                  start=int(out['year'].min()), end=int(out['year'].max()))
        written.append(path)
    print(f"\nwrote: {', '.join(written)}   (scale {args.scale:g})")


if __name__ == "__main__":
    main()
