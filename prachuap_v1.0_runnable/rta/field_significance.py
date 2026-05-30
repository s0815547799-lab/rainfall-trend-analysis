"""
rta.field_significance — Field significance testing for multi-station trend analysis.

References
----------
Walker, G. T. (1914). Correlation in seasonal variations of weather.
  Mem. India Meteorol. Dept., 21, 22–45.

Livezey, R. E., & Chen, W. Y. (1983). Statistical field significance and
  its determination by Monte Carlo techniques.
  Monthly Weather Review, 111, 46–59.
"""

import math
import numpy as np
import pandas as pd
from scipy.stats import binom

from .config import MIN_N, ALPHA_005, ALPHA_001
from .trend_tests import standard_mk

__all__ = ["walker_test", "livezey_chen_mc", "field_sig_summary"]


# ── Walker (1914) binomial test ───────────────────────────────────────────────

def walker_test(n_stations: int, n_sig: int,
                alpha: float = 0.05) -> dict:
    """
    Walker (1914) field significance test.

    Under H₀ (no field-wide trend), the number of locally significant tests
    follows Binomial(n_stations, alpha).  The one-sided p-value is:

        p_walker = P(X ≥ n_sig | n=n_stations, p=alpha)

    Parameters
    ----------
    n_stations : int  — total number of stations tested
    n_sig      : int  — number of stations with p < alpha
    alpha      : float — local significance level (default 0.05)

    Returns
    -------
    dict with keys:
        n_stations, n_sig, alpha,
        expected      (float) — n_stations × alpha,
        p_walker      (float) — one-sided binomial p-value,
        field_significant (bool),
        fraction_sig  (float)
    """
    if n_stations <= 0:
        return {"n_stations": 0, "n_sig": 0, "alpha": alpha,
                "expected": 0.0, "p_walker": 1.0,
                "field_significant": False, "fraction_sig": 0.0}

    # P(X >= n_sig) = 1 - P(X <= n_sig-1) = binom.sf(n_sig-1, n, p)
    p_walker = float(binom.sf(max(n_sig - 1, 0), n_stations, alpha))
    p_walker = min(p_walker, 1.0)

    return {
        "n_stations":        int(n_stations),
        "n_sig":             int(n_sig),
        "alpha":             float(alpha),
        "expected":          round(n_stations * alpha, 3),
        "p_walker":          round(p_walker, 6),
        "field_significant": bool(p_walker < alpha),
        "fraction_sig":      round(n_sig / n_stations, 4),
    }


# ── Livezey-Chen (1983) Monte Carlo permutation test ─────────────────────────

def livezey_chen_mc(series_dict: dict,
                    alpha: float = 0.05,
                    n_perm: int = 1000,
                    seed: int = 42) -> dict:
    """
    Livezey-Chen (1983) field significance via Monte Carlo permutation.

    Parameters
    ----------
    series_dict : dict
        {station_name: np.ndarray}  — one annual series per station.
        NaN values are dropped within each series.
    alpha  : float — local significance level (default 0.05)
    n_perm : int   — number of permutations (default 1000)
    seed   : int   — random seed for reproducibility

    Returns
    -------
    dict with keys:
        S_obs          (float)   — observed fraction of significant stations
        n_sig_obs      (int)     — observed count with p < alpha
        n_stations     (int)
        null_mean      (float)   — mean of MC null distribution
        null_std       (float)
        null_95th      (float)   — 95th percentile of null distribution
        p_field_LC     (float)   — fraction of MC draws ≥ S_obs
        field_significant (bool)
        n_perm         (int)
        null_distribution (np.ndarray) — full array of MC fractions

    Algorithm
    ---------
    1. Compute S_obs = fraction of stations whose observed standard_mk p < alpha.
    2. For each of n_perm permutations:
         a. Independently permute (shuffle) each station's series.
         b. Run standard_mk on each permuted series.
         c. Record fraction with p < alpha → one draw of the null.
    3. p_field_LC = fraction of draws ≥ S_obs.
    """
    rng = np.random.default_rng(seed)

    stations = list(series_dict.keys())
    n_s = len(stations)

    if n_s == 0:
        return {"S_obs": 0.0, "n_sig_obs": 0, "n_stations": 0,
                "null_mean": 0.0, "null_std": 0.0, "null_95th": 0.0,
                "p_field_LC": 1.0, "field_significant": False,
                "n_perm": n_perm, "null_distribution": np.array([])}

    # Clean series
    clean = {s: np.asarray(v, dtype=float) for s, v in series_dict.items()}
    clean = {s: v[~np.isnan(v)] for s, v in clean.items()}

    # Observed significance
    obs_sigs = sum(
        1 for v in clean.values()
        if len(v) >= MIN_N and standard_mk(v)["p_value"] < alpha
    )
    S_obs = obs_sigs / n_s

    # Monte Carlo null distribution
    null_fracs = np.empty(n_perm)
    for p in range(n_perm):
        count = 0
        for v in clean.values():
            if len(v) < MIN_N:
                continue
            v_perm = rng.permutation(v)
            if standard_mk(v_perm)["p_value"] < alpha:
                count += 1
        null_fracs[p] = count / n_s

    p_field_LC = float(np.mean(null_fracs >= S_obs))
    # Floor at 1/n_perm to avoid reporting exactly 0
    p_field_LC = max(p_field_LC, 1.0 / n_perm)

    return {
        "S_obs":             round(S_obs, 4),
        "n_sig_obs":         int(obs_sigs),
        "n_stations":        int(n_s),
        "null_mean":         round(float(np.mean(null_fracs)), 4),
        "null_std":          round(float(np.std(null_fracs)), 4),
        "null_95th":         round(float(np.percentile(null_fracs, 95)), 4),
        "p_field_LC":        round(p_field_LC, 6),
        "field_significant": bool(p_field_LC < alpha),
        "n_perm":            int(n_perm),
        "null_distribution": null_fracs,
    }


