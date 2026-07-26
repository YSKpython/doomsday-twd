import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# =====================================================================
# DOOMSDAY ARGUMENT — Observation-Adjusted Framework
# Minimal model  (figure 1 = heatmap)
# =====================================================================
#
# HONESTY CONTRACT (read before trusting any number below):
#
# The growth-potential rate lambda and the window-fraction f used
# here are ILLUSTRATIVE PLACEHOLDERS.  They are NOT calibrated to
# published demographic projections (UN, IIASA, etc.).  A calibrated
# value can be substituted by editing the LAMBDA_GRID / F_GRID input
# blocks below; the framework (and the paper's tables) is unchanged
# by that substitution.
#
# CORE INSIGHT (structural parallel with the SOM):
#
#   Carter's Doomsday Argument assumes  n_obs / N_total ~ U(0,1).
#   This is equivalent to assuming the "growth potential"
#   g = r * T_remaining  ~  Exponential(rate = 1).
#
#   The SOM showed that the Fermi Paradox conflates EXISTENCE with
#   OBSERVABILITY:  kappa << 1  =>  silence is the default.
#
#   Here we show the DA conflates EXISTENCE with OBSERVABILITY in
#   the same way:  the observation "I am the n-th human" is only
#   possible during the "demographic transparency window" — the era
#   when a civilization can count its own population.  This window
#   is a tiny fraction of N_total, analogous to kappa << 1.
#
#   The DA's prediction  P(N > 20n) = 5%  is NOT a logical necessity.
#   It is a consequence of the implicit assumption  lambda = 1.
#   Change the observation model, change the conclusion.
#
# IMPORTANT (per the paper's dimensional allocation):
#   The growth-potential rate lambda is a TRAJECTORY property,
#   not a reference-class property.  It encodes the population
#   dynamics (exponential, logistic, collapse) and the remaining
#   civilization lifetime.  The DA's lambda = 1 corresponds to
#   a specific trajectory family, not to "rational reasoning."
#
# =====================================================================

LN10 = np.log(10.0)

# ----- Observed birth rank -----
N_OBS = 1.0e11            # ~100 billion humans have ever lived
K_DOOM = 20               # "doomsday multiplier": DA predicts P(N>20n)=5%
LN_K = np.log(K_DOOM)     # ln(20) ≈ 2.996

# =====================================================================
# 1. CARTER'S DOOMSDAY ARGUMENT (baseline)
# =====================================================================
# Assumption: n_obs / N_total ~ Uniform(0,1)
# Equivalently: growth potential g = ln(N_total / n_obs) ~ Exp(1)
#
# With Jeffreys prior P(N) ∝ 1/N:
#   P(N_total | n_obs) = n_obs / N_total^2   for N_total >= n_obs
#   P(N_total > k * n_obs | n_obs) = 1/k
# =====================================================================

def da_prob(k):
    """P(N_total > k * n_obs) under Carter's DA = 1/k."""
    return 1.0 / np.asarray(k, dtype=float)

def da_posterior(N_total, n_obs=N_OBS):
    """P(N_total | n_obs) under Carter's DA with Jeffreys prior.
    Returns n_obs / N_total^2 for N_total >= n_obs, else 0."""
    N = np.asarray(N_total, dtype=float)
    return np.where(N >= n_obs, n_obs / N**2, 0.0)

def da_ati(k):
    """Anthropic Tension Index under Carter's DA.
    A = -log10 P(N > k*n) = log10(k)."""
    return np.log10(np.asarray(k, dtype=float))

# =====================================================================
# 2. GROWTH-POTENTIAL MODEL (corrected)
# =====================================================================
# N_total = n_obs * exp(g),  where g = r * T_remaining.
#
# Under DA:          g ~ Exponential(rate=1)  =>  P(N>k*n) = 1/k
# Under corrected:   g ~ Exponential(rate=lambda)  =>  P(N>k*n) = k^{-lambda}
#
# lambda is the "growth-potential rate":
#   lambda = 1  : DA holds (growth potential ~ Exp(1))
#   lambda < 1  : larger growth potential than DA assumes (optimistic)
#   lambda > 1  : smaller growth potential than DA assumes (pessimistic)
#
# The ATI under the corrected model:
#   A(k, lambda) = lambda * log10(k)
#
# The "DA inflation factor" (how much the DA over/under-estimates tension):
#   A_DA / A_corrected = 1 / lambda
# =====================================================================

def gp_prob(k, lam):
    """P(N_total > k * n_obs) under growth-potential model = k^{-lambda}."""
    k = np.asarray(k, dtype=float)
    return k ** (-lam)

def gp_ati(k, lam):
    """ATI under growth-potential model = lambda * log10(k)."""
    return lam * np.log10(np.asarray(k, dtype=float))

def gp_inflation(lam):
    """DA inflation factor: A_DA / A_corrected = 1/lambda.
    lambda < 1 => DA overestimates tension (doomsday less likely than DA says).
    lambda > 1 => DA underestimates tension (doomsday more likely than DA says)."""
    return 1.0 / lam

