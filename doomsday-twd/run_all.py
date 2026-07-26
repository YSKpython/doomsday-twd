#!/usr/bin/env python3
"""
run_all.py -- reproduce every number in the paper with one command.

    python run_all.py

Works the same in PowerShell, cmd and bash: it shells out with the very
interpreter that is running it, so there is no `&&`, no line continuation
and no quoting to get wrong.

Source files are looked up in ./ , ./data/ and ./data/raw/ , so both a
flat working folder and the repository layout work unchanged:

    unpopulation_dataportal_*.csv          UN WPP 2024 export
    ssp_snapshot_*.csv                     IIASA SSP snapshot
    IHME_*LIVE_BIRTHS*.CSV                 IHME live births -- NOT in the
                                           repository; download it yourself
                                           (see data/README.md)

Derived series are written to ./data/ when that folder exists, otherwise
next to this script.
"""

import subprocess
import sys
from pathlib import Path

PY = sys.executable
HERE = Path(__file__).resolve().parent
SEARCH = [HERE, HERE / "data", HERE / "data" / "raw"]
OUT = HERE / "data" if (HERE / "data").is_dir() else HERE


def rel(p):
    return str(p.relative_to(HERE)).replace("\\", "/")


def find(patterns, what, required=True):
    for folder in SEARCH:
        if not folder.is_dir():
            continue
        for pat in patterns:
            hits = sorted(folder.glob(pat))
            if hits:
                if len(hits) > 1:
                    print(f"  note: {len(hits)} files match {pat}; "
                          f"using {hits[0].name}")
                return rel(hits[0])
    msg = f"could not find the {what} file (looked for {', '.join(patterns)})"
    if required:
        sys.exit(f"\nSTOP: {msg}\n      searched: "
                 f"{', '.join(rel(f) or '.' for f in SEARCH if f.is_dir())}\n")
    print(f"  SKIPPING: {msg}")
    return None


def run(args, title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
    r = subprocess.run([PY] + args, cwd=HERE)
    if r.returncode != 0:
        sys.exit(f"\nSTOP: '{' '.join(args)}' failed with code {r.returncode}.\n"
                 f"Fix that before continuing; later steps depend on it.\n")


def main():
    print(f"interpreter : {PY}")
    print(f"folder      : {HERE}")
    print(f"output to   : {rel(OUT) or '.'}/")

    wpp = find(["unpopulation_dataportal_*.csv", "*dataportal*.csv"], "UN WPP")
    ssp = find(["ssp_snapshot_*.csv"], "IIASA SSP")
    ihme = find(["IHME_*LIVE_BIRTHS*.CSV", "IHME_*LIVE_BIRTHS*.csv",
                 "*LIVE_BIRTHS*.CSV", "*LIVE_BIRTHS*.csv"],
                "IHME live births", required=False)
    if ihme is None:
        print("  -> Table 2 will have six rows instead of seven.")
        print("  -> The IHME file is not redistributable; see data/README.md.")

    op = f"{rel(OUT)}/" if OUT != HERE else ""

    run(["convert_wpp.py", wpp, "--prefix", f"{op}wpp2024"],
        "1/6  UN WPP 2024 -> year,births")
    if ihme:
        run(["convert_ihme.py", ihme, "--out", f"{op}ihme2020_reference.csv"],
            "2/6  IHME 2020 -> year,births")
    run(["convert_ssp.py", ssp, "--variable", "Female|Age 0-4",
         "--no-midpoint", "--prefix", f"{op}ssp"],
        "3/6  IIASA SSP -> reconstructed year,births")

    series = [f"{op}wpp2024_low.csv", f"{op}wpp2024_medium.csv",
              f"{op}wpp2024_high.csv"]
    labels = ["UN WPP 2024, low", "UN WPP 2024, medium", "UN WPP 2024, high"]
    if ihme:
        series.append(f"{op}ihme2020_reference.csv")
        labels.append("IHME / Lancet 2020")
    series += [f"{op}ssp_ssp1.csv", f"{op}ssp_ssp2.csv", f"{op}ssp_ssp3.csv"]
    labels += ["IIASA SSP1", "IIASA SSP2", "IIASA SSP3"]

    missing = [s for s in series if not (HERE / s).exists()]
    if missing:
        sys.exit(f"\nSTOP: the converters did not produce {missing}.\n")

    run(["doomsday_demography.py"] + series
        + ["--labels", ";".join(labels), "--latex"], "4/6  Table 2")
    run(["doomsday_checks.py"], "5/6  verification suite")
    run(["doomsday_tables.py"], "6/6  Table 1")
    run(["doomsday_figures.py"], "extra  Figures 1-2 and the .tex coordinates")

    print("\n" + "=" * 70)
    print("DONE.")
    print("The 'LaTeX body for Table 2' block above is formatted exactly as")
    print("the manuscript expects: paste it between \\midrule and \\bottomrule.")
    print("Every converter should have reported 'years written: 75'.")
    if not ihme:
        print("\nTable 2 is missing its IHME row. See data/README.md for how to")
        print("obtain the source file and reproduce that row.")
    print("=" * 70)


if __name__ == "__main__":
    main()
