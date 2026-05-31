"""
cmip6_trend.module01.lag_k_mmk
==============================

Lag-K Modified Mann-Kendall (PRIMARY trend method) and Sen's intercept.

This module does NOT re-implement the Mann-Kendall S statistic or Sen's slope.
It REUSES the audit-passed primitives from the frozen baseline
(``cmip6_trend.trend_tests`` and ``cmip6_trend.autocorr``) and exposes the
Lag-K variance correction with explicit reporting required by the Directive:

    - significant lag(s)        (ranked-series autocorrelation, alpha=0.05)
    - effective sample size n*
    - variance correction n/n*  and adjusted Var(S)
    - corrected Z and corrected p

Method (Hamed & Rao 1998, J. Hydrol. 204:182-196), significant-lag form:

    n/n* = 1 + (2/n) * sum_{k in significant lags} (n-k) * rho_k(ranks)
    Var*(S) = Var(S) * (n/n*)

The set of significant lags is reported (``lag_used``); when no lag is
significant the result reduces to Standard MK (n*=n, correction=1).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats as sps
from scipy.stats import norm as scipy_norm

from .config import MIN_N, ALPHA_005, ALPHA_001
from .trend_tests import _mk_s_fast, mk_variance_ties, sens_slope
from .autocorr import all_lag_autocorr

__all__ = ["sen_intercept", "lag_k_mmk"]


def sen_intercept(x: np.ndarray, slope: float) -> float:
    """Sen's intercept (Conover 1980): median(x) - slope * median(t), t=1..n."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n == 0 or np.isnan(slope):
        return np.nan
    t = np.arange(1, n + 1, dtype=float)
    return float(np.median(x) - slope * np.median(t))


def lag_k_mmk(x: np.ndarray) -> dict:
    """Lag-K Modified Mann-Kendall test (primary method).

    Parameters
    ----------
    x : 1-D array of a single series (annual/seasonal/per-month-across-years).

    Returns
    -------
    dict with keys:
        method, n, tau, s, var_s, var_s_adj, z, p_value, significant,
        sen_slope, sen_intercept, sen_lo, sen_hi,
        lag_used (list[int]), n_effective, correction_factor, rho_1, sig_01
    """
    null = {
        "method": "Lag-K MMK", "n": np.nan, "tau": np.nan, "s": np.nan,
        "var_s": np.nan, "var_s_adj": np.nan, "z": np.nan, "p_value": np.nan,
        "significant": False, "sen_slope": np.nan, "sen_intercept": np.nan,
        "sen_lo": np.nan, "sen_hi": np.nan, "lag_used": [], "n_effective": np.nan,
        "correction_factor": np.nan, "rho_1": np.nan, "sig_01": False,
    }

    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = int(len(x))
    if n < MIN_N:
        return null

    # --- S, Var(S) via audit-passed primitives ---
    S, ties = _mk_s_fast(x)
    if np.isnan(S):
        return null
    var_s = mk_variance_ties(n, ties)
    if var_s <= 0:
        return null

    # --- ranked-series autocorrelation; keep only significant lags ---
    ranks = sps.rankdata(x).astype(float)
    max_lag = min(n // 3, n - 1)
    rho = all_lag_autocorr(ranks, max_lag=max_lag)

    lag_used: list[int] = []
    if len(rho) == 0:
        n_over_neff = 1.0
        rho_1 = np.nan
    else:
        se_rho = 1.0 / math.sqrt(n)
        z_crit = scipy_norm.ppf(1 - ALPHA_005 / 2)
        sig_mask = np.abs(rho) > z_crit * se_rho
        rho_sig = np.where(sig_mask, rho, 0.0)
        ks = np.arange(1, len(rho_sig) + 1)
        n_over_neff = max(1.0 + (2.0 / n) * np.sum((n - ks) * rho_sig), 1.0)
        lag_used = [int(k) for k in ks[sig_mask]]
        rho_1 = float(rho[0])

    n_eff = n / n_over_neff
    var_s_adj = var_s * n_over_neff

    # --- corrected Z, p ---
    z = ((S - 1) / math.sqrt(var_s_adj) if S > 0 else
         (S + 1) / math.sqrt(var_s_adj) if S < 0 else 0.0)
    p = float(min(2.0 * (1.0 - scipy_norm.cdf(abs(z))), 1.0))
    tau = float(S / (0.5 * n * (n - 1)))
    sig05 = p < ALPHA_005
    sig01 = p < ALPHA_001

    slope_Q, slope_lo, slope_hi = sens_slope(x)
    intercept = sen_intercept(x, slope_Q)

    return {
        "method": "Lag-K MMK", "n": n, "tau": round(tau, 4), "s": float(S),
        "var_s": round(var_s, 4), "var_s_adj": round(var_s_adj, 4),
        "z": round(z, 4), "p_value": round(p, 6), "significant": bool(sig05),
        "sen_slope": round(slope_Q, 4) if not np.isnan(slope_Q) else np.nan,
        "sen_intercept": round(intercept, 4) if not np.isnan(intercept) else np.nan,
        "sen_lo": round(slope_lo, 4) if not np.isnan(slope_lo) else np.nan,
        "sen_hi": round(slope_hi, 4) if not np.isnan(slope_hi) else np.nan,
        "lag_used": lag_used,
        "n_effective": round(n_eff, 4),
        "correction_factor": round(n_over_neff, 4),
        "rho_1": round(rho_1, 4) if not np.isnan(rho_1) else np.nan,
        "sig_01": bool(sig01),
    }
