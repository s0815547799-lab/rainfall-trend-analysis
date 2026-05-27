"""
rta.trend_tests — Mann-Kendall family trend tests and Sen's slope estimator.

Extracted and extended from rainfall_trend_analysis_v3.py §4-§6
(lines 350–535).

Tests implemented:
  - Standard MK      (Mann 1945; Kendall 1975)
  - Modified MK      (Hamed & Rao 1998, J. Hydrol. 204:182–196)
  - PW-MK            (Yue & Wang 2004, Water Resour. Res. 40:W08307)
  - TFPW-MK          (Yue et al. 2002; Önöz & Bayazit 2003, Hydrol. Sci. J. 48:25–34)
"""

import math
import numpy as np
from scipy import stats as sps
from scipy.stats import norm as scipy_norm
from .config import MIN_N, ALPHA_005, ALPHA_001, Z_005, Z_001
from .autocorr import lag_k_autocorr, all_lag_autocorr, is_sig_autocorr


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  S statistic helpers                                                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def mk_s_ties(x: np.ndarray) -> tuple:
    """Compute S statistic and tie sizes."""
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 4: return np.nan, []
    S = int(np.sum(np.sign(x[j] - x[i])
                   for i in range(n-1) for j in range(i+1, n)))
    _, counts = np.unique(x, return_counts=True)
    ties = counts[counts > 1].tolist()
    return float(S), ties


