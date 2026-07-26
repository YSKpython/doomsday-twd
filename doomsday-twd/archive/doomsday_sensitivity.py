import numpy as np
import matplotlib.pyplot as plt

# =====================================================================
# DOOMSDAY ARGUMENT — Sensitivity / robustness analysis (figure 2)
# (Analog of fermi_sensitivity.py)
# =====================================================================
#
# LEFT panel:  P(N > 20*n_obs) vs lambda_gp (growth-potential rate)
#              for different k values.
#              Shows: DA's 5% prediction is lambda-dependent.
#
# RIGHT panel: P(N > 20*n_obs) vs W (window size)
#              for different N_total values.
#              Shows: window fraction f = W/N_total governs the correction.
#
# =====================================================================

LN10 = np.log(10.0)
N_OBS = 1.0e11
K_DOOM = 20

# ----- Analytic functions -----
def gp_prob(k, lam):
    return np.asarray(k, dtype=float) ** (-lam)

def window_prob(k, W, N_total):
    """
    Corrected P(N > k*n_obs) accounting for window fraction.
    
    If W >= k * n_obs: no constraint (P ≈ 1)
    If W < n_obs: impossible
    If n_obs <= W < k * n_obs: P = W / (k * n_obs)
    
    This is a simplified model; the full treatment uses the
    growth-potential distribution.
    """
    W = np.asarray(W, dtype=float)
    threshold = k * N_OBS
    return np.where(W >= threshold, 1.0,
           np.where(W < N_OBS, 0.0, W / threshold))

# =====================================================================
# FIGURE 2
# =====================================================================

fig, axes = plt.subplots(1, 2, figsize=(15, 6.2))

# ---- LEFT panel: lambda sensitivity ----
ax = axes[0]
lam_plot = np.linspace(0.05, 5.0, 500)
k_values = [5, 10, 20, 50, 100]
colors = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e"]

for k, col in zip(k_values, colors):
    P = gp_prob(k, lam_plot)
    ax.plot(lam_plot, P, color=col, lw=2.0,
            label=rf"$k={k}$")

# Mark the DA line (lambda = 1)
ax.axvline(1.0, color="black", lw=2.0, ls="--",
           label=r"Carter's DA ($\lambda=1$)")

# Mark the 5% level
ax.axhline(0.05, color="gray", lw=1.0, ls=":",
           label=r"$P = 5\%$ (DA at $k=20$)")

ax.set_xlim(0.05, 5.0)
ax.set_ylim(0, 1.05)
ax.set_xlabel(r"Growth-potential rate $\lambda_{\rm gp}$", fontsize=12)
ax.set_ylabel(r"$P(N_{\rm total} > k \cdot n_{\rm obs})$", fontsize=12)
ax.set_title(r"Sensitivity: growth-potential rate $\lambda_{\rm gp}$" + "\n"
             r"($P = k^{-\lambda}$; DA holds only at $\lambda=1$)",
             fontsize=11)
ax.legend(fontsize=9, loc="upper right")
ax.grid(True, alpha=0.3)

# ---- RIGHT panel: window size sensitivity ----
ax = axes[1]
W_plot = np.logspace(8, 14, 500)  # W from 1e8 to 1e14
N_total_values = [1e11, 1e12, 1e13, 1e14]
colors2 = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a"]

for N_tot, col in zip(N_total_values, colors2):
    P = window_prob(K_DOOM, W_plot, N_tot)
    ax.plot(W_plot, P, color=col, lw=2.0,
            label=rf"$N_{{\rm total}}={N_tot:.0e}$")

# Mark the baseline W
ax.axvline(1.2e10, color="black", lw=2.0, ls="--",
           label=r"$W = 1.2 \times 10^{10}$ (baseline)")

# Mark the DA regime (W = N_total)
ax.axhline(0.05, color="gray", lw=1.0, ls=":",
           label=r"$P = 5\%$ (DA prediction)")

ax.set_xscale("log")
ax.set_xlim(1e8, 1e14)
ax.set_ylim(0, 1.05)
ax.set_xlabel(r"Window size $W$ (humans in transparency era)", fontsize=12)
ax.set_ylabel(r"$P(N_{\rm total} > 20 \cdot n_{\rm obs})$", fontsize=12)
ax.set_title(r"Sensitivity: transparency window $W$" + "\n"
             r"(DA holds only when $W \geq N_{\rm total}$)",
             fontsize=11)
ax.legend(fontsize=9, loc="center right")
ax.grid(True, which="both", alpha=0.3)

plt.suptitle("Doomsday Argument Robustness: "
             "How does the 'doomsday probability' depend on the parameters?",
             fontsize=12, y=1.02)
plt.tight_layout()
plt.savefig("doomsday_fig2.png", dpi=200, bbox_inches="tight")
plt.show()

# ----- Console summary -----
print("\n=== lambda_gp sensitivity (k=20 fixed) ===")
print("lambda_gp   P(N>20n)   DA prediction   ratio")
for lam in [0.25, 0.50, 1.00, 2.00, 4.00]:
    p = gp_prob(20, lam)
    p_da = 1.0 / 20
    print(f"{lam:8.2f}   {p:10.6f}   {p_da:10.6f}      {p/p_da:8.2f}")

print("\n=== W sensitivity (N_total=1e12, k=20 fixed) ===")
print("W           f=W/N     P(N>20n)   interpretation")
for W in [1e8, 1e9, 1e10, 1e11, 1e12, 1e13]:
    f = W / 1e12
    p = window_prob(20, W, 1e12)
    if f >= 1.0:
        interp = "DA holds"
    elif f >= 0.05:
        interp = "partial correction"
    else:
        interp = "DA dissolved"
    print(f"{W:.0e}   {f:.2e}   {p:10.6f}   {interp}")