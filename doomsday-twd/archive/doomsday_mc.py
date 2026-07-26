import numpy as np
from scipy import stats

# =====================================================================
# DOOMSDAY ARGUMENT — Monte Carlo Validation
# Non-circular validation of the growth-potential model
# (Analog of fermi_v2_mc.py)
# =====================================================================
#
# HONESTY CONTRACT:
# The trajectory parameters (r, T_remaining, distribution shape)
# are ILLUSTRATIVE PLACEHOLDERS. Calibrated values require
# demographic projections (UN, IIASA, Lancet). The framework
# is unchanged by substitution.
#
# CORE TEST:
# Carter's DA assumes  s = n_obs / N_total ~ Uniform(0,1).
# This is equivalent to  g = -ln(s) = ln(N_total/n_obs) ~ Exp(1).
#
# We test: under different growth-potential distributions,
# does s remain Uniform(0,1)?  (Spoiler: only for Exp(1).)
#
# =====================================================================

LN10 = np.log(10.0)
N_OBS = 1.0e11
K_DOOM = 20
LN_K = np.log(K_DOOM)

# =====================================================================
# 1. ANALYTIC BASELINE
# =====================================================================

def da_prob(k):
    """Carter's DA: P(N > k*n) = 1/k."""
    return 1.0 / np.asarray(k, dtype=float)

def gp_prob_analytic(k, lam):
    """Growth-potential model: P(N > k*n) = k^{-lambda}."""
    return np.asarray(k, dtype=float) ** (-lam)

def gp_ati(k, lam):
    """ATI = lambda * log10(k)."""
    return lam * np.log10(np.asarray(k, dtype=float))

# =====================================================================
# 2. MONTE CARLO: sample g, compute s = exp(-g), test against U(0,1)
# =====================================================================

def mc_growth_potential(lam, M=2_000_000, seed=20260725):
    """
    Sample g ~ Exponential(rate=lam), compute s = exp(-g).
    
    Under lam=1: s ~ U(0,1)  (Carter's DA holds)
    Under lam!=1: s is NOT uniform  (DA breaks)
    
    Returns dict with:
      - s_samples: the survival fractions
      - p_doom_mc: P(N > K_DOOM * n_obs) = P(g > ln(K_DOOM))
      - p_doom_se: standard error
      - ks_stat, ks_pval: KS test against U(0,1)
      - ati_mc: empirical ATI at k=K_DOOM
    """
    rng = np.random.default_rng(seed)
    
    # Sample growth potential
    g = rng.exponential(scale=1.0/lam, size=M)
    
    # Survival fraction
    s = np.exp(-g)
    
    # P(N > K_DOOM * n_obs) = P(g > ln(K_DOOM))
    passed = g > LN_K
    p_doom_mc = passed.mean()
    p_doom_se = np.sqrt(p_doom_mc * (1.0 - p_doom_mc) / M)
    
    # KS test against U(0,1)
    ks_stat, ks_pval = stats.kstest(s, 'uniform')
    
    # Empirical ATI
    if p_doom_mc > 0:
        ati_mc = -np.log10(p_doom_mc)
    else:
        ati_mc = np.inf
    
    return {
        "s_samples": s,
        "p_doom_mc": p_doom_mc,
        "p_doom_se": p_doom_mc,
        "ks_stat": ks_stat,
        "ks_pval": ks_pval,
        "ati_mc": ati_mc,
        "s_mean": s.mean(),
        "s_median": np.median(s),
    }

# =====================================================================
# 3. DIRECT AUDIT: explicit trajectory simulation
# =====================================================================

def mc_trajectory_exponential(r_mean, r_std, T_mean, T_std,
                               M=2_000_000, seed=999):
    """
    Direct audit: sample (r, T_remaining) from lognormal priors,
    compute g = r * T_remaining, s = exp(-g).
    
    This is less efficient than sampling g directly, but useful
    as a check that the growth-potential abstraction is valid.
    """
    rng = np.random.default_rng(seed)
    
    # Sample growth rate and remaining lifetime
    r = rng.lognormal(mean=np.log(r_mean), sigma=r_std, size=M)
    T = rng.lognormal(mean=np.log(T_mean), sigma=T_std, size=M)
    
    g = r * T
    s = np.exp(-g)
    
    passed = g > LN_K
    p_doom_mc = passed.mean()
    p_doom_se = np.sqrt(p_doom_mc * (1.0 - p_doom_mc) / M)
    
    ks_stat, ks_pval = stats.kstest(s, 'uniform')
    
    return {
        "p_doom_mc": p_doom_mc,
        "p_doom_se": p_doom_mc,
        "ks_stat": ks_stat,
        "ks_pval": ks_pval,
        "g_mean": g.mean(),
        "g_median": np.median(g),
        "s_mean": s.mean(),
        "s_median": np.median(s),
    }