# =====================================================================
# 3. WINDOW-FRACTION MODEL (complementary formulation)
# =====================================================================
# The "demographic transparency window" covers W humans out of N_total.
# Window fraction:  f = W / N_total.
#
# Under DA:          f = 1  (every human is an observer)
# Under corrected:   f << 1 (only the transparency era is observable)
#
# The ATI inflation due to the window:
#   A_DA - A_corrected = log10(N_total) - log10(W) = log10(1/f)
#
# This is the exact analog of the SOM's kappa:
#   SOM:  tension inflated by 1/kappa  (observability filter)
#   DA:   tension inflated by 1/f      (transparency-window filter)
# =====================================================================

def wf_inflation(f):
    """Window-fraction inflation factor = 1/f.
    Analogous to 1/kappa in the SOM."""
    return 1.0 / np.asarray(f, dtype=float)

def wf_ati_correction(f):
    """ATI correction due to window fraction = log10(1/f).
    This is the amount by which the DA overestimates the surprisal
    of the observed rank, analogous to -log10(kappa) in the SOM."""
    return np.log10(1.0 / np.asarray(f, dtype=float))

# =====================================================================
# 4. REPRESENTATIVE TABLES (console)
# =====================================================================

print("=" * 78)
print("DOOMSDAY ARGUMENT — Observation-Adjusted Framework")
print("Minimal model (console tables; not used in paper)")
print("=" * 78)

# ----- Table 1: P(N > k*n) across lambda and k -----
print("\n--- Table 1: P(N_total > k * n_obs) ---")
print("(Carter's DA = lambda=1 row; corrected model = other rows)\n")

k_values = [2, 5, 10, 20, 50, 100]
lam_values = [0.25, 0.50, 1.00, 2.00, 4.00]

header = f"{'lambda':>8} |" + "".join(f"{'k='+str(k):>10}" for k in k_values) + " |  regime"
print(header)
print("-" * len(header))

for lam in lam_values:
    row = f"{lam:8.2f} |"
    for k in k_values:
        p = gp_prob(k, lam)
        row += f"{p:10.4f}"
    if lam < 1.0:
        regime = "optimistic (DA overestimates doom)"
    elif lam == 1.0:
        regime = "Carter's DA (baseline)"
    else:
        regime = "pessimistic (DA underestimates doom)"
    row += f" |  {regime}"
    print(row)

# ----- Table 2: ATI across scenarios -----
print("\n--- Table 2: Anthropic Tension Index A(k, lambda) ---")
print("(A = -log10 P(N > k*n); higher A = more 'surprising' observation)\n")

header2 = f"{'lambda':>8} |" + "".join(f"{'k='+str(k):>10}" for k in k_values) + " |  DA inflation"
print(header2)
print("-" * len(header2))

for lam in lam_values:
    row = f"{lam:8.2f} |"
    for k in k_values:
        a = gp_ati(k, lam)
        row += f"{a:10.3f}"
    infl = gp_inflation(lam)
    row += f" |  {infl:.2f}x"
    print(row)

# ----- Table 3: Window fraction and inflation -----
print("\n--- Table 3: Window-fraction inflation (SOM analog) ---")
print("(f = W / N_total;  inflation = 1/f, analogous to 1/kappa in SOM)\n")

f_values = [1.0, 0.1, 0.01, 0.001, 1e-4, 1e-5]

header3 = f"{'f = W/N':>10} | {'W (humans)':>14} | {'inflation 1/f':>14} | {'ATI correction':>14} |  interpretation"
print(header3)
print("-" * len(header3))

for f in f_values:
    W = f * 1e12  # illustrative: N_total ~ 1 trillion
    infl = wf_inflation(f)
    corr = wf_ati_correction(f)
    if f >= 1.0:
        interp = "DA holds (window = entire population)"
    elif f >= 0.01:
        interp = "moderate correction"
    else:
        interp = "DA dissolved (window << population)"
    print(f"{f:10.1e} | {W:14.2e} | {infl:14.2e} | {corr:14.3f} |  {interp}")

# =====================================================================
# 5. HEATMAP: P(N > k*n) vs (lambda, k)  ->  fig1.png
# =====================================================================
# This is the direct analog of fermi.py's fig1 (P(D=0) heatmap).
#
# x-axis: lambda (growth-potential rate, log scale)
# y-axis: k (doomsday multiplier, log scale)
# color:  P(N_total > k * n_obs) = k^{-lambda}
#
# The DA's prediction (lambda=1) is marked as a vertical line.
# The key message: the DA's 5% prediction is ONE POINT in a
# two-dimensional parameter space, not a logical necessity.
# =====================================================================

lam_plot = np.logspace(-1, 1.5, 400)     # lambda: 0.1 to ~30
k_plot = np.logspace(np.log10(2), 3, 400) # k: 2 to 1000
LAM, K = np.meshgrid(lam_plot, k_plot)

