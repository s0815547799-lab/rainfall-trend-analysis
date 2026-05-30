"""
rta.field_sig — Field significance testing for hydroclimatological trend studies.

Implements:
  - Walker (1914) binomial test for field significance
  - Livezey-Chen (1983) Monte Carlo permutation test
  - field_sig_summary() — convenience wrapper for all temporal scales

References
----------
Walker, G.T. (1914) Memoirs of the Indian Meteorological Department 24:75-131.
Livezey, R.E. & Chen, W.Y. (1983) Mon. Weather Rev. 111:46-59.
"""

import math
import numpy as np
import pandas as pd
from scipy.stats import binom, norm as scipy_norm
from .config import ALPHA_005, ALPHA_001
from .trend_tests import standard_mk


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Walker (1914) Binomial Field Significance Test                         ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def walker_test(n_stations: int, n_sig: int, alpha: float = 0.05) -> dict:
    """
    Walker (1914) field significance test.

    H0: proportion of significant local tests <= alpha under independence.
    Uses a one-sided binomial test:

        P(X >= n_sig | n = n_stations, p = alpha)

    where X ~ Binomial(n_stations, alpha) under the null.

    Parameters
    ----------
    n_stations : total number of stations (trials)
    n_sig      : observed number of significant local tests
    alpha      : local significance level (default 0.05)

    Returns
    -------
    dict with keys:
      n_stations       : int
      n_sig            : int
      alpha            : float
      expected         : float   — n_stations * alpha
      p_walker         : float   — P(X >= n_sig)
      field_significant: bool    — p_walker < alpha
      fraction_sig     : float   — n_sig / n_stations
    """
    if n_stations < 1:
        return {
            "n_stations":        n_stations,
            "n_sig":             n_sig,
            "alpha":             alpha,
            "expected":          np.nan,
            "p_walker":          np.nan,
            "field_significant": False,
            "fraction_sig":      np.nan,
        }

    expected = n_stations * alpha

    # P(X >= n_sig) = 1 - P(X <= n_sig - 1)  = binom.sf(n_sig - 1, n, p)
    p_walker = float(binom.sf(n_sig - 1, n_stations, alpha))
    # clip to [0,1] for numerical safety
    p_walker = max(0.0, min(1.0, p_walker))

    return {
        "n_stations":        int(n_stations),
        "n_sig":             int(n_sig),
        "alpha":             float(alpha),
        "expected":          round(float(expected), 3),
        "p_walker":          round(p_walker, 6),
        "field_significant": p_walker < alpha,
        "fraction_sig":      round(float(n_sig) / float(n_stations), 4),
    }


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Livezey-Chen (1983) Monte Carlo Field Significance Test                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def livezey_chen_mc(series_dict: dict, alpha: float = 0.05,
                    n_perm: int = 1000, seed: int = 42) -> dict:
    """
    Livezey-Chen (1983) field significance via Monte Carlo permutation.

    Parameters
    ----------
    series_dict : {station_name: np.ndarray of annual values}
                  NaN values are dropped before testing within standard_mk.
    alpha       : local significance level (default 0.05)
    n_perm      : number of Monte Carlo permutations (default 1000)
    seed        : random seed for reproducibility (default 42)

    Algorithm
    ---------
    1. S_obs = fraction of stations whose standard_mk p-value < alpha.
    2. For each of n_perm permutations:
       a. Independently permute each station's time series.
       b. Run standard_mk on each permuted series.
       c. Record fraction with p < alpha.
    3. p_field_LC = fraction of MC draws >= S_obs.

    Returns
    -------
    dict with keys:
      S_obs             : float  — observed fraction of significant stations
      n_sig_obs         : int    — observed count of significant stations
      n_stations        : int    — total stations with valid data
      null_mean         : float  — mean of null distribution
      null_std          : float  — std  of null distribution
      null_95th         : float  — 95th percentile of null distribution
      p_field_LC        : float  — Monte Carlo p-value
      field_significant : bool   — p_field_LC < alpha
      n_perm            : int
      null_distribution : np.ndarray  — full array of MC fraction values
    """
    rng = np.random.default_rng(seed)

    # Build list of valid (name, array) pairs
    station_arrays = []
    for name, arr in series_dict.items():
        a = np.asarray(arr, dtype=float)
        a = a[~np.isnan(a)]
        if len(a) >= 4:
            station_arrays.append(a)

    n_stations = len(station_arrays)

    if n_stations == 0:
        null_dist = np.zeros(n_perm)
        return {
            "S_obs":              0.0,
            "n_sig_obs":          0,
            "n_stations":         0,
            "null_mean":          0.0,
            "null_std":           0.0,
            "null_95th":          0.0,
            "p_field_LC":         1.0,
            "field_significant":  False,
            "n_perm":             n_perm,
            "null_distribution":  null_dist,
        }

    # Step 1: Observed fraction of significant tests
    n_sig_obs = sum(
        1 for a in station_arrays
        if standard_mk(a).get("p_value", 1.0) < alpha
    )
    S_obs = float(n_sig_obs) / float(n_stations)

    # Step 2: Monte Carlo null distribution
    null_fracs = np.empty(n_perm, dtype=float)
    for b in range(n_perm):
        count = 0
        for a in station_arrays:
            a_perm = rng.permutation(a)
            res = standard_mk(a_perm)
            if res.get("p_value", 1.0) < alpha:
                count += 1
        null_fracs[b] = float(count) / float(n_stations)

    # Step 3: MC p-value = fraction of draws >= S_obs
    p_field_LC = float(np.mean(null_fracs >= S_obs))
    p_field_LC = max(1.0 / n_perm, min(1.0, p_field_LC))   # floor at 1/n_perm

    return {
        "S_obs":              round(S_obs, 4),
        "n_sig_obs":          int(n_sig_obs),
        "n_stations":         int(n_stations),
        "null_mean":          round(float(np.mean(null_fracs)), 4),
        "null_std":           round(float(np.std(null_fracs)),  4),
        "null_95th":          round(float(np.percentile(null_fracs, 95)), 4),
        "p_field_LC":         round(p_field_LC, 6),
        "field_significant":  p_field_LC < alpha,
        "n_perm":             int(n_perm),
        "null_distribution":  null_fracs,
    }


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  field_sig_summary — convenience wrapper for all temporal scales        ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def field_sig_summary(scales: dict, stns: list,
                      alpha: float = 0.05,
                      n_perm: int = 1000) -> pd.DataFrame:
    """
    Run Walker + Livezey-Chen field significance for each temporal scale.

    Parameters
    ----------
    scales  : dict with keys "annual", "wet", "dry" → pd.DataFrame (columns=stations)
    stns    : list of station identifiers
    alpha   : local significance level (default 0.05)
    n_perm  : number of Monte Carlo permutations for Livezey-Chen (default 1000)

    Returns
    -------
    DataFrame with one row per temporal scale (annual, wet, dry) and columns:
      Scale, N_stations, N_sig_MK, N_sig_MMK,
      Frac_sig_MK, Frac_sig_MMK,
      Walker_p_MK, Walker_sig_MK,
      LC_S_obs_MK, LC_p_MK, LC_sig_MK,
      LC_null_mean_MK, LC_null_95th_MK
    """
    from .trend_tests import modified_mk  # local import to avoid circular at module level

    rows = []
    scale_keys = ["annual", "wet", "dry"]

    for sk in scale_keys:
        df_s = scales[sk]

        # Build per-station series dicts for MK and MMK
        mk_series  = {}
        mmk_series = {}
        for stn in [str(s) for s in stns]:
            if stn not in df_s.columns:
                continue
            arr = df_s[stn].dropna().values.astype(float)
            if len(arr) >= 4:
                mk_series[stn]  = arr
                mmk_series[stn] = arr

        n_stn = len(mk_series)
        if n_stn == 0:
            rows.append({
                "Scale":            sk,
                "N_stations":       0,
                "N_sig_MK":         0,
                "N_sig_MMK":        0,
                "Frac_sig_MK":      np.nan,
                "Frac_sig_MMK":     np.nan,
                "Walker_p_MK":      np.nan,
                "Walker_sig_MK":    False,
                "LC_S_obs_MK":      np.nan,
                "LC_p_MK":          np.nan,
                "LC_sig_MK":        False,
                "LC_null_mean_MK":  np.nan,
                "LC_null_95th_MK":  np.nan,
            })
            continue

        # Count significant stations: Standard MK
        n_sig_mk = sum(
            1 for a in mk_series.values()
            if standard_mk(a).get("p_value", 1.0) < alpha
        )

        # Count significant stations: Modified MK
        n_sig_mmk = sum(
            1 for a in mmk_series.values()
            if modified_mk(a).get("p_value", 1.0) < alpha
        )

        # Walker test for Standard MK
        wt = walker_test(n_stn, n_sig_mk, alpha=alpha)

        # Livezey-Chen for Standard MK
        lc = livezey_chen_mc(mk_series, alpha=alpha, n_perm=n_perm)

        rows.append({
            "Scale":            sk,
            "N_stations":       n_stn,
            "N_sig_MK":         n_sig_mk,
            "N_sig_MMK":        n_sig_mmk,
            "Frac_sig_MK":      round(float(n_sig_mk)  / float(n_stn), 4),
            "Frac_sig_MMK":     round(float(n_sig_mmk) / float(n_stn), 4),
            "Walker_p_MK":      wt["p_walker"],
            "Walker_sig_MK":    wt["field_significant"],
            "LC_S_obs_MK":      lc["S_obs"],
            "LC_p_MK":          lc["p_field_LC"],
            "LC_sig_MK":        lc["field_significant"],
            "LC_null_mean_MK":  lc["null_mean"],
            "LC_null_95th_MK":  lc["null_95th"],
        })

    return pd.DataFrame(rows)