# ── Summary function: both tests for all temporal scales ─────────────────────

def field_sig_summary(scales: dict,
                      stns: list,
                      alpha: float = 0.05,
                      n_perm: int = 1000) -> pd.DataFrame:
    """
    Run Walker + Livezey-Chen field significance for each temporal scale.

    Parameters
    ----------
    scales : dict  — output of aggregate_all(); keys "annual", "wet", "dry"
    stns   : list  — station column names
    alpha  : float — local significance level (default 0.05)
    n_perm : int   — Monte Carlo permutations for LC test (default 1000)

    Returns
    -------
    pd.DataFrame  — one row per temporal scale with columns:
        Scale, N_stations,
        N_sig_MK,  Frac_sig_MK,  Walker_p_MK,  Walker_sig_MK,
                                  LC_S_obs_MK,  LC_p_MK,  LC_sig_MK,
                                  LC_null_mean_MK, LC_null_95th_MK,
        N_sig_MMK, Frac_sig_MMK, Walker_p_MMK, Walker_sig_MMK,
                                  LC_p_MMK,     LC_sig_MMK
    """
    from .trend_tests import modified_mk

    stns = [str(s) for s in stns]
    rows = []

    for sk in ["annual", "wet", "dry"]:
        df_s = scales.get(sk)
        if df_s is None:
            continue

        series_mk  = {}
        series_mmk = {}
        n_sig_mk   = 0
        n_sig_mmk  = 0
        n_valid    = 0

        for stn in stns:
            if stn not in df_s.columns:
                continue
            arr = df_s[stn].dropna().values.astype(float)
            if len(arr) < MIN_N:
                continue
            n_valid += 1
            series_mk[stn]  = arr
            series_mmk[stn] = arr
            if standard_mk(arr)["p_value"] < alpha:
                n_sig_mk += 1
            if modified_mk(arr)["p_value"] < alpha:
                n_sig_mmk += 1

        if n_valid == 0:
            continue

        wk_mk  = walker_test(n_valid, n_sig_mk,  alpha=alpha)
        wk_mmk = walker_test(n_valid, n_sig_mmk, alpha=alpha)

        lc_mk  = livezey_chen_mc(series_mk,  alpha=alpha, n_perm=n_perm)
        lc_mmk = livezey_chen_mc(series_mmk, alpha=alpha, n_perm=n_perm)

        rows.append({
            "Scale":           sk,
            "N_stations":      n_valid,
            "N_sig_MK":        n_sig_mk,
            "N_sig_MMK":       n_sig_mmk,
            "Frac_sig_MK":     round(n_sig_mk  / n_valid, 4),
            "Frac_sig_MMK":    round(n_sig_mmk / n_valid, 4),
            "Walker_p_MK":     wk_mk["p_walker"],
            "Walker_sig_MK":   wk_mk["field_significant"],
            "Walker_p_MMK":    wk_mmk["p_walker"],
            "Walker_sig_MMK":  wk_mmk["field_significant"],
            "LC_S_obs_MK":     lc_mk["S_obs"],
            "LC_p_MK":         lc_mk["p_field_LC"],
            "LC_sig_MK":       lc_mk["field_significant"],
            "LC_null_mean_MK": lc_mk["null_mean"],
            "LC_null_95th_MK": lc_mk["null_95th"],
            "LC_p_MMK":        lc_mmk["p_field_LC"],
            "LC_sig_MMK":      lc_mmk["field_significant"],
        })

    return pd.DataFrame(rows)
