"""
rta.pw — Prewhitening Mann-Kendall Test (Yue & Wang 2004).

Yue, S., & Wang, C. (2004). The Mann-Kendall test modified by effective
sample size to detect trend in serially correlated hydrological series.
Water Resources Research, 40, W08307.
"""

import math
import numpy as np
from scipy.stats import norm as _norm

from .config import MIN_N, ALPHA_005, ALPHA_001
from .autocorr import lag_k_autocorr, is_sig_autocorr
from .trend_tests import (
    _mk_s_fast, mk_variance_ties, sens_slope,
    standard_mk,
)

__all__ = ["pw_mk"]


def pw_mk(x: np.ndarray) -> dict:
    """
    Prewhitening Mann-Kendall (PW-MK) trend test.

    Parameters
    ----------
    x : array-like
        Annual (or seasonal) time series, NaN values are dropped.

    Returns
    -------
    dict with keys:
        S, n, Var_S, Z, p_value, tau,
        slope_Q, slope_lo, slope_hi,
        trend, sig_05, sig_01,
        pw_applied (bool),
        rho_1_used (float),
        method ("PW-MK")

    Algorithm
    ---------
    1. Compute ρ₁ = lag_k_autocorr(x, k=1).
    2. Test significance: |ρ₁| > Z₀.₀₂₅ / √n  (two-tailed, α=0.05).
    3. If ρ₁ NOT significant  → apply standard_mk(x) unchanged.
    4. If ρ₁ IS  significant  → prewhiten:
           y[i] = x[i+1] − ρ₁ · x[i]   (length n-1)
       then apply standard_mk(y).
    """
    _null = {k: np.nan for k in ["S", "n", "Var_S", "Z", "p_value", "tau",
                                  "slope_Q", "slope_lo", "slope_hi",
                                  "trend", "sig_05", "sig_01",
                                  "pw_applied", "rho_1_used"]}
    _null.update({"trend": "—", "sig_05": False, "sig_01": False,
                  "pw_applied": False, "rho_1_used": np.nan,
                  "method": "PW-MK"})

    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < MIN_N:
        return _null

    rho1   = lag_k_autocorr(x, k=1)
    sig_ac = is_sig_autocorr(rho1, n)

    if not sig_ac or np.isnan(rho1):
        # No significant autocorrelation — standard MK on original series
        res = standard_mk(x)
        res["pw_applied"]  = False
        res["rho_1_used"]  = float(rho1) if not np.isnan(rho1) else np.nan
        res["method"]      = "PW-MK"
        return res

    # Prewhiten: y[i] = x[i+1] − ρ₁ · x[i]
    y = x[1:] - rho1 * x[:-1]

    if len(y) < MIN_N:
        return _null

    res = standard_mk(y)
    res["pw_applied"] = True
    res["rho_1_used"] = round(float(rho1), 4)
    res["method"]     = "PW-MK"
    return res
