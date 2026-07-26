"""Shared helpers for the source-data converters."""
import sys
import pandas as pd

try:
    from doomsday_core import N_OBS
except ImportError:                      # standalone use
    N_OBS = 1.17e11

# ONE KNOB FOR THE WHOLE PIPELINE.
# 2026 matches the manuscript as submitted. n_obs is PRB's estimate as of
# 2022, so births in 2023-2025 fall in neither term and are omitted; this
# understates every g_2100 by about 0.003. Section 4.2 discloses it.
# To switch, change this line (or pass --start to every script) and re-run
# ALL converters -- a table mixing start years is worse than either choice.
START_YEAR, END_YEAR = 2026, 2100


def die(msg):
    sys.exit(f"\nERROR: {msg}\n")


def normalise_columns(df):
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df


def pick_column(df, candidates, what, required=True):
    for c in candidates:
        if c in df.columns:
            return c
    if required:
        die(f"could not find a {what} column. Tried {candidates}.\n"
            f"       Columns present: {list(df.columns)}\n"
            f"       Pass the right name explicitly on the command line.")
    return None


def require_nonempty(df, description):
    if len(df) == 0:
        die(f"the filter '{description}' matched 0 rows. Nothing was written.")
    return df


def require_one_row_per_year(df, year_col, context_cols):
    """Catch the silent multiplication that an unset sex/age filter causes."""
    dup = df[df.duplicated(year_col, keep=False)]
    if len(dup):
        years = sorted(dup[year_col].unique())[:3]
        cols = [c for c in context_cols if c in df.columns]
        sample = dup[dup[year_col] == years[0]][[year_col] + cols].head(8)
        die(f"{len(dup)} rows share a year (e.g. {years}).\n"
            f"       Summing them would multiply the birth count.\n"
            f"       These rows differ in some column you have not filtered:\n\n"
            f"{sample.to_string(index=False)}\n\n"
            f"       Add the missing filter and rerun.")
    return df


def write_series(df, year_col, value_col, scale, out_path,
                 start=START_YEAR, end=END_YEAR):
    out = (df[[year_col, value_col]]
           .rename(columns={year_col: "year", value_col: "births"})
           .astype({"year": int, "births": float})
           .sort_values("year"))
    out["births"] *= scale
    out = out[(out["year"] >= start) & (out["year"] <= end)]
    out.to_csv(out_path, index=False)
    return out


def summarise(out, label, out_path, n_obs=N_OBS,
              start=START_YEAR, end=END_YEAR):
    import math
    total = float(out["births"].sum())
    n_years = len(out)
    expected = end - start + 1
    g = math.log((n_obs + total) / n_obs)
    mean_rate = total / n_years if n_years else float("nan")
    print(f"\n  {label} -> {out_path}")
    print(f"    years written      : {n_years}   (expected {expected})")
    if n_years != expected:
        print(f"    *** WARNING: {expected - n_years} year(s) missing; "
              f"B is an undercount ***")
    print(f"    B_{end}             : {total:.4g}")
    print(f"    g_{end}             : {g:.4f}")
    print(f"    mean annual births : {mean_rate:.3g}"
          f"   (world total today is about 1.3e8)")
    if not (1e7 <= mean_rate <= 5e8):
        print(f"    *** UNIT WARNING: that rate is implausible. Check --scale. ***")
    return total, g