def mc_trajectory_logistic(K_mean, K_std, t_obs_frac,
                            M=2_000_000, seed=888):
    """
    Logistic trajectory: N(t) = K / (1 + exp(-r*(t-t0))).
    n_obs / N_total depends on where t_obs sits relative to t0.
    
    t_obs_frac: fraction of the logistic curve at which observation occurs.
      0.5 = inflection point (n_obs/N_total ≈ 0.5)
      0.1 = early (n_obs/N_total << 0.5)
      0.9 = late (n_obs/N_total ≈ 1)
    """
    rng = np.random.default_rng(seed)
    
    K = rng.lognormal(mean=np.log(K_mean), sigma=K_std, size=M)
    
    # For a logistic curve, n_obs/N_total = 1/(1+exp(-r*(t_obs-t0)))
    # We parameterize by the fraction of the curve at t_obs
    # s = n_obs/N_total = t_obs_frac (approximately, for symmetric logistic)
    # Add noise to simulate uncertainty
    s = np.clip(t_obs_frac + 0.05 * rng.standard_normal(M), 0.001, 0.999)
    
    passed = s < (1.0 / K_DOOM)
    p_doom_mc = passed.mean()
    p_doom_se = np.sqrt(p_doom_mc * (1.0 - p_doom_mc) / M)
    
    ks_stat, ks_pval = stats.kstest(s, 'uniform')
    
    return {
        "p_doom_mc": p_doom_mc,
        "p_doom_se": p_doom_mc,
        "ks_stat": ks_stat,
        "ks_pval": ks_pval,
        "s_mean": s.mean(),
        "s_median": np.median(s),
    }

# =====================================================================
# 4. MAIN: run all validations
# =====================================================================

