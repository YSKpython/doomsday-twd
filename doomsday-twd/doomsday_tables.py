"""
doomsday_tables.py -- generates Table 1 of the paper (positions in
(alpha, beta) coordinates) and emits the LaTeX body.

Run:  python3 doomsday_tables.py
"""

import numpy as np
from doomsday_core import N_OBS, K_DOOM, POSITIONS, R_GRID, tail, \
    posterior_median_ratio

SEP = "=" * 84


def main():
    print(SEP)
    print("Table 1 -- existing positions in (alpha, beta) coordinates")
    print(f"k = {K_DOOM},  n_obs = {N_OBS:.3g}  (PRB, Haub & Kaneda 2022 revision)")
    print(SEP)

    head = (f"{'position':<34}{'a':>4}{'b':>4}{'sig':>5}"
            + "".join(f"{'R=1e'+str(int(np.log10(R))):>10}" for R in R_GRID)
            + f"{'R->inf':>10}")
    print(head)
    print("-" * len(head))
    for label, a, b in POSITIONS:
        s = a + b
        row = f"{label:<34}{a:4.0f}{b:4.0f}{s:5.0f}"
        for R in R_GRID:
            row += f"{tail(K_DOOM, a, b, R):10.4f}"
        lim = tail(K_DOOM, a, b)
        row += f"{lim:10.4f}" + ("  (limit)" if s <= 1 else "")
        print(row)

    print("\nNote: entries with sigma <= 1 reach 1 only as an improper limit.")
    print("Carter's 5% is nearly independent of R; the sigma = 1 results")
    print("are not. See Sec. 3.4 of the paper.\n")

    print("% ---- LaTeX body for Table 1 (paste between \\midrule and \\bottomrule)")
    for label, a, b in POSITIONS:
        s = a + b
        cells = " & ".join(f"{tail(K_DOOM, a, b, R):.4f}" for R in R_GRID)
        lim = tail(K_DOOM, a, b)
        lim_s = "1" if s <= 1 else f"{lim:.4f}"
        tex = label.replace("&", r"\&")
        print(f"{tex:<34} & {a:.0f} & {b:.0f} & {s:.0f} & {cells} & {lim_s} \\\\")

    print("\n" + SEP)
    print("Posterior median translation (paper Sec. 4.3)")
    print(SEP)
    for label, a, b in POSITIONS:
        if a + b <= 1:
            continue
        m = posterior_median_ratio(a, b)
        print(f"  {label:<34} median N_total = {m:.3f} * n_obs "
              f"= {m * N_OBS:.4g}")


if __name__ == "__main__":
    main()
