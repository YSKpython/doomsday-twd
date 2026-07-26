# Beyond Rank: An Observation-Adjusted Framework for the Doomsday Argument

**Yavuz Selim Kılınç** — Independent Researcher, Manisa, Türkiye

Companion paper to *Beyond N: A Synchronized Observability Model for the
Fermi Paradox* (Zenodo DOI: 10.5281/zenodo.21539849).

---

## Abstract

The Doomsday Argument (DA) infers, from one's observed birth rank among all
humans, that humanity is probably near its end. We show that the DA's central
assumption — that the survival fraction s = n_obs / N_total is uniformly
distributed on (0,1) — is not a consequence of Bayesian reasoning but a
specific distributional commitment: it is equivalent to assuming that the
growth potential g = ln(N_total / n_obs) follows an Exponential distribution
with rate λ_gp = 1. We present an observation-adjusted framework that replaces
this commitment with a one-parameter family P(N_total > k · n_obs) = k^{−λ_gp},
attaches a survey-comparable reporting transform — the Anthropic Tension Index
A = λ_gp · log₁₀(k) — and introduces a demographic transparency window of size
W whose fraction f = W / N_total plays the role of the observability multiplier
κ in the companion Synchronized Observability Model (SOM) for the Fermi paradox.

---

## Key Results

| λ_gp | P(N > 20·n_obs) | DA prediction | Regime |
|------|-----------------|---------------|--------|
| 0.25 | 0.473 | 0.050 | Optimistic (DA overestimates doom) |
| 0.50 | 0.224 | 0.050 | Optimistic |
| **1.00** | **0.050** | **0.050** | **Carter's DA (baseline)** |
| 2.00 | 0.0025 | 0.050 | Pessimistic |
| 4.00 | 0.000006 | 0.050 | Pessimistic |

**Monte Carlo validation**: The DA's U(0,1) assumption holds ONLY for
λ_gp = 1 (KS p = 0.42). All other tested distributions reject U(0,1)
at p < 0.01.

---

## Scripts

| Script | Purpose | SOM Analog |
|--------|---------|------------|
| `doomsday.py` | Minimal model: Tables 1–3, fig1 heatmap | `fermi.py` |
| `doomsday_mc.py` | Monte Carlo validation: KS test against U(0,1) | `fermi_v2_mc.py` |
| `doomsday_forward_sim.py` | Full forward simulation: trajectory families | `fermi_forward_sim.py` |
| `doomsday_sensitivity.py` | Sensitivity analysis: fig2 (λ and W panels) | `fermi_sensitivity.py` |
| `doomsday_ati.py` | Structure-anchored ATI: Table 7, scaling audit | `fermi_empirical_F.py` |

---

## Structural Parallel: SOM ↔ Doomsday

| SOM (Fermi) | Doomsday (this work) |
|---|---|
| N_ever (total civilizations) | N_total (total humans) |
| κ (observability multiplier) | f = W / N_total (window fraction) |
| λ = N_ever · κ | g = r · T_remaining (growth potential) |
| F = λ / ln(10) | A = λ_gp · log₁₀(k) |
| P(D=0) = exp(−λ) | P(N > k·n) = k^{−λ_gp} |
| κ ≪ 1 → silence default | f ≪ 1 → doom not default |
| 1/κ (tension inflation) | 1/f (ATI inflation) |
| d_max² scaling (quadratic) | k^{−λ} scaling (power-law) |
| p_survey linear scaling | λ linear in ATI |

---

## Running the Code

```bash
# Requirements
pip install numpy scipy matplotlib

# Run all scripts
python doomsday.py
python doomsday_mc.py
python doomsday_forward_sim.py
python doomsday_sensitivity.py
python doomsday_ati.py
```

All scripts are self-contained and produce console tables + figures.
No external data files are required.

---

## Honesty Contract

The growth-potential rate λ_gp and the window-fraction values used here are
**ILLUSTRATIVE PLACEHOLDERS**. They are NOT calibrated to published demographic
projections (UN, IIASA, Lancet). A calibrated value can be substituted by
editing the relevant input block in each script; the framework (and the
paper's tables) is unchanged by that substitution.

The DA's λ_gp = 1 is ONE POINT in parameter space, not a theorem.

---

## AI Use Disclosure

AI-assisted tools were used for code development, mathematical verification,
and language polishing. All intellectual contributions — the framework design,
the factorization choices, the dimensional allocation of the window fraction,
the decision to exclude λ_gp from the window-fraction product, the honesty
contract, and the structural parallel with the SOM — are the author's.
The author takes full responsibility for the content.

---

## Citation

```bibtex
@misc{kilinc2026doomsday,
  title  = {Beyond Rank: An Observation-Adjusted Framework
            for the Doomsday Argument},
  author = {K{\i}l{\i}n{\c{c}}, Yavuz Selim},
  year   = {2026},
  doi    = {10.5281/zenodo.21562241},
  url    = {https://github.com/YSKpython/doomsday-oaf}
}
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Companion Paper

Kılınç, Y.S. (2026). "Beyond N: A Synchronized Observability Model for the
Fermi Paradox." Zenodo DOI: 10.5281/zenodo.21539849.
Code: https://github.com/YSKpython/fermi-som
```

### `LICENSE` — MIT

```
MIT License

Copyright (c) 2026 Yavuz Selim Kılınç

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
