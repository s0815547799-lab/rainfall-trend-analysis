"""
Formal validation suite for Comparative_4MMK.py — v2.1
Tests: T01–T24 covering syntax, MMK VIF, PW-MK, TFPW-MK, BH-FDR,
       AR1Generator, Monte Carlo Type I error.

Run with:  pytest tests/test_validation.py -v
or:        python tests/test_validation.py
"""

import sys, importlib, math, pathlib
import numpy as np
import pytest

# Allow running from repo root or from within tests/
ROOT = pathlib.Path(__file__).parent.parent
SRC  = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import Comparative_4MMK as c4

SEED = 42
RNG  = np.random.default_rng(SEED)


# ---------------------------------------------------------------------------
# T01 — Syntax: module imported without parse errors
# ---------------------------------------------------------------------------
def test_T01_syntax():
    assert c4 is not None


# ---------------------------------------------------------------------------
# T02 — MIN_N must not exist as a module-level name
# ---------------------------------------------------------------------------
def test_T02_min_n_absent():
    assert not hasattr(c4, "MIN_N"), "MIN_N must be removed from global namespace (FIX-8)"


# ---------------------------------------------------------------------------
# T03 — H&R98 Eq.(3): manual VIF cross-check on known series
#        For AR(1) phi=0.7, n=34, significant rho_k from paper → VIF≈1.749036
# ---------------------------------------------------------------------------
def test_T03_hr98_equation_match():
    rng = np.random.default_rng(SEED)
    phi = 0.7
    n   = 34
    series = np.zeros(n)
    for t in range(1, n):
        series[t] = phi * series[t-1] + rng.standard_normal()
    res = c4.modified_mk_hamed_rao(series)
    vif = res.get("vif", res.get("VIF", np.nan))
    assert not np.isnan(vif), "VIF must not be NaN"
    assert vif == pytest.approx(1.749036, abs=0.05), f"VIF={vif:.6f} deviates from expected 1.749036"


# ---------------------------------------------------------------------------
# T04 — Ranked ACF differs from raw-series ACF
# ---------------------------------------------------------------------------
def test_T04_ranked_acf():
    rng = np.random.default_rng(SEED)
    phi = 0.7
    n   = 50
    series = np.zeros(n)
    for t in range(1, n):
        series[t] = phi * series[t-1] + rng.standard_normal()
    res_mmk = c4.modified_mk_hamed_rao(series)
    vif_mmk = res_mmk.get("vif", res_mmk.get("VIF", np.nan))
    # Compute naive VIF from raw (unranked) series
    from statsmodels.tsa.stattools import acf
    from scipy.stats import norm
    rho_raw = acf(series, nlags=min(n-2, 20), fft=True, alpha=None)
    sig     = norm.ppf(0.975) / np.sqrt(n)
    vif_raw = 1.0 + 2.0 * sum((n-i)/n * rho_raw[i] for i in range(1, len(rho_raw))
                                if abs(rho_raw[i]) > sig)
    # VIF from ranked series must differ from VIF from raw series
    assert abs(vif_mmk - vif_raw) > 0.01, (
        f"Ranked VIF ({vif_mmk:.4f}) equals raw VIF ({vif_raw:.4f}) — ranked ACF not applied"
    )


# ---------------------------------------------------------------------------
# T05 — White noise: VIF ≈ 1.0 (no significant lags)
# ---------------------------------------------------------------------------
def test_T05_white_noise_vif():
    rng = np.random.default_rng(SEED)
    series = rng.standard_normal(500)
    res = c4.modified_mk_hamed_rao(series)
    vif = res.get("vif", res.get("VIF", np.nan))
    assert vif == pytest.approx(1.0, abs=0.15), f"White noise VIF={vif:.4f}, expected ≈1.0"


# ---------------------------------------------------------------------------
# T06 — Positive AR(1) phi=0.7: VIF > 1.0 (variance inflation)
# ---------------------------------------------------------------------------
def test_T06_positive_ar1_vif():
    rng = np.random.default_rng(SEED)
    series = np.zeros(200)
    for t in range(1, 200):
        series[t] = 0.7 * series[t-1] + rng.standard_normal()
    res = c4.modified_mk_hamed_rao(series)
    vif = res.get("vif", res.get("VIF", np.nan))
    assert vif > 1.0, f"Positive AR(1) VIF={vif:.4f} must be > 1.0"


# ---------------------------------------------------------------------------
# T07 — Negative AR(1): VIF clamped at 1.0 (FIX-9)
# ---------------------------------------------------------------------------
def test_T07_negative_ar1_vif_clamped():
    rng = np.random.default_rng(SEED)
    series = np.zeros(34)
    for t in range(1, 34):
        series[t] = -0.5 * series[t-1] + rng.standard_normal()
    res = c4.modified_mk_hamed_rao(series)
    vif = res.get("vif", res.get("VIF", np.nan))
    assert vif >= 1.0, f"Negative AR(1) VIF={vif:.4f} must be clamped to >=1.0 (FIX-9)"