def _mk_s_fast(x: np.ndarray) -> tuple:
    """Vectorised S statistic (faster than nested loops for large n)."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 4: return np.nan, []
    S = 0
    for i in range(n - 1):
        S += int(np.sum(np.sign(x[i+1:] - x[i])))
    _, counts = np.unique(x, return_counts=True)
    ties = counts[counts > 1].tolist()
    return float(S), ties


def mk_variance_ties(n: int, ties: list) -> float:
    """Var(S) with tie correction."""
    tie_sum = sum(t * (t - 1) * (2 * t + 5) for t in ties)
    return (n * (n - 1) * (2 * n + 5) - tie_sum) / 18.0


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Sen's Slope Estimator  (Sen 1968 / Gilbert 1987)                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def sens_slope(x: np.ndarray, alpha: float = 0.05) -> tuple:
    """
    Sen's Slope Estimator + 95% CI (rank-based, Gilbert 1987).

    Q  = median[(xj - xi)/(j - i)]  for all j > i
    CI : Calpha = z_{alpha/2} * sqrt(Var(S))
         lo_rank = (N - Calpha)/2,  hi_rank = (N + Calpha)/2 + 1
    """
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 4: return np.nan, np.nan, np.nan

    slopes = []
    for i in range(n - 1):
        for j in range(i + 1, n):
            slopes.append((x[j] - x[i]) / (j - i))
    slopes = np.sort(slopes)
    N      = len(slopes)
    Q      = float(np.median(slopes))

    _, ties = _mk_s_fast(x)
    Var_S   = mk_variance_ties(n, ties)
    if Var_S <= 0: return Q, np.nan, np.nan

    z_crit  = scipy_norm.ppf(1 - alpha / 2)
    C_alpha = z_crit * math.sqrt(Var_S)
    lo_r    = max(0,     int(round((N - C_alpha) / 2.0)))
    hi_r    = min(N - 1, int(round((N + C_alpha) / 2.0)))

    return Q, float(slopes[lo_r]), float(slopes[hi_r])


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Standard Mann-Kendall Test  (Mann 1945; Kendall 1975)                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def standard_mk(x: np.ndarray) -> dict:
    """
    Standard Mann-Kendall Test  (Mann 1945; Kendall 1975).

    Does NOT correct for serial autocorrelation.
    Use this as baseline; compare with Modified MK.
    """
    null = {k: np.nan for k in ["S", "n", "Var_S", "Z", "p_value", "tau",
                                  "slope_Q", "slope_lo", "slope_hi",
                                  "trend", "sig_05", "sig_01"]}
    null.update({"trend": "—", "sig_05": False, "sig_01": False})

    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = int(len(x))
    if n < MIN_N: return null

    S, ties = _mk_s_fast(x)
    if np.isnan(S): return null

    Var_S = mk_variance_ties(n, ties)
    if Var_S <= 0: return null

    Z = (S - 1) / math.sqrt(Var_S) if S > 0 else \
        (S + 1) / math.sqrt(Var_S) if S < 0 else 0.0
    p_val = float(min(2.0 * (1.0 - scipy_norm.cdf(abs(Z))), 1.0))
    tau   = float(S / (0.5 * n * (n - 1)))
    sig05 = p_val < ALPHA_005
    sig01 = p_val < ALPHA_001
    trend = ("Increasing ↑" if (sig05 and Z > 0) else
             "Decreasing ↓" if (sig05 and Z < 0) else "No trend")

    slope_Q, slope_lo, slope_hi = sens_slope(x)

    return {"S":       float(S),          "n":       n,
            "Var_S":   round(Var_S, 2),   "Z":       round(Z, 4),
            "p_value": round(p_val, 6),   "tau":     round(tau, 4),
            "slope_Q": round(slope_Q, 3)  if not np.isnan(slope_Q)  else np.nan,
            "slope_lo":round(slope_lo, 3) if not np.isnan(slope_lo) else np.nan,
            "slope_hi":round(slope_hi, 3) if not np.isnan(slope_hi) else np.nan,
            "trend":   trend, "sig_05": sig05, "sig_01": sig01,
            "method":  "Standard MK"}


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Modified Mann-Kendall Test  (Hamed & Rao 1998)                         ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def modified_mk(x: np.ndarray) -> dict:
    """
    Modified Mann-Kendall Test  (Hamed & Rao 1998, J. Hydrol. 204:182-196).

    Corrects Var(S) for serial autocorrelation using ranked-series
    autocorrelations and effective sample size n*:

       n / n* = 1 + (2/n) sum_{k=1}^{n-1} (n-k) rho_k(ranks)

    Only statistically significant rho_k are used (Hamed & Rao 1998).
    Var*(S) = Var(S) * (n / n*)
    """
    null = {k: np.nan for k in ["S", "n", "Var_S", "Var_S_adj", "n_eff",
                                  "rho_1", "Z", "p_value", "tau",
                                  "slope_Q", "slope_lo", "slope_hi",
                                  "trend", "sig_05", "sig_01"]}
    null.update({"trend": "—", "sig_05": False, "sig_01": False})

    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = int(len(x))
    if n < MIN_N: return null

    S, ties = _mk_s_fast(x)
    if np.isnan(S): return null

    Var_S = mk_variance_ties(n, ties)
    if Var_S <= 0: return null

    # Autocorrelations of ranked series (Hamed & Rao 1998)
    ranks = sps.rankdata(x).astype(float)
    rho   = all_lag_autocorr(ranks, max_lag=min(n // 3, n - 1))

    # Effective sample size correction
    if len(rho) == 0:
        n_over_neff = 1.0
    else:
        se_rho = 1.0 / math.sqrt(n)
        z_crit = scipy_norm.ppf(1 - ALPHA_005 / 2)
        rho_sig = np.where(np.abs(rho) > z_crit * se_rho, rho, 0.0)
        ks   = np.arange(1, len(rho_sig) + 1)
        n_over_neff = max(1.0 + (2.0 / n) * np.sum((n - ks) * rho_sig), 1.0)

    rho_1     = float(rho[0]) if len(rho) > 0 else np.nan
    n_eff     = n / n_over_neff
    Var_S_adj = Var_S * n_over_neff

    Z     = (S - 1) / math.sqrt(Var_S_adj) if S > 0 else \
            (S + 1) / math.sqrt(Var_S_adj) if S < 0 else 0.0
    p_val = float(min(2.0 * (1.0 - scipy_norm.cdf(abs(Z))), 1.0))
    tau   = float(S / (0.5 * n * (n - 1)))
    sig05 = p_val < ALPHA_005
    sig01 = p_val < ALPHA_001
    trend = ("Increasing ↑" if (sig05 and Z > 0) else
             "Decreasing ↓" if (sig05 and Z < 0) else "No trend")

    slope_Q, slope_lo, slope_hi = sens_slope(x)

    return {"S":        float(S),            "n":         n,
            "Var_S":    round(Var_S, 2),
            "Var_S_adj":round(Var_S_adj, 2), "n_eff":     round(n_eff, 2),
            "rho_1":    round(rho_1, 4)      if not np.isnan(rho_1) else np.nan,
            "Z":        round(Z, 4),          "p_value":   round(p_val, 6),
            "tau":      round(tau, 4),
            "slope_Q":  round(slope_Q, 3)    if not np.isnan(slope_Q)  else np.nan,
            "slope_lo": round(slope_lo, 3)   if not np.isnan(slope_lo) else np.nan,
            "slope_hi": round(slope_hi, 3)   if not np.isnan(slope_hi) else np.nan,
            "trend":    trend, "sig_05": sig05, "sig_01": sig01,
            "method":   "Modified MK (H&R98)"}


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PW-MK: Prewhitening Mann-Kendall  (Yue & Wang 2004)                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def pw_mk(x: np.ndarray) -> dict:
    """
    Prewhitening Mann-Kendall Test (Yue & Wang 2004, Water Resour. Res. 40:W08307).

    Algorithm:
      1. Compute rho1 = lag_k_autocorr(x, k=1)
      2. sig_ac = is_sig_autocorr(rho1, n)
      3. If not sig_ac: return standard_mk(x) with pw_applied=False, rho_1_used=rho1
      4. Prewhiten: y[i] = x[i+1] - rho1 * x[i]  (length n-1)
      5. Return standard_mk(y) with pw_applied=True, rho_1_used=rho1

    Returns dict with all standard_mk fields plus:
      "pw_applied": bool
      "rho_1_used": float
      "method": "PW-MK"
    """
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = int(len(x))

    # Build null result with all standard_mk fields + pw extras
    null_base = {k: np.nan for k in ["S", "n", "Var_S", "Z", "p_value", "tau",
                                       "slope_Q", "slope_lo", "slope_hi",
                                       "trend", "sig_05", "sig_01"]}
    null_base.update({"trend": "—", "sig_05": False, "sig_01": False,
                      "pw_applied": False, "rho_1_used": np.nan,
                      "method": "PW-MK"})
    if n < MIN_N:
        return null_base

    rho1   = lag_k_autocorr(x, k=1)
    sig_ac = is_sig_autocorr(rho1, n)

    if not sig_ac:
        res = standard_mk(x)
        res["pw_applied"] = False
        res["rho_1_used"] = float(rho1) if not np.isnan(rho1) else np.nan
        res["method"]     = "PW-MK"
        return res

    # Prewhiten: y[i] = x[i+1] - rho1 * x[i]
    y = x[1:] - rho1 * x[:-1]

    res = standard_mk(y)
    res["pw_applied"] = True
    res["rho_1_used"] = float(rho1)
    res["method"]     = "PW-MK"
    return res


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TFPW-MK: Trend-Free Prewhitening  (Yue et al. 2002 / Önöz & Bayazit) ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def tfpw_mk(x: np.ndarray) -> dict:
    """
    Trend-Free Prewhitening Mann-Kendall Test.
    Reference: Yue et al. (2002); Önöz & Bayazit (2003) Hydrol. Sci. J. 48:25-34.

    Algorithm:
      1. Compute beta = sens_slope(x)[0]  (Sen's slope of original series)
      2. t = np.arange(1, n+1)
      3. x_d[i] = x[i] - beta * t[i]     (detrend)
      4. rho1 = lag_k_autocorr(x_d, k=1)
      5. If not is_sig_autocorr(rho1, n):
           pw_applied = False
           z = x_d + beta * t   (same as original)
         Else:
           y[i] = x_d[i+1] - rho1 * x_d[i]   (prewhiten detrended, length n-1)
           z[i] = y[i] + beta * t[i+1]         (restore trend, length n-1)
           pw_applied = True
      6. Return standard_mk(z) with pw_applied, beta_initial=beta, rho_1_used=rho1

    Returns dict with all standard_mk fields plus:
      "pw_applied": bool
      "beta_initial": float  (Sen's slope of original)
      "rho_1_used": float
      "method": "TFPW-MK"
    """
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = int(len(x))

    # Build null result with all standard_mk fields + tfpw extras
    null_base = {k: np.nan for k in ["S", "n", "Var_S", "Z", "p_value", "tau",
                                       "slope_Q", "slope_lo", "slope_hi",
                                       "trend", "sig_05", "sig_01"]}
    null_base.update({"trend": "—", "sig_05": False, "sig_01": False,
                      "pw_applied": False, "beta_initial": np.nan,
                      "rho_1_used": np.nan, "method": "TFPW-MK"})
    if n < MIN_N:
        return null_base

    # Step 1: Sen's slope of original series
    beta = sens_slope(x)[0]
    if np.isnan(beta):
        return null_base

    # Step 2-3: Detrend
    t   = np.arange(1, n + 1, dtype=float)
    x_d = x - beta * t

    # Step 4: Lag-1 autocorrelation of detrended series
    rho1   = lag_k_autocorr(x_d, k=1)
    sig_ac = is_sig_autocorr(rho1, n)

    if not sig_ac:
        # No significant autocorrelation: restore and test original
        pw_applied = False
        z = x_d + beta * t   # same as original x
    else:
        # Prewhiten the detrended series, then restore trend
        pw_applied = True
        y = x_d[1:] - rho1 * x_d[:-1]          # length n-1
        z = y + beta * t[1:]                     # restore trend on t[1..n]

    res = standard_mk(z)
    res["pw_applied"]   = pw_applied
    res["beta_initial"] = float(beta)
    res["rho_1_used"]   = float(rho1) if not np.isnan(rho1) else np.nan
    res["method"]       = "TFPW-MK"
    return res
