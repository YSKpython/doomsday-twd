"""
doomsday_demography.py -- Table 2 of the paper.

The paper's Data and Code section promises this script; it computes the
near-term growth potential from a projection's ANNUAL BIRTH SERIES:

    B_2100  = sum_{t=START_YEAR}^{2100} B(t)
    N_cum   = n_obs + B_2100
    g_2100  = ln(N_cum / n_obs)

Input: a CSV with columns `year` and `births` (annual live births, in
persons). UN WPP publishes this series directly, so the sum is a plain
addition and a referee can reproduce it.

Do NOT type values into the paper by hand. Every number in Table 2 must
come out of this script.

Usage:
    python3 doomsday_demography.py --selftest
    python3 doomsday_demography.py wpp2024_medium.csv --label "UN WPP 2024, medium"
    python3 doomsday_demography.py *.csv --latex
"""

import argparse
import csv
import math
import sys

from doomsday_core import N_OBS, K_DOOM

# PRB's ~117 billion is an estimate "by 2022", so the projected sum must
# start in 2023. Starting later drops those births from both terms.
START_YEAR, END_YEAR = 2026, 2100

# UN WPP reports counts in THOUSANDS. Pass --scale 1000 for raw WPP values.
# convert_wpp.py already applies it, so its output needs --scale 1 (default).
DEFAULT_SCALE = 1.0


def read_births(path, scale=1.0):
    """Return {year: births}. Accepts commas and scientific notation."""
    out = {}
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        cols = {c.lower().strip(): c for c in (reader.fieldnames or [])}
        if "year" not in cols or "births" not in cols:
            raise SystemExit(
                f"{path}: need columns 'year' and 'births', got "
                f"{reader.fieldnames}")
        for row in reader:
            y = int(float(row[cols["year"]]))
            b = float(str(row[cols["births"]]).replace(",", "").strip())
            out[y] = b * scale
    return out


def growth_potential(births, n_obs=N_OBS, start=START_YEAR, end=END_YEAR):
    have = [y for y in range(start, end + 1) if y in births]
    missing = [y for y in range(start, end + 1) if y not in births]
    total = sum(births[y] for y in have)
    n_cum = n_obs + total
    return {
        "B_2100": total,
        "N_cum": n_cum,
        "g_2100": math.log(n_cum / n_obs),
        "years_used": len(have),
        "years_missing": missing,
    }


def report(label, res, n_obs=N_OBS):
    print(f"\n{label}")
    print("-" * max(len(label), 52))
    if res["years_missing"]:
        m = res["years_missing"]
        print(f"  WARNING: {len(m)} year(s) missing "
              f"({m[0]}..{m[-1]}) -- B_2100 is an UNDERCOUNT")
    print(f"  years summed        : {res['years_used']}")
    print(f"  B_2100              : {res['B_2100']:.4g}")
    print(f"  n_obs               : {n_obs:.4g}")
    print(f"  N_cum(2100)         : {res['N_cum']:.4g}")
    print(f"  g_2100              : {res['g_2100']:.4f}")
    print(f"  g_tail threshold    : {math.log(K_DOOM) - res['g_2100']:.4f}"
          f"   (bound fails only above this)")
    mean_rate = res["B_2100"] / max(res["years_used"], 1)
    print(f"  implied mean births : {mean_rate:.3g} / year"
          f"   (sanity check against ~1.3e8 today)")
    if not (1e7 <= mean_rate <= 5e8):
        off = 1.15e8 / mean_rate if mean_rate else float("inf")
        print(f"  *** UNIT WARNING: implied rate is off by ~{off:.0f}x. "
              f"Raw WPP counts are in thousands -- try --scale 1000. ***")


def sci(x, sig=3):
    """Format as LaTeX scientific notation: 6.09 \\times 10^{9}."""
    if x == 0:
        return "0"
    exp = int(math.floor(math.log10(abs(x))))
    mant = x / 10 ** exp
    return f"{mant:.{sig - 1}f} \\times 10^{{{exp}}}"


def latex_row(label, res):
    return (f"{label} & ${sci(res['B_2100'], 3)}$ & "
            f"${sci(res['N_cum'], 4)}$ & "
            f"${res['g_2100']:.4f}$ \\\\")


def selftest():
    """Synthetic series: verify the plumbing before real data arrives."""
    print("SELF-TEST -- synthetic series, 1.30e8 births in 2026 falling "
          "linearly to 1.00e8 in 2100")
    births = {}
    for i, y in enumerate(range(START_YEAR, END_YEAR + 1)):
        frac = i / (END_YEAR - START_YEAR)
        births[y] = 1.30e8 + frac * (1.00e8 - 1.30e8)
    res = growth_potential(births)
    report("synthetic linear-decline scenario", res)
    expected = 75 * 1.15e8
    print(f"\n  closed-form expectation for B_2100 (75 * mean 1.15e8) "
          f"= {expected:.4g}")
    print(f"  agreement: {abs(res['B_2100'] - expected) / expected:.2%}")
    print("\n  This is a plumbing test only. It is NOT a demographic result "
          "and must\n  never be reported in the paper.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv", nargs="*", help="CSV files with year,births")
    ap.add_argument("--label", default=None,
                    help="one label for a single file")
    ap.add_argument("--labels", default=None,
                    help="semicolon-separated, one per file, in order")
    ap.add_argument("--n-obs", type=float, default=N_OBS)
    ap.add_argument("--scale", type=float, default=DEFAULT_SCALE,
                    help="multiply the births column (raw WPP thousands: 1000)")
    ap.add_argument("--start", type=int, default=START_YEAR)
    ap.add_argument("--end", type=int, default=END_YEAR)
    ap.add_argument("--latex", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        selftest()
        return
    if not args.csv:
        ap.print_help()
        sys.exit("\nNo CSV given. Run with --selftest to check the plumbing.")

    labels = [x.strip() for x in args.labels.split(";")] if args.labels else None
    if labels and len(labels) != len(args.csv):
        sys.exit(f"--labels has {len(labels)} entries but {len(args.csv)} files "
                 f"were given")

    rows = []
    for i, path in enumerate(args.csv):
        label = labels[i] if labels else (args.label or path)
        res = growth_potential(read_births(path, scale=args.scale),
                               n_obs=args.n_obs,
                               start=args.start, end=args.end)
        report(label, res, n_obs=args.n_obs)
        rows.append((label, res))

    if args.latex:
        print("\n% ---- LaTeX body for Table 2 ----")
        for label, res in rows:
            print(latex_row(label, res))


if __name__ == "__main__":
    main()