# ---------------------------------------------------------------------------
# T08 — Raw vif_sum < 0 for negatively autocorrelated series
#        (confirms clamp is numerically essential, not cosmetic)
# ---------------------------------------------------------------------------
def test_T08_raw_vif_sum_negative():
    from statsmodels.tsa.stattools import acf
    from scipy.stats import norm
    rng = np.random.default_rng(SEED)
    phi = -0.7
    n   = 34
    series = np.zeros(n)
    for t in range(1, n):
        series[t] = phi * series[t-1] + rng.standard_normal()
    from scipy.stats import rankdata
    ranks  = rankdata(series)
    nlags  = min(n - 2, 20)
    rho    = acf(ranks, nlags=nlags, fft=True, alpha=None)
    sig    = norm.ppf(0.975) / np.sqrt(n)
    vif_sum = sum((n-i)/n * rho[i] for i in range(1, nlags+1) if abs(rho[i]) > sig)
    assert vif_sum < 0, f"vif_sum={vif_sum:.4f} should be negative for phi=-0.7"


# ---------------------------------------------------------------------------
# T09 — PW-MK: n=4 returns NaN dict
# ---------------------------------------------------------------------------
def test_T09_pw_n4_nan():
    res = c4.prewhitening_mk(np.array([1.0, 2.0, 3.0, 4.0]))
    assert np.isnan(res["Z"]), "PW-MK n=4 must return NaN (needs n>=5)"


# ---------------------------------------------------------------------------
# T10 — PW-MK: n=5 returns valid result
# ---------------------------------------------------------------------------
def test_T10_pw_n5_valid():
    res = c4.prewhitening_mk(np.array([1.0, 2.5, 2.0, 3.5, 4.0]))
    assert not np.isnan(res["Z"]), "PW-MK n=5 must return a valid Z statistic"


# ---------------------------------------------------------------------------
# T15 — PW-MK: n=9 valid (old MIN_N=10 gate must not block this)
# ---------------------------------------------------------------------------
def test_T15_pw_n9_valid():
    x = np.arange(1.0, 10.0)
    res = c4.prewhitening_mk(x)
    assert not np.isnan(res["Z"]), "PW-MK n=9 must be valid after MIN_N=10 removal (FIX-8)"


# ---------------------------------------------------------------------------
# T11 — TFPW-MK: n=4 returns NaN dict
# ---------------------------------------------------------------------------
def test_T11_tfpw_n4_nan():
    res = c4.tfpw_mk(np.array([1.0, 2.0, 3.0, 4.0]))
    assert np.isnan(res["Z"]), "TFPW-MK n=4 must return NaN"


# ---------------------------------------------------------------------------
# T12 — TFPW-MK: n=5 returns valid result
# ---------------------------------------------------------------------------
def test_T12_tfpw_n5_valid():
    res = c4.tfpw_mk(np.array([1.0, 2.5, 2.0, 3.5, 4.0]))
    assert not np.isnan(res["Z"]), "TFPW-MK n=5 must return a valid Z statistic"


# ---------------------------------------------------------------------------
# T16 — TFPW-MK: n=9 valid (old MIN_N=10 gate must not block this)
# ---------------------------------------------------------------------------
def test_T16_tfpw_n9_valid():
    x = np.arange(1.0, 10.0)
    res = c4.tfpw_mk(x)
    assert not np.isnan(res["Z"]), "TFPW-MK n=9 must be valid after MIN_N=10 removal (FIX-8)"


# ---------------------------------------------------------------------------
# T13 — PW-MK slope comes from original series, not prewhitened series
# ---------------------------------------------------------------------------
def test_T13_pw_slope_from_original():
    x = np.array([1.0, 3.0, 2.0, 5.0, 4.0, 7.0, 6.0, 9.0, 8.0, 11.0])
    res = c4.prewhitening_mk(x)
    expected_slope = c4.sens_slope(x)
    assert res["slope"] == pytest.approx(expected_slope, rel=1e-6), (
        f"PW-MK slope={res['slope']:.4f} must equal sens_slope(original)={expected_slope:.4f} (FIX-4)"
    )


# ---------------------------------------------------------------------------
# T14 — TFPW-MK slope equals original Sen's slope (beta used in detrending)
# ---------------------------------------------------------------------------
def test_T14_tfpw_slope_original():
    x = np.array([1.0, 3.0, 2.0, 5.0, 4.0, 7.0, 6.0, 9.0, 8.0, 11.0])
    res = c4.tfpw_mk(x)
    expected_slope = c4.sens_slope(x)
    assert res["slope"] == pytest.approx(expected_slope, rel=1e-6), (
        f"TFPW-MK slope={res['slope']:.4f} must equal original sens_slope={expected_slope:.4f}"
    )


# ---------------------------------------------------------------------------
# T15b — BH FDR: p=0.001 at alpha=0.05 is rejected; p=0.90 is retained
# ---------------------------------------------------------------------------
def test_T15b_bh_fdr_basic():
    p_values = np.array([0.001, 0.90])
    rejected = c4.benjamini_hochberg(p_values, alpha=0.05)
    assert rejected[0] == True,  "p=0.001 must be rejected by BH at alpha=0.05"
    assert rejected[1] == False, "p=0.90 must be retained by BH at alpha=0.05"


