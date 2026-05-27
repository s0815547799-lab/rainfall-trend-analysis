"""
rta.tfpw — Trend-Free Prewhitening Mann-Kendall Test.

References
----------
Yue, S., Pilon, P., Phinney, B., & Cavadias, G. (2002). The influence of
autocorrelation on the ability to detect trend in hydrological series.
Hydrological Processes, 16, 1807–1829.

Önöz, B., & Bayazit, M. (2003). The power of statistical tests for trend
detection. Hydrological Sciences Journal, 48, 25–34.
"""

import numpy as np

from .config import MIN_N, ALPHA_005, ALPHA_001
from .autocorr import lag_k_autocorr, is_sig_autocorr
from .trend_tests import sens_slope, standard_mk

__all__ = ["tfpw_mk"]


def tfpw_mk(x: np.ndarray) -> dict:
    """
    Trend-Free Prewhitening Mann-Kendall (TFPW-MK) trend test.

    Parameters
    ----------
    x : array-like
        Annual (or seasonal) time series, NaN values are dropped.

    Returns
    -------
    dict with all standard_mk fields plus:
        pw_applied  (bool)   — True when prewhitening was applied
        beta_initial (float) — Sen's slope of original series
        rho_1_used   (float) — lag-1 AC of detrended series
        method       (str)   — "TFPW-MK"

    Algorithm
    ---------
    1.  β = Sen's slope of original series x.
    2.  Detrend: x_d[i] = x[i] − β·(i+1)     (1-indexed time axis)
    3.  ρ₁ = lag_k_autocorr(x_d, k=1)
    4a. If ρ₁ NOT significant:
            z = original x  (no prewhitening needed)
            pw_applied = False
    4b. If ρ₁ IS significant:
            Prewhiten detrended series:
                y[i] = x_d[i+1] − ρ₁ · x_d[i]   (length n-1)
            Restore trend:
                z[i] = y[i] + β · (i+2)           (1-indexed, shifted by 1)
            pw_applied = True
    5.  Return standard_mk(z).
    """
    _null = {k: np.nan for k in ["S", "n", "Var_S", "Z", "p_value", "tau",
                                  "slope_Q", "slope_lo", "slope_hi",
                                  "trend", "sig_05", "sig_01",
                                  "pw_applied", "beta_initial", "rho_1_used"]}
    _null.update({"trend": "—", "sig_05": False, "sig_01": False,
                  "pw_applied": False, "beta_initial": np.nan,
                  "rho_1_used": np.nan, "method": "TFPW-MK"})

    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < MIN_N:
        return _null

    t = np.arange(1, n + 1, dtype=float)

    # Step 1: Sen's slope of original
    beta, _, _ = sens_slope(x)
    if np.isnan(beta):
        beta = 0.0

    # Step 2: Detrend
    x_d = x - beta * t

    # Step 3: lag-1 AC of detrended series
    rho1   = lag_k_autocorr(x_d, k=1)
    sig_ac = is_sig_autocorr(rho1, n)

    if not sig_ac or np.isnan(rho1):
        # No prewhitening needed — run MK on original
        res = standard_mk(x)
        res["pw_applied"]   = False
        res["beta_initial"] = round(float(beta), 4)
        res["rho_1_used"]   = float(rho1) if not np.isnan(rho1) else np.nan
        res["method"]       = "TFPW-MK"
        return res

    # Step 4b: Prewhiten detrended series
    y = x_d[1:] - rho1 * x_d[:-1]      # length n-1
    t2 = np.arange(2, n + 1, dtype=float)  # time axis for restored series

    # Restore trend component
    z = y + beta * t2

    if len(z) < MIN_N:
        return _null

    res = standard_mk(z)
    res["pw_applied"]   = True
    res["beta_initial"] = round(float(beta), 4)
    res["rho_1_used"]   = round(float(rho1), 4)
    res["method"]       = "TFPW-MK"
    return res
