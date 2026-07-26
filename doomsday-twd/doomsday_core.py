"""
doomsday_core.py -- shared math for
"The Transparency-Window Dilemma: Why the Doomsday Argument Cannot
Settle Its Own Reference Class" (v3).

MODEL (paper Sec. 2)
--------------------
    prior      pi(N)          ~  N^-alpha         on [n_obs, R*n_obs]
    likelihood P(n | N, O)    ~  N^-beta          (window W ~ N^beta)
    posterior                 ~  N^-(alpha+beta)  on [n_obs, R*n_obs]

Everything below depends on (alpha, beta) ONLY through sigma = alpha+beta.
That is the identifiability result of Proposition 1, and it is checked
numerically in doomsday_checks.py.

    beta = 1  ->  window scales with N   ->  DA preserved
    beta = 0  ->  absolute window        ->  no DA update (Neal FNC)

NOT IN THIS CODEBASE, DELIBERATELY
----------------------------------
  * the Anthropic Tension Index A = alpha*log10(k). Dropped in v3: it is
    base-10 surprisal under another name, and the paper does not use it.
  * the window fraction f = W/N_total and the additive correction
    A_corr = A + log10(f). Retracted -- it was never derived and it
    implies P > 1.
  * "growth potential" / lambda_gp language. alpha is a PRIOR exponent,
    an epistemic input, not a demographic parameter.
"""

import math
import numpy as np

# PRB, Haub & Kaneda 2022 revision: about 117 billion humans ever born.
N_OBS = 1.17e11
K_DOOM = 20


def tail(k, alpha, beta=1.0, R=np.inf):
    """P(N_total > k*n_obs | n_obs, O).

    k     : doomsday multiplier (scalar)
    alpha : prior exponent (scalar or array)
    beta  : window exponent; 1 = proportional, 0 = absolute
    R     : N_max / n_obs. np.inf gives the improper limit, which
            returns exactly 1 for sigma <= 1 -- that value is a LIMIT,
            not a probability. Prefer a finite R.

    Numerically stable: the branch with the large power is rescaled
    rather than evaluated directly.
    """
    k = float(k)
    if k <= 1.0:
        raise ValueError("k must exceed 1")
    scalar_in = np.isscalar(alpha)
    sig = np.atleast_1d(np.asarray(alpha, dtype=float)) + float(beta)
    out = np.empty(sig.shape, dtype=float)

    if math.isinf(R):
        big = sig > 1.0
        out[big] = k ** (1.0 - sig[big])
        out[~big] = 1.0
    else:
        if R <= k:
            raise ValueError("R must exceed k for the tail to be defined")
        lnR, lnk = math.log(R), math.log(k)
        near1 = np.abs(sig - 1.0) < 1e-12
        out[near1] = (lnR - lnk) / lnR

        a = 1.0 - sig[~near1]
        res = np.empty(a.shape, dtype=float)
        neg = a < 0.0                       # sigma > 1: R^a is tiny
        res[neg] = (np.exp(a[neg] * lnk) - np.exp(a[neg] * lnR)) \
                   / (1.0 - np.exp(a[neg] * lnR))
        pos = ~neg                          # sigma < 1: rescale by R^a
        res[pos] = (np.exp(a[pos] * (lnk - lnR)) - 1.0) \
                   / (np.exp(-a[pos] * lnR) - 1.0)
        out[~near1] = res

    out = np.clip(out, 0.0, 1.0)
    return float(out[0]) if scalar_in else out


def posterior_median_ratio(alpha, beta=1.0, R=np.inf):
    """Median of N_total / n_obs under the posterior.

    Large-R limit, sigma > 1:  2^(1/(sigma-1)).
    Carter (sigma = 2) gives 2, i.e. the median total is 2*n_obs.
    """
    sig = float(alpha) + float(beta)
    if math.isinf(R):
        if sig <= 1.0:
            return math.inf
        return 2.0 ** (1.0 / (sig - 1.0))
    if abs(sig - 1.0) < 1e-12:
        return R ** 0.5
    a = 1.0 - sig
    return (0.5 * (1.0 + R ** a)) ** (1.0 / a)


def sample_posterior_ratio(n, alpha, beta=1.0, R=1e6, seed=0):
    """Draw N_total/n_obs from the posterior by inverse CDF.

    Used by doomsday_checks.py to verify the closed form in `tail`
    against an independent computation.
    """
    sig = float(alpha) + float(beta)
    u = np.random.default_rng(seed).random(n)
    if abs(sig - 1.0) < 1e-12:
        return R ** u
    a = 1.0 - sig
    return (1.0 + u * (R ** a - 1.0)) ** (1.0 / a)


POSITIONS = [
    # label                              alpha  beta
    ("Carter / Leslie / Gott",            1.0,  1.0),
    ("SIA from Jeffreys",                 0.0,  1.0),
    ("Absolute window (Neal FNC here)",   1.0,  0.0),
    ("SIA and absolute window together",  0.0,  0.0),
    ("Pessimistic prior, full class",     2.0,  1.0),
]

R_GRID = [1e3, 1e6, 1e9]