P_mesh = K ** (-LAM)   # P(N > k*n) = k^{-lambda}

fig, ax = plt.subplots(figsize=(10, 7))

levels = [0.001, 0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.95]
contour = ax.contourf(LAM, K, P_mesh, levels=levels, cmap="RdYlGn")
cbar = plt.colorbar(contour, ax=ax, label=r"$P(N_{\rm total} > k \cdot n_{\rm obs})$")

# Mark the DA line (lambda = 1)
ax.axvline(1.0, color="black", lw=2.5, ls="--",
           label=r"Carter's DA ($\lambda = 1$)")

# Mark the "doomsday boundary" k = 20
ax.axhline(20, color="white", lw=1.5, ls=":",
           label=r"$k = 20$ (DA: $P = 5\%$)")

# Annotate key regions
ax.annotate("DA overestimates\ndoom\n(optimistic)",
            xy=(0.3, 50), fontsize=10, color="darkgreen",
            ha="center", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

ax.annotate("DA underestimates\ndoom\n(pessimistic)",
            xy=(8.0, 50), fontsize=10, color="darkred",
            ha="center", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

ax.annotate(r"Carter's DA" + "\n" + r"$P(N>20n)=5\%$",
            xy=(1.0, 20), fontsize=9, color="black",
            ha="center", va="bottom",
            xytext=(1.8, 80),
            arrowprops=dict(arrowstyle="->", color="black"),
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.8))

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(0.1, 30)
ax.set_ylim(2, 1000)
ax.set_xlabel(r"Growth-potential rate $\lambda$" + "\n"
              r"($\lambda=1$: Carter's DA;  $\lambda<1$: optimistic;  $\lambda>1$: pessimistic)",
              fontsize=11)
ax.set_ylabel(r"Doomsday multiplier $k$" + "\n"
              r"($P(N_{\rm total} > k \cdot n_{\rm obs})$)",
              fontsize=11)
ax.set_title("Observation-Adjusted Doomsday Framework:\n"
             r"$P(N_{\rm total} > k \cdot n_{\rm obs}) = k^{-\lambda}$",
             fontsize=13)
ax.legend(loc="upper right", fontsize=10)
ax.grid(True, which="both", alpha=0.3)

plt.tight_layout()
plt.savefig("doomsday_fig1.png", dpi=200)
plt.show()

# =====================================================================
# 6. SCALING AUDIT (analog of SOM's d_max x10 => F x100)
# =====================================================================
print("\n=== Scaling audit ===")
print("k x10  =>  P(N>k*n) changes by factor 10^{-lambda}")
print("(For DA lambda=1: P drops by exactly 10x when k grows by 10x)\n")

for lam in [0.5, 1.0, 2.0]:
    p1 = gp_prob(10, lam)
    p2 = gp_prob(100, lam)
    ratio = p1 / p2
    print(f"lambda={lam:.1f}:  P(k=10)={p1:.4e}  P(k=100)={p2:.4e}  "
          f"ratio={ratio:.2f}  (expect 10^{lam:.1f}={10**lam:.2f})")

# =====================================================================
# 7. SOM STRUCTURAL PARALLEL (console summary)
# =====================================================================
print("\n=== SOM <-> Doomsday structural parallel ===")
print(f"{'SOM (Fermi)':<35} | {'Doomsday (this work)':<35}")
print("-" * 73)
print(f"{'N_ever (total civilizations)':<35} | {'N_total (total humans)':<35}")
print(f"{'kappa (observability multiplier)':<35} | {'f = W/N_total (window fraction)':<35}")
print(f"{'lambda = N_ever * kappa':<35} | {'g = r * T_remaining (growth pot.)':<35}")
print(f"{'F = lambda / ln(10)':<35} | {'A = lambda_gp * log10(k)':<35}")
print(f"{'P(D=0) = exp(-lambda)':<35} | {'P(N>k*n) = k^{-lambda_gp}':<35}")
print(f"{'kappa << 1 => silence default':<35} | {'f << 1 => doom not default':<35}")
print(f"{'1/kappa (tension inflation)':<35} | {'1/f (ATI inflation)':<35}")
print(f"{'d_max^2 scaling (quadratic)':<35} | {'k^{-lambda} scaling (power-law)':<35}")
print(f"{'p_survey linear scaling':<35} | {'lambda linear in ATI':<35}")

# =====================================================================
# 8. SELF-CORRECTION NOTE
# =====================================================================
print("\n=== Self-correction note ===")
print("The growth-potential rate lambda is an ILLUSTRATIVE PLACEHOLDER.")
print("Calibrated values require:")
print("  (1) Demographic trajectory models (UN, IIASA, Lancet)")
print("  (2) Independent estimates of the transparency window W")
print("  (3) Prior over civilization lifetime T_remaining")
print("The framework is unchanged by substituting calibrated values.")
print("The DA's lambda=1 is ONE POINT in parameter space, not a theorem.")