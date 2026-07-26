import numpy as np
from scipy import stats

# =====================================================================
# DOOMSDAY ARGUMENT — FULL FORWARD SIMULATION  (corrected, v2)
# (Analog of fermi_forward_sim.py)
# =====================================================================
#
# HONESTY CONTRACT (read before trusting any number below):
#
# The demographic parameters below are ILLUSTRATIVE PLACEHOLDERS.
# Calibrated values require UN / IIASA / Lancet projections and
# historical demographic data (PRB).  The framework is unchanged
# by substituting calibrated values through the single W_BASELINE
# input block below.
#
# FIXES vs previous version (v1):
#
#   (1) S1 was mislabeled "DA-equivalent" but sampled r and T from
#       narrow lognormals (sigma=0.01), giving g = r*T ≈ 1.0
#       deterministically.  This is NOT Exponential(1); it gives
#       P(g > ln 20) ≈ 0 instead of the DA's 1/20 = 0.05.
#       FIX: Added S0 "DA-equivalent (g ~ Exp(1))" that samples g
#       directly from Exponential(rate=1).  Relabeled old S1 as
#       "Narrow exponential (g ≈ 1)".
#
#   (2) Added "exponential_direct" trajectory type for true
#       DA-equivalent sampling.
#
#   (3) Added MC-vs-analytic comparison and KS test against U(0,1)
#       for every scenario, so the validation is self-contained.
#
#   (4) Added s = exp(-g) distribution diagnostics (mean, median,
#       KS stat, KS p-value) for each scenario.
#
# CORE INSIGHT (structural parallel with the SOM):
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
#   It is a consequence of the implicit assumption  g ~ Exp(1).
#   Change the trajectory model, change the conclusion.
#
# =====================================================================

LN10     = np.log(10.0)
N_OBS    = 1.0e11          # ~100 billion humans have ever lived
K_DOOM   = 20              # "doomsday multiplier"
LN_K     = np.log(K_DOOM)  # ln(20) ≈ 2.996

# ----- Demographic transparency window -----
# The era when population counting is possible.
# For humanity: roughly 1800 CE to present (~226 years).
# During this era, ~10-15 billion humans have been born.
T_WINDOW_START = 1800      # CE
T_WINDOW_END   = 2026      # CE (present)
T_WINDOW_DUR   = T_WINDOW_END - T_WINDOW_START   # ~226 years

# Illustrative: humans born during the transparency window.
# [ILLUSTRATIVE PLACEHOLDER — substitute calibrated value here]
W_BASELINE = 1.2e10        # ~12 billion

# =====================================================================
# 1. ANALYTIC BASELINES
# =====================================================================

def da_prob(k):
    """Carter's DA: P(N > k*n) = 1/k."""
    return 1.0 / np.asarray(k, dtype=float)

def gp_prob(k, lam):
    """Growth-potential model: P(N > k*n) = k^{-lambda}."""
    return np.asarray(k, dtype=float) ** (-lam)

def gp_ati(k, lam):
    """ATI = lambda * log10(k)."""
    return lam * np.log10(np.asarray(k, dtype=float))

# =====================================================================
# 2. FORWARD MONTE CARLO  (all trajectory types)
# =====================================================================

