import numpy as np

# =====================================================================
# DOOMSDAY ARGUMENT — Structure-anchored ATI
# (Analog of fermi_empirical_F.py)
# =====================================================================
#
# HONESTY CONTRACT:
# The window-fraction values produced here are ILLUSTRATIVE
# PLACEHOLDERS, built from representative demographic parameters.
# They are NOT read off a published table. A calibrated value
# (from UN/IIASA/Lancet projections) can be substituted by editing
# the WF_OPT / WF_PESS input block below; the framework (and
# Table 7 of the paper) is unchanged by that substitution.
#
# IMPORTANT (per the paper's structural allocation):
# The window fraction f = W / N_total is the DEMOGRAPHIC analog
# of the SOM's kappa. It encodes the observation filter:
#   f = p_window * p_demo * p_cult * p_tech
# where:
#   p_window = fraction of population in the transparency era
#   p_demo   = probability of having demographic tools
#   p_cult   = probability of cultural motivation to count
#   p_tech   = probability of individual access to the count
#
# The growth-potential rate lambda_gp is a TRAJECTORY property,
# NOT a reference-class property. It is EXCLUDED from the
# window-fraction product (analog of p_sync exclusion in SOM).
#
# =====================================================================

LN10 = np.log(10.0)
N_OBS = 1.0e11
K_DOOM = 20

# =====================================================================
# 1. WINDOW-FRACTION STRUCTURE (analog of Wright et al. haystack)
# =====================================================================

def window_fraction(p_window, p_demo, p_cult, p_tech):
    """Four-factor window fraction (analog of survey_coverage in SOM).
    Growth potential is deliberately excluded (it's a trajectory
    property, not an observation-filter property)."""
    return float(p_window) * float(p_demo) * float(p_cult) * float(p_tech)

# Two representative factor sets -> bracket the plausible f.
# (Growth potential excluded: it lives in the trajectory, not the filter.)
WF_OPT  = dict(p_window=0.10, p_demo=0.8, p_cult=0.5, p_tech=0.5)   # -> 0.02
WF_PESS = dict(p_window=0.01, p_demo=0.3, p_cult=0.3, p_tech=0.3)   # -> 2.7e-4

f_opt  = window_fraction(**WF_OPT)
f_pess = window_fraction(**WF_PESS)

# =====================================================================
# 2. ATI COMPUTATION
# =====================================================================

def doomsday_ati(k, lam_gp):
    """ATI = lambda_gp * log10(k)."""
    return lam_gp * np.log10(float(k))

def doomsday_ati_corrected(k, lam_gp, f):
    """
    Corrected ATI accounting for window fraction.
    
    The DA's ATI is inflated by 1/f relative to the corrected value.
    ATI_corrected = ATI_DA - log10(1/f) = ATI_DA + log10(f)
    
    (Analog of F = lambda/ln(10) in SOM, where lambda includes kappa.)
    """
    ati_da = lam_gp * np.log10(float(k))
    correction = np.log10(f)  # negative since f < 1
    return ati_da + correction

def doomsday_prob(k, lam_gp):
    """P(N > k*n) = k^{-lambda_gp}."""
    return float(k) ** (-lam_gp)

# =====================================================================
# 3. TABLE 7: ATI across scenarios x window fractions
# =====================================================================

scenarios = [
    ("S1: DA-equivalent (lambda=1)",          1.0),
    ("S2: Optimistic (lambda=0.5)",           0.5),
    ("S3: Pessimistic (lambda=2)",            2.0),
    ("S4: High growth potential (lambda=0.25)", 0.25),
]

grid = [1.0, 1e-1, 1e-2, 1e-3, 1e-4]

print("=" * 78)
print("DOOMSDAY ARGUMENT — Structure-anchored ATI")
print("(Analog of fermi_empirical_F.py)")
print("=" * 78)

print(f"\nStructure-consistent bracket:  f_opt = {f_opt:.2e}   "
      f"f_pess = {f_pess:.2e}\n")

