"""
doomsday_figures.py -- Figures 1 and 2, and the exact coordinate blocks
that are hard-coded into the LaTeX source.

Figure 1  the (alpha, beta) identifiability plane
Figure 2  sensitivity of the tail at k = 20, for finite N_max

The .tex file embeds Figure 2's coordinates so that it compiles without
data and without pgfmath overflow. This script regenerates them, so the
archive is verifiable: the printed block must match the .tex byte for
byte after rounding.

Run:  python3 doomsday_figures.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import os

import pathlib
from doomsday_core import K_DOOM, tail

_HERE = pathlib.Path(__file__).resolve().parent
_FIGDIR = _HERE / "figures" if (_HERE / "figures").is_dir() else _HERE

VIOLET, TEAL = "#7F77DD", "#1D9E75"
ALPHA_GRID = np.round(np.arange(0.05, 4.001, 0.05), 4)


def figure1(path="figures/doomsday_fig1.png"):
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot([0, 2], [2, 0], color=VIOLET, lw=2.5)
    ax.plot([0, 1], [1, 0], color=TEAL, lw=2.5)
    ax.axvline(1, color="gray", lw=0.8, ls="--", alpha=0.5)
    ax.axhline(1, color="gray", lw=0.8, ls="--", alpha=0.5)
    for (x, y, c, lab, ha) in [
            (1, 1, VIOLET, "Carter", "right"),
            (0, 1, TEAL, "SIA", "left"),
            (1, 0, TEAL, "Absolute window", "left")]:
        ax.plot(x, y, "o", color=c, ms=9, zorder=5)
        ax.annotate(lab, (x, y), textcoords="offset points",
                    xytext=(8 if ha == "left" else -8, 8),
                    ha=ha, fontsize=10)
    ax.text(1.32, 0.95, r"$\alpha+\beta=2$", color=VIOLET, fontsize=11)
    ax.text(0.52, 0.70, r"$\alpha+\beta=1$", color=TEAL, fontsize=11)
    ax.set_xlim(-0.05, 2.3)
    ax.set_ylim(-0.05, 2.3)
    ax.set_xlabel(r"prior exponent $\alpha$", fontsize=12)
    ax.set_ylabel(r"window exponent $\beta$", fontsize=12)
    ax.set_title("The identifiability plane\n"
                 r"the tail depends on $(\alpha,\beta)$ only through their sum",
                 fontsize=12)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def figure2(path="figures/doomsday_fig2.png"):
    a = np.linspace(0.05, 4.0, 400)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(a, tail(K_DOOM, a, 1.0, 1e6), color=VIOLET, lw=2.5,
            label=r"$\beta=1$ (window scales with $N$), $R=10^{6}$")
    ax.plot(a, tail(K_DOOM, a, 0.0, 1e6), color=TEAL, lw=2.5,
            label=r"$\beta=0$ (absolute window), $R=10^{6}$")
    ax.plot(a, tail(K_DOOM, a, 0.0, 1e3), color=TEAL, lw=2.5, ls="--",
            label=r"$\beta=0$ (absolute window), $R=10^{3}$")
    ax.axvline(1.0, color="black", lw=1.8, ls="--",
               label=r"Jeffreys prior, $\alpha=1$")
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 1.04)
    ax.set_xlabel(r"prior exponent $\alpha$", fontsize=12)
    ax.set_ylabel(r"$P(N_{\rm total} > 20\,n_{\rm obs})$", fontsize=12)
    ax.set_title("Sensitivity of the doomsday tail at $k=20$", fontsize=12)
    ax.legend(fontsize=9, loc="upper right", frameon=False)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def emit_tex_coordinates():
    """Print the exact blocks embedded in the .tex source."""
    for label, beta, R in [("beta=1 proportional, R=1e6", 1.0, 1e6),
                           ("beta=0 absolute,     R=1e6", 0.0, 1e6),
                           ("beta=0 absolute,     R=1e3", 0.0, 1e3)]:
        print(f"% --- {label} ---")
        pts = [f"({x:.2f},{tail(K_DOOM, x, beta, R):.5f})" for x in ALPHA_GRID]
        for i in range(0, len(pts), 8):
            print(" ".join(pts[i:i + 8]))
        print()


if __name__ == "__main__":
    os.makedirs("figures", exist_ok=True)
    print("wrote", figure1())
    print("wrote", figure2())
    print("\nOne-unit shift, verified on the plotted grid:")
    for x in (0.05, 0.55, 1.00):
        lhs = tail(K_DOOM, x, 1.0, 1e6)
        rhs = tail(K_DOOM, x + 1.0, 0.0, 1e6)
        print(f"  P(alpha={x:.2f}, beta=1) = {lhs:.5f}   "
              f"P(alpha={x + 1:.2f}, beta=0) = {rhs:.5f}   "
              f"diff = {abs(lhs - rhs):.1e}")
    print()
    emit_tex_coordinates()
