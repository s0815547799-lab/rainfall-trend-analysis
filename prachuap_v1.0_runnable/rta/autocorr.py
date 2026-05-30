"""
rta.autocorr — Lag-k autocorrelation functions.

Extracted verbatim from rainfall_trend_analysis_v3.py §3 (lines 318–343).
"""

import math
import numpy as np
from scipy.stats import norm as scipy_norm
from .config import ALPHA_005


def lag_k_autocorr(x: np.ndarray, k: int = 1) -> float:
    """Pearson Lag-k autocorrelation."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < k + 3: return np.nan
    xb  = np.mean(x)
    num = np.sum((x[:n-k] - xb) * (x[k:n] - xb))
    den = np.sum((x - xb) ** 2)
    return float(num / den) if den > 0 else np.nan


def all_lag_autocorr(x: np.ndarray, max_lag: int = None) -> np.ndarray:
    """Autocorrelation for lags 1..max_lag (default n//3)."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 4: return np.array([])
    if max_lag is None: max_lag = min(n // 3, n - 1)
    return np.array([lag_k_autocorr(x, k) for k in range(1, max_lag + 1)])


def is_sig_autocorr(r1: float, n: int, alpha: float = 0.05) -> bool:
    """Two-tailed significance of Lag-1 autocorrelation."""
    if np.isnan(r1) or n < 4: return False
    return abs(r1) > scipy_norm.ppf(1 - alpha/2) / math.sqrt(n)