# ----- Table 7: ATI -----
header = (f"{'scenario':<42} |  " +
          "  ".join(f"{'f='+f'{p:.0e}':>10}" for p in grid) +
          f" | {'f_opt':>10} {'f_pess':>10}")
print("--- Table 7: ATI = lambda_gp * log10(k) + log10(f)  (k=20) ---\n")
print(header)
print("-" * len(header))

for name, lam in scenarios:
    row = f"{name:<42} |  "
    for f in grid:
        A = doomsday_ati_corrected(K_DOOM, lam, f)
        row += f"{A:10.3f}  "
    Ao = doomsday_ati_corrected(K_DOOM, lam, f_opt)
    Ap = doomsday_ati_corrected(K_DOOM, lam, f_pess)
    row += f"| {Ao:10.3f} {Ap:10.3f}"
    print(row)

# ----- Table 7b: P(N > 20n) -----
print(f"\n--- Table 7b: P(N > 20*n_obs) = 20^(-lambda_gp) ---\n")
header2 = f"{'scenario':<42} | {'P(N>20n)':>12} {'DA P=5%':>12} {'ratio':>8}"
print(header2)
print("-" * len(header2))

for name, lam in scenarios:
    p = doomsday_prob(K_DOOM, lam)
    p_da = 1.0 / K_DOOM
    ratio = p / p_da
    print(f"{name:<42} | {p:12.6f} {p_da:12.6f} {ratio:8.2f}")

# =====================================================================
# 4. SCALING AUDIT
# =====================================================================

print("\n=== Scaling audit ===")
print("k x10  =>  ATI changes by lambda_gp")
print("(For DA lambda=1: ATI increases by exactly 1.0 when k grows by 10x)")
print("(Analog of d_max x10 => F x100 in SOM)\n")

for lam in [0.5, 1.0, 2.0]:
    A10 = doomsday_ati(10, lam)
    A100 = doomsday_ati(100, lam)
    delta = A100 - A10
    print(f"lambda={lam:.1f}:  ATI(k=10)={A10:.3f}  ATI(k=100)={A100:.3f}  "
          f"delta={delta:.3f}  (expect {lam:.1f})")

print("\n=== Window-fraction scaling ===")
print("f x10  =>  ATI_corrected changes by +1.0")
print("(Analog of p_survey x10 => F x10 in SOM)\n")

for f in [1.0, 1e-1, 1e-2, 1e-3, 1e-4]:
    A = doomsday_ati_corrected(K_DOOM, 1.0, f)
    print(f"f={f:.0e}  ATI_corrected={A:.3f}  "
          f"(DA ATI={doomsday_ati(K_DOOM, 1.0):.3f}, "
          f"correction={np.log10(f):.3f})")

# =====================================================================
# 5. WRIGHT-ANALOG COMPARISON
# =====================================================================

print("\n=== Window-fraction sub-product (no growth potential) ===")
print("Per the structural allocation, lambda_gp is a trajectory property,")
print("not an observation-filter property, so it is excluded from the")
print("window-fraction product (analog of p_sync exclusion in SOM).\n")

prod_filter = f_pess  # window fraction at pessimistic coverage
print(f"Four-factor window fraction (pessimistic) = {prod_filter:.2e}")
print(f"Inflation factor 1/f = {1.0/prod_filter:.2e}")
print(f"ATI correction = log10(1/f) = {np.log10(1.0/prod_filter):.3f}")
print(f"\nInterpretation: the DA's ATI is inflated by {1.0/prod_filter:.0e}x")
print(f"relative to the corrected value. This is the exact analog of")
print(f"the SOM's 1/kappa inflation.")

# =====================================================================
# 6. SELF-CORRECTION
# =====================================================================

print("\n=== Self-correction note ===")
print(f"Old f plausible range upper bound : 1.0 (DA assumption)")
print(f"Structure-consistent optimistic f : {f_opt:.2e}")
print(f"Structure-consistent pessimistic f: {f_pess:.2e}")
print("=> values above ~0.1 require an implausibly large transparency")
print("   window; revise upper bound 1.0 -> 0.1.")
print("(Analog of SOM's p_survey revision: 0.1 -> 1e-2.)")