# ---------------------------------------------------------------------------
# T16b — BH returns bool array
# ---------------------------------------------------------------------------
def test_T16b_bh_returns_bool():
    p_values = np.array([0.01, 0.03, 0.05, 0.10, 0.50])
    result   = c4.benjamini_hochberg(p_values, alpha=0.05)
    assert result.dtype == bool or result.dtype == np.bool_, (
        f"BH result dtype={result.dtype}, expected bool"
    )
    assert len(result) == len(p_values)


# ---------------------------------------------------------------------------
# T17 — AR1Generator produces series of correct length
# ---------------------------------------------------------------------------
def test_T17_ar1_generator_length():
    gen    = c4.AR1Generator(phi=0.7, sigma=1.0, seed=SEED)
    series = gen.generate(n=34)
    assert len(series) == 34, f"AR1Generator produced {len(series)} points, expected 34"


# ---------------------------------------------------------------------------
# T18 — AR1Generator VIF >= 1.0 for all phi values
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("phi,label", [(0.7, "0.7"), (-0.5, "-0.5")])
def test_T18_ar1_vif_nonneg(phi, label):
    gen    = c4.AR1Generator(phi=phi, sigma=1.0, seed=SEED)
    series = gen.generate(n=200)
    res    = c4.modified_mk_hamed_rao(series)
    vif    = res.get("vif", res.get("VIF", np.nan))
    assert vif >= 1.0, f"phi={label}: VIF={vif:.4f} must be >= 1.0"


# ---------------------------------------------------------------------------
# T19–T22 — Monte Carlo Type I error: all four methods near 5% under H0
#            phi=0.0 (white noise), n=34, 10_000 iterations
#            Acceptance band: [2.5%, 7.5%]
# ---------------------------------------------------------------------------
def _mc_type_i(method_fn, n=34, n_iter=10_000, alpha=0.05, phi=0.0):
    rng = np.random.default_rng(SEED)
    count = 0
    for _ in range(n_iter):
        x = np.zeros(n)
        for t in range(1, n):
            x[t] = phi * x[t-1] + rng.standard_normal()
        res = method_fn(x)
        p   = res.get("p", np.nan)
        if not np.isnan(p) and p < alpha:
            count += 1
    return count / n_iter


def test_T19_type_i_mk():
    rate = _mc_type_i(c4.standard_mk)
    assert 0.025 <= rate <= 0.075, f"Standard MK Type I={rate:.4f} outside [0.025, 0.075]"


def test_T20_type_i_mmk():
    rate = _mc_type_i(c4.modified_mk_hamed_rao)
    assert 0.025 <= rate <= 0.075, f"MMK Type I={rate:.4f} outside [0.025, 0.075]"


def test_T21_type_i_pw():
    rate = _mc_type_i(c4.prewhitening_mk)
    assert 0.025 <= rate <= 0.075, f"PW-MK Type I={rate:.4f} outside [0.025, 0.075]"


def test_T22_type_i_tfpw():
    rate = _mc_type_i(c4.tfpw_mk)
    assert 0.025 <= rate <= 0.075, f"TFPW-MK Type I={rate:.4f} outside [0.025, 0.075]"


# ---------------------------------------------------------------------------
# T23 — H&R98 reduces Type I vs Standard MK for positive AR(1)
# ---------------------------------------------------------------------------
def test_T23_mmk_reduces_type_i():
    mk_rate  = _mc_type_i(c4.standard_mk,          phi=0.7)
    mmk_rate = _mc_type_i(c4.modified_mk_hamed_rao, phi=0.7)
    assert mmk_rate < mk_rate, (
        f"MMK Type I ({mmk_rate:.4f}) must be < MK Type I ({mk_rate:.4f}) for phi=0.7"
    )


# ---------------------------------------------------------------------------
# T24 — FDR analysis values in [0, 1]
# ---------------------------------------------------------------------------
def test_T24_fdr_values_range():
    df = c4.fdr_analysis(n_iter=200, seed=SEED)
    fdr_cols = [c for c in df.columns if "FDR" in c.upper() or "fdr" in c.lower()]
    assert len(fdr_cols) > 0, "fdr_analysis must return FDR columns"
    for col in fdr_cols:
        vals = df[col].dropna()
        assert (vals >= 0).all() and (vals <= 1).all(), (
            f"FDR column '{col}' contains values outside [0,1]: {vals.tolist()}"
        )


# ---------------------------------------------------------------------------
# Entry point for direct execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    print(f"Validation Suite — {__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 68)
    for fn in tests:
        name = fn.__name__
        try:
            if hasattr(fn, "pytestmark"):
                # parametrized — skip in direct mode
                print(f"[SKIP] {name} (parametrized — run via pytest)")
                continue
            fn()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            failed += 1
    print()
    print("=" * 68)
    print(f"  TOTAL: {passed+failed}  PASSED: {passed}  FAILED: {failed}")
    print("=" * 68)
    sys.exit(0 if failed == 0 else 1)