def forward_mc_doomsday(traj_type, params, W, M=10_000_000, seed=20260725):
    """
    Full forward simulation for a given trajectory model.

    Trajectory types
    ----------------
    "exponential_direct" : g ~ Exponential(rate=lam)  [TRUE DA-equivalent]
    "exponential"        : g = r * T,  r ~ Lognormal, T ~ Lognormal
    "logistic"           : s = n_obs/N_total near inflection point
    "collapse"           : g ~ Exponential(small scale)  [near end]

    Returns dict with MC estimates, analytic comparison, KS test,
    window fraction, and ATI.
    """
    rng = np.random.default_rng(seed)

    # ---- Sample growth potential g and compute N_total ----
    if traj_type == "exponential_direct":
        # TRUE DA-equivalent: g ~ Exponential(rate = lam_rate)
        # For lam_rate = 1: P(g > ln k) = 1/k  (Carter's DA)
        (lam_rate,) = params
        g = rng.exponential(scale=1.0 / lam_rate, size=M)
        N_total = N_OBS * np.exp(g)

    elif traj_type == "exponential":
        # g = r * T_remaining, both lognormal
        r_mean, r_std, T_mean, T_std = params
        r     = rng.lognormal(mean=np.log(r_mean), sigma=r_std, size=M)
        T_rem = rng.lognormal(mean=np.log(T_mean), sigma=T_std, size=M)
        g = r * T_rem
        N_total = N_OBS * np.exp(g)

    elif traj_type == "logistic":
        # N_total = K (carrying capacity); s = n_obs/K near inflection
        K_mean, K_std = params
        K = rng.lognormal(mean=np.log(K_mean), sigma=K_std, size=M)
        N_total = K
        # s = n_obs / N_total; near inflection s ≈ 0.5
        s = 0.5 + 0.1 * rng.standard_normal(M)
        s = np.clip(s, 0.01, 0.99)
        g = -np.log(s)

    elif traj_type == "collapse":
        # Near end: small growth potential
        r_mean, r_std, tau_mean, tau_std = params
        g = rng.exponential(scale=0.1, size=M)
        N_total = N_OBS * np.exp(g)

    else:
        raise ValueError(f"Unknown trajectory type: {traj_type}")

    # ---- Survival fraction s = n_obs / N_total = exp(-g) ----
    s = np.exp(-g)

    # ---- P(N > K_DOOM * n_obs) = P(g > ln K_DOOM) ----
    passed     = g > LN_K
    p_doom_mc  = float(passed.mean())
    p_doom_se  = float(np.sqrt(p_doom_mc * (1.0 - p_doom_mc) / M))

    # ---- ATI ----
    ati_mc = -np.log10(p_doom_mc) if p_doom_mc > 0 else np.inf
    ati_da = np.log10(K_DOOM)

    # ---- Carter's DA prediction ----
    p_doom_da = 1.0 / K_DOOM

    # ---- KS test: is s ~ Uniform(0,1)? ----
    ks_stat, ks_pval = stats.kstest(s, 'uniform')

    # ---- Window fraction f = W / N_total ----
    f = np.clip(W / N_total, 1e-15, 1.0)

    return {
        "p_doom_mc"    : p_doom_mc,
        "p_doom_se"    : p_doom_se,
        "p_doom_da"    : p_doom_da,
        "ratio"        : p_doom_mc / p_doom_da if p_doom_da > 0 else 0.0,
        "ati_mc"       : ati_mc,
        "ati_da"       : ati_da,
        "f_mean"       : float(f.mean()),
        "f_median"     : float(np.median(f)),
        "N_total_mean" : float(N_total.mean()),
        "N_total_med"  : float(np.median(N_total)),
        "g_mean"       : float(g.mean()),
        "g_median"     : float(np.median(g)),
        "s_mean"       : float(s.mean()),
        "s_median"     : float(np.median(s)),
        "ks_stat"      : float(ks_stat),
        "ks_pval"      : float(ks_pval),
        "uniform"      : "YES" if ks_pval > 0.01 else "NO",
    }

# =====================================================================
# 3. MAIN
# =====================================================================

