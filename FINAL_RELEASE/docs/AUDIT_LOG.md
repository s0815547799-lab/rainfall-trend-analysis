# Scientific Audit Log — Comparative_4MMK.py v2.1

**Date:** 2026-06-17  
**Scope:** Corrections FIX-1 through FIX-9  
**Standard:** Q1/Q2 hydroclimatology publication

---

## FIX-1 — CRITICAL: FDR Analysis (BH correction)

**Problem:** `fdr_analysis()` called `standard_mk()` for rejection rate without passing p-values through `benjamini_hochberg()`. FDR columns reflected raw FWER rates.

**Correction:** `fdr_analysis()` now correctly computes BH-adjusted rejection indicator per iteration and averages over Monte Carlo draws.

**Verification:** T24 — FDR values in [0, 1]; BH manually cross-checked against Benjamini & Hochberg (1995) Table 1.

---

## FIX-2 — CRITICAL: AR1Generator independence

**Problem:** `AR1Generator` was re-created inside the inner simulation loop, resetting the RNG state on every draw. All replications had identical seeds, destroying Monte Carlo independence.

**Correction:** Generator created once per phi level, outside the loop. Each call to `.generate()` advances the same RNG.

**Verification:** Empirical Type I rates now converge to nominal alpha=5% for phi=0. Prior to fix, rates were deterministic and biased.

---

## FIX-3 / FIX-9 — CRITICAL: VIF clamping (reclassified)

**Problem (original FIX-3):** VIF computed without floor. For negatively autocorrelated series, VIF < 0 → Var*(S) < 0 → `sqrt()` undefined / NaN.

**Reclassification (FIX-9):** Originally labelled "MODERATE policy choice." After publication-grade MC validation, reclassified CRITICAL.

**Root cause:** H&R98 significant-lag filter passes ρ₁ < 0 for φ < 0 series while sub-threshold even lags (ρ₂, ρ₄…) are excluded. Net vif_sum < 0 for φ ∈ [−0.7, −0.3]. Without clamp:

| φ | Unclamped Type I | Clamped Type I |
|---|---|---|
| −0.7 | 47.4% | 0.02% |
| −0.5 | 37.1% | 0.22% |
| −0.3 | 18.2% | 1.02% |

**Scientific basis:** H&R98 was derived for positive serial persistence (hydrological data). Clamp at VIF=1.0 means: "when data are negatively autocorrelated, apply no variance correction." This is conservative and correct — negative AC makes MK conservative, not anti-conservative.

**Verification:** T07 (VIF ≥ 1.0 for φ=−0.5), T08 (raw vif_sum < 0 confirmed).

---

## FIX-4 — MODERATE: PW-MK slope source

**Problem:** `prewhitening_mk()` returned `sens_slope(x_pw)` — slope computed on the prewhitened series. Prewhitening removes trend signal; the resulting slope underestimates the true trend.

**Correction:** `slope` field now returns `sens_slope(x)` (original series). Prewhitened slope stored separately as `slope_pw` for diagnostic comparison.

**Reference:** CLAUDE.md §12.1 — "PW-MK: Sen's slope MUST come from original series x."

**Verification:** T13 — PW-MK slope == sens_slope(original).

---

## FIX-5 — MINOR: CI computation (t vs z)

**Problem:** `_ci95()` used z = 1.96 (Gaussian) regardless of sample size. For n ≤ 30, t-distribution provides correct coverage.

**Correction:** Uses `scipy.stats.t.ppf(0.975, df=n-1)`.

---

## FIX-6 — MINOR: AR1Generator initialisation

**Problem:** `X₀ = 0` initialisation comment omitted the stationarity caveat. Starting at 0 rather than the stationary distribution introduces burn-in bias for large |φ|.

**Correction:** Added 50-step burn-in in `AR1Generator.generate()`. Innovation variance scaled as σ·√(1−φ²) to preserve stationary variance.

---

## FIX-7 — CRITICAL: H&R98 significant-lag filter

**Problem:** Original `modified_mk_hamed_rao()` summed all ACF lags, including sub-threshold lags that contain only sampling noise. This inflates VIF and over-corrects variance.

**Correction:** Only lags with |ρS(k)| > 1.96/√n (Bartlett significance bound) are included in the VIF sum. Implements H&R98 Eq.(3) exactly.

**H&R98 Eq.(3):** n/n* = 1 + (2/n)·Σᵢ(n−i)·ρS(i), sum only over significant i.

**MC results (n=34, 5,000 iterations, seed=42):**

| φ | MK Type I | MMK Type I |
|---|---|---|
| 0.0 | 4.4% | 3.8% |
| 0.3 | 13.0% | 8.6% |
| 0.7 | 38.1% | 11.1% |

Residual inflation at φ ≥ 0.3 is a known limitation of H&R98 (Önöz & Bayazit 2003, Hydrol. Sci. J. 48:25–34), not a code error.

**Verification:** T03 (manual VIF = 1.749036), T04 (ranked ≠ raw ACF), T23 (MMK < MK for φ=0.7).

---

## FIX-8 — REDESIGNED: Minimum n for prewhitening methods

**Original (rejected):** `n < MIN_N + 1` where `MIN_N = 10`. No cited literature (Mann 1945, Kendall 1975, H&R98, Yue et al. 2002, Yue & Wang 2004) specifies n ≥ 10 as a requirement.

**Redesign:** Algorithm-derived minimum n ≥ 5:
- `np.corrcoef(x[:-1], x[1:])` requires len ≥ 2 → n ≥ 3
- `standard_mk(x_pw)` on len n−1 series requires n−1 ≥ 4 (for C(4,2)=6 non-trivial pairwise comparisons) → n ≥ 5
- Combined: **n ≥ 5 is the exact computational minimum**

`MIN_N = 10` removed entirely from the algorithm layer.

**Verification:** T09/T11 (n=4 → NaN), T10/T12 (n=5 → valid), T15/T16 (n=9 → valid, previously blocked by MIN_N=10).

---

## References

| Citation | DOI / Source |
|---|---|
| Mann (1945) | Econometrica 13:245–259 |
| Kendall (1975) | Rank Correlation Methods, Griffin |
| Hamed & Rao (1998) | J. Hydrol. 204:182–196 |
| Yue et al. (2002) | Water Resour. Res. 38(6):1009 |
| Yue & Wang (2004) | Water Resour. Res. 40:W08307 |
| Önöz & Bayazit (2003) | Hydrol. Sci. J. 48:25–34 |
| Benjamini & Hochberg (1995) | J. R. Stat. Soc. B 57:289–300 |
| Sen (1968) | JASA 63:1379–1389 |
| Gilbert (1987) | Statistical Methods for Environmental Pollution Monitoring |
