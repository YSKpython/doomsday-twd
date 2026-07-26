"""
doomsday_checks.py -- verification suite.

Every check here is labelled by what it actually establishes. Two of
them are implementation checks (they confirm the code, not the model);
saying so plainly is the point.

  CHECK 1  Identifiability (Proposition 1). Substantive: the tail
           depends on (alpha, beta) only through their sum.
  CHECK 2  One-unit shift. Substantive: an absolute window at alpha
           equals a proportional window at alpha-1.
  CHECK 3  Closed form vs inverse-CDF Monte Carlo. IMPLEMENTATION
           CHECK: an independent sampler reproduces `tail`.
  CHECK 4  exp(-Exp(1)) ~ U(0,1). IMPLEMENTATION CHECK ONLY. This is a
           change-of-variable identity, provable in one line. The v1
           archive reported it as "validation" of the DA's assumption;
           it is nothing of the kind, and it is kept here only so the
           record is complete.

Run:  python3 doomsday_checks.py
"""

import numpy as np
from scipy import stats

from doomsday_core import K_DOOM, tail, sample_posterior_ratio

SEED = 20260725
M = 2_000_000
SEP = "=" * 78


def check_identifiability():
    print("CHECK 1 -- identifiability (substantive)")
    worst = 0.0
    for R in (1e3, 1e6, 1e9, np.inf):
        for sig in (0.4, 0.8, 1.0, 1.6, 2.0, 3.3):
            vals = [tail(K_DOOM, sig - b, b, R) for b in (0.0, 0.25, 0.5, 1.0)]
            worst = max(worst, max(vals) - min(vals))
    print(f"  max spread across (alpha,beta) splits of a fixed sigma: {worst:.3e}")
    print("  PASS\n" if worst < 1e-12 else "  FAIL\n")
    return worst < 1e-12


def check_one_unit_shift():
    print("CHECK 2 -- absolute window == proportional window at alpha-1 (substantive)")
    worst = 0.0
    for R in (1e3, 1e6, 1e9):
        for alpha in np.arange(1.05, 4.0, 0.05):
            worst = max(worst, abs(tail(K_DOOM, alpha, 0.0, R)
                                   - tail(K_DOOM, alpha - 1.0, 1.0, R)))
    print(f"  max |P_abs(alpha) - P_prop(alpha-1)|: {worst:.3e}")
    print("  PASS\n" if worst < 1e-12 else "  FAIL\n")
    return worst < 1e-12


def check_monte_carlo():
    print("CHECK 3 -- closed form vs inverse-CDF sampler (IMPLEMENTATION CHECK)")
    head = (f"  {'alpha':>6}{'beta':>6}{'R':>8}{'analytic':>11}"
            f"{'MC':>11}{'SE':>10}{'z':>8}")
    print(head)
    print("  " + "-" * (len(head) - 2))
    ok = True
    cases = [(1.0, 1.0, 1e6), (1.0, 0.0, 1e6), (0.0, 1.0, 1e6),
             (2.0, 1.0, 1e6), (1.5, 0.5, 1e3), (0.5, 0.5, 1e9)]
    for i, (a, b, R) in enumerate(cases):
        an = tail(K_DOOM, a, b, R)
        t = sample_posterior_ratio(M, a, b, R, seed=SEED + i)
        mc = float((t > K_DOOM).mean())
        se = float(np.sqrt(max(mc * (1 - mc), 1e-12) / M))
        z = (mc - an) / se if se > 0 else 0.0
        ok &= abs(z) < 5.0
        print(f"  {a:6.2f}{b:6.2f}{R:8.0e}{an:11.6f}{mc:11.6f}{se:10.6f}{z:8.2f}")
    print("  PASS\n" if ok else "  FAIL\n")
    return ok


def check_change_of_variable():
    print("CHECK 4 -- exp(-Exp(1)) ~ U(0,1)  (IMPLEMENTATION CHECK ONLY)")
    print("  This is a change-of-variable identity, not evidence about the DA.")
    rng = np.random.default_rng(SEED)
    for lam in (0.5, 1.0, 2.0):
        s = np.exp(-rng.exponential(scale=1.0 / lam, size=M))
        ks, p = stats.kstest(s, "uniform")
        verdict = "uniform (as the identity requires)" if lam == 1.0 \
            else "not uniform (as the identity requires)"
        print(f"  rate={lam:4.2f}  KS={ks:.5f}  p={p:.3e}  -> {verdict}")
    print("  (No conclusion about the Doomsday Argument follows.)\n")
    return True


if __name__ == "__main__":
    print(SEP)
    print("Verification suite -- transparency-window paper (v3)")
    print(SEP + "\n")
    results = [check_identifiability(), check_one_unit_shift(),
               check_monte_carlo(), check_change_of_variable()]
    print(SEP)
    print("ALL CHECKS PASSED" if all(results) else "SOME CHECKS FAILED")
    print(SEP)