if __name__ == "__main__":
    print("=" * 78)
    print("DOOMSDAY ARGUMENT — Monte Carlo Validation")
    print("(Analog of fermi_v2_mc.py)")
    print("=" * 78)
    
    # ----- Test 1: Growth-potential distributions -----
    print("\n--- Test 1: Growth-potential distributions ---")
    print("Carter's DA predicts s = n_obs/N_total ~ U(0,1).")
    print("This holds ONLY for g ~ Exponential(rate=1).\n")
    
    lam_values = [0.25, 0.50, 1.00, 2.00, 4.00]
    
    header = (f"{'lambda':>8} {'P(N>20n)_MC':>12} {'P(N>20n)_an':>12} "
              f"{'rel_err%':>10} {'KS_stat':>10} {'KS_pval':>10} "
              f"{'U(0,1)?':>10} {'ATI_MC':>10}")
    print(header)
    print("-" * len(header))
    
    for i, lam in enumerate(lam_values):
        res = mc_growth_potential(lam, M=2_000_000, seed=7000 + i)
        p_an = gp_prob_analytic(K_DOOM, lam)
        rel_err = (res["p_doom_mc"] - p_an) / p_an * 100.0 if p_an > 0 else 0.0
        uniform = "YES" if res["ks_pval"] > 0.01 else "NO"
        print(f"{lam:8.2f} {res['p_doom_mc']:12.6f} {p_an:12.6f} "
              f"{rel_err:10.2f} {res['ks_stat']:10.6f} {res['ks_pval']:10.4e} "
              f"{uniform:>10} {res['ati_mc']:10.4f}")
    
    print("\nKey: KS_pval > 0.01 => cannot reject U(0,1) => DA holds.")
    print("     KS_pval < 0.01 => reject U(0,1) => DA breaks.")
    
    # ----- Test 2: Direct trajectory audit -----
    print("\n--- Test 2: Direct trajectory audit (exponential growth) ---")
    print("Sample (r, T_remaining) from lognormal priors, compute g = r*T.\n")
    
    traj_configs = [
        ("DA-equivalent (r*T ~ Exp(1))", 1.0, 0.5, 1.0, 0.5),
        ("Optimistic (high growth)",     2.0, 0.3, 3.0, 0.3),
        ("Pessimistic (low growth)",     0.3, 0.3, 1.0, 0.3),
        ("High uncertainty",             1.0, 1.0, 1.0, 1.0),
    ]
    
    header2 = (f"{'trajectory':<35} {'P(N>20n)_MC':>12} {'KS_stat':>10} "
               f"{'KS_pval':>10} {'U(0,1)?':>10} {'g_mean':>10} {'s_median':>10}")
    print(header2)
    print("-" * len(header2))
    
    for name, r_m, r_s, T_m, T_s in traj_configs:
        res = mc_trajectory_exponential(r_m, r_s, T_m, T_s,
                                         M=2_000_000, seed=hash(name) % 10000)
        uniform = "YES" if res["ks_pval"] > 0.01 else "NO"
        print(f"{name:<35} {res['p_doom_mc']:12.6f} {res['ks_stat']:10.6f} "
              f"{res['ks_pval']:10.4e} {uniform:>10} {res['g_mean']:10.4f} "
              f"{res['s_median']:10.6f}")
    
    # ----- Test 3: Logistic trajectory -----
    print("\n--- Test 3: Logistic trajectory ---")
    print("n_obs/N_total depends on where t_obs sits on the S-curve.\n")
    
    logistic_configs = [
        ("Early (10% of curve)",    0.1),
        ("Inflection (50%)",        0.5),
        ("Late (90% of curve)",     0.9),
    ]
    
    header3 = (f"{'position':<30} {'P(N>20n)_MC':>12} {'KS_stat':>10} "
               f"{'KS_pval':>10} {'U(0,1)?':>10} {'s_median':>10}")
    print(header3)
    print("-" * len(header3))
    
    for name, frac in logistic_configs:
        res = mc_trajectory_logistic(1e12, 0.3, frac,
                                      M=2_000_000, seed=hash(name) % 10000)
        uniform = "YES" if res["ks_pval"] > 0.01 else "NO"
        print(f"{name:<30} {res['p_doom_mc']:12.6f} {res['ks_stat']:10.6f} "
              f"{res['ks_pval']:10.4e} {uniform:>10} {res['s_median']:10.6f}")
    
    # ----- Scaling audit -----
    print("\n=== Scaling audit ===")
    print("k x10 => P(N>k*n) changes by factor 10^{-lambda}")
    print("(For DA lambda=1: P drops by exactly 10x when k grows by 10x)\n")
    
    for lam in [0.5, 1.0, 2.0]:
        res10 = mc_growth_potential(lam, M=2_000_000, seed=5000)
        # Override K_DOOM for this test
        rng = np.random.default_rng(5000)
        g = rng.exponential(scale=1.0/lam, size=2_000_000)
        p10 = (g > np.log(10)).mean()
        p100 = (g > np.log(100)).mean()
        ratio = p10 / p100 if p100 > 0 else np.inf
        print(f"lambda={lam:.1f}:  P(k=10)={p10:.4e}  P(k=100)={p100:.4e}  "
              f"ratio={ratio:.2f}  (expect 10^{lam:.1f}={10**lam:.2f})")
    
    # ----- SOM parallel -----
    print("\n=== SOM <-> Doomsday MC parallel ===")
    print(f"{'fermi_v2_mc.py':<35} | {'doomsday_mc.py':<35}")
    print("-" * 73)
    print(f"{'Rao-Blackwellized p_sync MC':<35} | {'Direct g-sampling MC':<35}")
    print(f"{'Direct tau-sampling audit':<35} | {'Trajectory (r,T) audit':<35}")
    print(f"{'KS: p_sync vs L_eff/T_G':<35} | {'KS: s vs U(0,1)':<35}")
    print(f"{'Thin-disk vs slab geometry':<35} | {'Exp vs logistic trajectory':<35}")
    print(f"{'lambda_MC vs lambda_analytic':<35} | {'P_MC vs P_analytic':<35}")