if __name__ == "__main__":

    print("=" * 86)
    print("DOOMSDAY ARGUMENT — Full Forward Simulation  (corrected, v2)")
    print("(Analog of fermi_forward_sim.py)")
    print("=" * 86)

    print(f"\nTransparency window : {T_WINDOW_START}–{T_WINDOW_END} "
          f"({T_WINDOW_DUR} years)")
    print(f"W (humans in window): {W_BASELINE:.2e}  "
          f"[ILLUSTRATIVE PLACEHOLDER]")
    print(f"n_obs               : {N_OBS:.2e}")
    print(f"K_DOOM              : {K_DOOM}")
    print(f"ln(K_DOOM)          : {LN_K:.4f}")

    # -----------------------------------------------------------------
    # Scenario table  (CORRECTED: S0 = true DA-equivalent)
    # -----------------------------------------------------------------
    scenarios = [
        # TRUE DA-equivalent: g ~ Exp(1) directly
        ("S0: DA-equivalent (g~Exp(1))",
         "exponential_direct", (1.0,)),

        # Old S1, correctly relabeled
        ("S1: Narrow exponential (g≈1)",
         "exponential", (1.0, 0.01, 1.0, 0.01)),

        ("S2: Optimistic (high growth)",
         "exponential", (2.0, 0.3, 3.0, 0.3)),

        ("S3: Pessimistic (low growth)",
         "exponential", (0.3, 0.3, 0.5, 0.3)),

        ("S4: Logistic (near inflection)",
         "logistic", (1e12, 0.3)),

        ("S5: Collapse (near end)",
         "collapse", (0.5, 0.3, 100.0, 0.3)),
    ]

    header = (f"{'scenario':<38} {'P(N>20n)_MC':>12} {'P(N>20n)_DA':>12} "
              f"{'ratio':>7} {'ATI_MC':>8} {'ATI_DA':>8} "
              f"{'KS_stat':>9} {'KS_pval':>10} {'U(0,1)?':>8} "
              f"{'f_median':>10} {'N_tot_med':>12}")
    print(f"\n{header}")
    print("-" * len(header))

    results = []
    for i, (name, ttype, params) in enumerate(scenarios):
        res = forward_mc_doomsday(ttype, params, W_BASELINE,
                                   M=10_000_000, seed=7000 + i)
        results.append((name, res))
        print(f"{name:<38} {res['p_doom_mc']:12.6f} {res['p_doom_da']:12.6f} "
              f"{res['ratio']:7.2f} {res['ati_mc']:8.3f} {res['ati_da']:8.3f} "
              f"{res['ks_stat']:9.6f} {res['ks_pval']:10.4e} {res['uniform']:>8} "
              f"{res['f_median']:10.2e} {res['N_total_med']:12.2e}")

    # -----------------------------------------------------------------
    # MC vs analytic comparison  (like fermi_forward_sim Table 2)
    # -----------------------------------------------------------------
    print("\n--- MC vs Analytic comparison (DA-equivalent, S0) ---")
    print("(Analog of fermi_forward_sim.py Table 2: factorized vs extended vs MC)\n")

    res0 = results[0][1]
    p_analytic = da_prob(K_DOOM)   # 1/20 = 0.05
    p_mc       = res0["p_doom_mc"]
    rel_err    = (p_mc - p_analytic) / p_analytic * 100.0

    print(f"  P(N>20n) analytic (Carter DA) : {p_analytic:.6f}")
    print(f"  P(N>20n) MC (g~Exp(1))       : {p_mc:.6f}  "
          f"(SE = {res0['p_doom_se']:.6f})")
    print(f"  Relative error               : {rel_err:+.2f}%")
    print(f"  KS stat (s vs U(0,1))        : {res0['ks_stat']:.6f}")
    print(f"  KS p-value                   : {res0['ks_pval']:.4e}")
    print(f"  U(0,1) rejected?             : {res0['uniform']}")
    print(f"  s = exp(-g) mean             : {res0['s_mean']:.6f}  "
          f"(expect 0.5 for U(0,1))")
    print(f"  s = exp(-g) median           : {res0['s_median']:.6f}  "
          f"(expect 0.5 for U(0,1))")
    print(f"  g mean                       : {res0['g_mean']:.6f}  "
          f"(expect 1.0 for Exp(1))")
    print(f"  g median                     : {res0['g_median']:.6f}  "
          f"(expect ln2 ≈ 0.693 for Exp(1))")

    # -----------------------------------------------------------------
    # Error decomposition  (like fermi_forward_sim +10.3%)
    # -----------------------------------------------------------------
    print("\n--- Error decomposition: why S1 ≠ S0 ---")
    print("(Analog of fermi_forward_sim +10.3% = +13.3pp luminosity - 3.0pp slab)\n")

    res1 = results[1][1]
    print(f"  S0 (g~Exp(1)):     P(N>20n) = {res0['p_doom_mc']:.6f}  "
          f"g_mean = {res0['g_mean']:.4f}  g_median = {res0['g_median']:.4f}")
    print(f"  S1 (g≈1 narrow):   P(N>20n) = {res1['p_doom_mc']:.6f}  "
          f"g_mean = {res1['g_mean']:.4f}  g_median = {res1['g_median']:.4f}")
    print(f"  Difference: S1 uses Lognormal(ln1, 0.01) x Lognormal(ln1, 0.01)")
    print(f"  => g ≈ 1.0 (narrow), NOT Exp(1) (wide, mean=1, P(g>3)=5%)")
    print(f"  => P(g > ln20 ≈ 3.0) ≈ 0 for S1, but = 0.05 for S0")
    print(f"  This is why S1 was relabeled from 'DA-equivalent' to "
          f"'Narrow exponential'.")

    # -----------------------------------------------------------------
    # LaTeX table output
    # -----------------------------------------------------------------
    print("\n% --- paste into Table 3 (paper) ---")
    for name, res in results:
        ati_str = f"{res['ati_mc']:.3f}" if np.isfinite(res['ati_mc']) else r"\infty"
        print(f"{name} & ${res['p_doom_mc']:.4f}$ & ${res['p_doom_da']:.4f}$ & "
              f"${res['ratio']:.2f}$ & ${ati_str}$ & "
              f"${res['f_median']:.2e}$ \\\\")

    # -----------------------------------------------------------------
    # Window fraction audit  (analog of kappa in SOM)
    # -----------------------------------------------------------------
    print("\n=== Window fraction audit ===")
    print("f = W / N_total  (analog of kappa in SOM)\n")

    print(f"{'N_total':>12} {'f = W/N':>12} {'1/f':>12} "
          f"{'ATI_corr':>12} {'interpretation':<30}")
    print("-" * 80)
    for N_tot in [1e11, 1e12, 1e13, 1e14, 1e15]:
        f = W_BASELINE / N_tot
        inflation = 1.0 / f
        ati_corr = np.log10(inflation)
        if f >= 0.1:
            interp = "DA approximately holds"
        elif f >= 0.01:
            interp = "moderate correction"
        else:
            interp = "DA dissolved"
        print(f"{N_tot:12.0e} {f:12.2e} {inflation:12.2e} "
              f"{ati_corr:12.3f} {interp:<30}")

    # -----------------------------------------------------------------
    # Scaling audit  (analog of d_max x10 => F x100 in SOM)
    # -----------------------------------------------------------------
    print("\n=== Scaling audit ===")
    print("W x10  =>  f x10  =>  inflation /10  =>  ATI correction -1.0")
    print("(Analog of d_max x10 => p_space x100 => F x100 in SOM)\n")

    for W in [1e9, 1e10, 1e11, 1e12]:
        f = W / 1e12   # N_total = 1 trillion
        print(f"W={W:.0e}  f={f:.2e}  1/f={1/f:.2e}  "
              f"ATI_corr={np.log10(1/f):.3f}")

    print("\nk x10  =>  P(N>k*n) changes by factor 10^{-lambda_gp}")
    print("(For DA lambda=1: P drops by exactly 10x when k grows by 10x)\n")

    for lam in [0.5, 1.0, 2.0]:
        p10  = gp_prob(10, lam)
        p100 = gp_prob(100, lam)
        ratio = p10 / p100
        print(f"lambda={lam:.1f}:  P(k=10)={p10:.4e}  P(k=100)={p100:.4e}  "
              f"ratio={ratio:.2f}  (expect 10^{lam:.1f}={10**lam:.2f})")

    # -----------------------------------------------------------------
    # SOM structural parallel
    # -----------------------------------------------------------------
    print("\n=== SOM <-> Doomsday forward-sim structural parallel ===")
    print(f"{'fermi_forward_sim.py':<40} | {'doomsday_forward_sim.py':<40}")
    print("-" * 83)
    print(f"{'lambda_factorized (thin-disk, fixed ell)':<40} | "
          f"{'P(N>k*n) = k^{{-lambda}} (DA)':<40}")
    print(f"{'lambda_extended (slab, lognormal ell)':<40} | "
          f"{'P(N>k*n) trajectory-dependent':<40}")
    print(f"{'forward_mc (spatial + luminosity MC)':<40} | "
          f"{'forward_mc (growth potential MC)':<40}")
    print(f"{'+10.3% = +13.3pp lum - 3.0pp slab':<40} | "
          f"{'S1 vs S0: narrow lognormal != Exp(1)':<40}")
    print(f"{'p_space = (d_max/R_G)^2':<40} | "
          f"{'f = W / N_total':<40}")
    print(f"{'F = lambda / ln(10)':<40} | "
          f"{'A = lambda_gp * log10(k)':<40}")
    print(f"{'d_max x10 => F x100 (quadratic)':<40} | "
          f"{'k x10 => P x 10^{{-lambda}} (power)':<40}")
    print(f"{'p_survey x10 => F x10 (linear)':<40} | "
          f"{'f x10 => ATI_corr +1.0 (linear)':<40}")

    # -----------------------------------------------------------------
    # Self-correction note
    # -----------------------------------------------------------------
    print("\n=== Self-correction note ===")
    print(f"W = {W_BASELINE:.2e} is an ILLUSTRATIVE PLACEHOLDER.")
    print("Calibrated W requires:")
    print("  (1) Historical demographic data (PRB, UN)")
    print("  (2) Definition of 'transparency window' boundaries")
    print("      (when did population counting begin? when might it end?)")
    print("  (3) Projection of window duration into the future")
    print("The framework is unchanged by substituting calibrated W.")
    print()
    print("S0 (g~Exp(1)) validates Carter's DA: P(N>20n) ≈ 0.05, KS p > 0.01.")
    print("S1 (narrow lognormal) is NOT DA-equivalent: P(N>20n) ≈ 0, KS p < 0.01.")
    print("The DA's U(0,1) assumption requires the SPECIFIC distribution Exp(1),")
    print("not merely g_mean = 1. This is the key finding.")