"""
rta.batch — Batch execution of trend tests across stations × temporal scales.

Extends the v3 run_all / build_comparison workflow to support all four
Mann-Kendall variants: Standard MK, Modified MK, PW-MK, TFPW-MK.
"""

import numpy as np
import pandas as pd
from .config import MIN_N, SCALE_META, ALPHA_005
from .autocorr import lag_k_autocorr, is_sig_autocorr
from .trend_tests import standard_mk, modified_mk, pw_mk, tfpw_mk, sens_slope


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Method function map                                                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝

METHOD_FN = {
    "Standard MK": standard_mk,
    "Modified MK": modified_mk,
    "PW-MK":       pw_mk,
    "TFPW-MK":     tfpw_mk,
}

_ALL_METHODS = ["Standard MK", "Modified MK", "PW-MK", "TFPW-MK"]


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  run_all — all stations × scales × methods                              ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def run_all(scales: dict, stns: list, smap: dict,
            methods: list = None) -> pd.DataFrame:
    """
    Run all 4 methods for all stations × temporal scales.

    Parameters
    ----------
    scales  : dict with keys "annual", "wet", "dry" → pd.DataFrame (columns=stations)
    stns    : list of station identifiers (matched against DataFrame columns)
    smap    : dict mapping station id → short code / label
    methods : list of method names to run (default: all 4).
              Valid: "Standard MK", "Modified MK", "PW-MK", "TFPW-MK"

    Returns
    -------
    Tidy DataFrame with columns:
      Station, Code, Scale, Scale_Label, Method,
      rho_1, Sig_AC, N, S, Var_S, Var_S_adj, n_eff,
      Z, tau, p_value, Trend, sig_05, sig_01,
      Slope_Q, Slope_lo, Slope_hi,
      pw_applied, rho_1_used, beta_initial
    """
    if methods is None:
        methods = _ALL_METHODS

    # Validate method names
    unknown = [m for m in methods if m not in METHOD_FN]
    if unknown:
        raise ValueError(f"Unknown method(s): {unknown}. "
                         f"Valid choices: {list(METHOD_FN.keys())}")

    rows = []
    scale_keys = ["annual", "wet", "dry"]

    for sk in scale_keys:
        df_s = scales[sk]
        meta = SCALE_META[sk]

        for stn in [str(s) for s in stns]:
            if stn not in df_s.columns:
                continue
            arr = df_s[stn].dropna().values.astype(float)
            if len(arr) < MIN_N:
                continue

            # Lag-1 autocorrelation (always on original series)
            r1     = lag_k_autocorr(arr)
            sig_ac = is_sig_autocorr(r1, len(arr))

            for method_name in methods:
                method_fn = METHOD_FN[method_name]
                res = method_fn(arr)

                rows.append({
                    "Station":      stn,
                    "Code":         smap.get(stn, stn),
                    "Scale":        sk,
                    "Scale_Label":  meta["label"],
                    "Method":       method_name,
                    "rho_1":        round(r1, 4) if not np.isnan(r1) else np.nan,
                    "Sig_AC":       sig_ac,
                    "N":            res.get("n",           np.nan),
                    "S":            res.get("S",           np.nan),
                    "Var_S":        res.get("Var_S",       np.nan),
                    "Var_S_adj":    res.get("Var_S_adj",   np.nan),
                    "n_eff":        res.get("n_eff",       np.nan),
                    "Z":            res.get("Z",           np.nan),
                    "tau":          res.get("tau",         np.nan),
                    "p_value":      res.get("p_value",     np.nan),
                    "Trend":        res.get("trend",       "—"),
                    "sig_05":       res.get("sig_05",      False),
                    "sig_01":       res.get("sig_01",      False),
                    "Slope_Q":      res.get("slope_Q",     np.nan),
                    "Slope_lo":     res.get("slope_lo",    np.nan),
                    "Slope_hi":     res.get("slope_hi",    np.nan),
                    "pw_applied":   res.get("pw_applied",  np.nan),
                    "rho_1_used":   res.get("rho_1_used",  np.nan),
                    "beta_initial": res.get("beta_initial",np.nan),
                })

    return pd.DataFrame(rows)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  build_comparison — MK vs MMK (v3-compatible)                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def build_comparison(trend_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build MK vs MMK comparison table (v3-compatible, 2-method).

    Groups by (Station, Scale) and pairs Standard MK with Modified MK rows.
    Returns one row per (Station × Scale) with side-by-side statistics and
    delta_Z / delta_p / Agree columns.
    """
    rows = []
    for (stn, sk), grp in trend_df.groupby(["Station", "Scale"]):
        mk  = grp[grp["Method"] == "Standard MK"].squeeze()
        mmk = grp[grp["Method"] == "Modified MK"].squeeze()
        if isinstance(mk,  pd.DataFrame) or isinstance(mmk, pd.DataFrame):
            continue
        dZ    = float(mmk["Z"])       - float(mk["Z"])
        dp    = float(mmk["p_value"]) - float(mk["p_value"])
        agree = mk["Trend"] == mmk["Trend"]
        rows.append({
            "Station":    stn,
            "Code":       mk.get("Code", stn),
            "Scale":      sk,
            "Scale_Label":mk.get("Scale_Label", ""),
            "rho_1":      mk.get("rho_1", np.nan),
            "Sig_AC":     bool(mk.get("Sig_AC", False)),
            "MK_Z":       mk["Z"],       "MK_p":      mk["p_value"],
            "MK_Trend":   mk["Trend"],   "MK_sig05":  mk["sig_05"],
            "MMK_Z":      mmk["Z"],      "MMK_p":     mmk["p_value"],
            "MMK_Trend":  mmk["Trend"],  "MMK_sig05": mmk["sig_05"],
            "delta_Z":    round(dZ, 4),
            "delta_p":    round(dp, 6),
            "Agree":      agree,
            "MK_Slope":   mk["Slope_Q"],
            "MMK_Slope":  mmk["Slope_Q"],
            "Slope_lo":   mmk["Slope_lo"],
            "Slope_hi":   mmk["Slope_hi"],
        })
    return pd.DataFrame(rows)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  build_4method_comparison — wide 4-method table                         ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def _sig_label(sig_05: bool, sig_01: bool) -> str:
    """Return '**', '*', or 'ns' significance label."""
    if sig_01:  return "**"
    if sig_05:  return "*"
    return "ns"


def build_4method_comparison(trend_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build 4-method wide comparison table for each (Station, Scale).

    Columns
    -------
    Station, Code, Scale, Scale_Label, rho_1, Sig_AC,
    MK_Z,   MK_p,   MK_slope,   MK_sig,   MK_trend,
    MMK_Z,  MMK_p,  MMK_slope,  MMK_sig,  MMK_trend,
    PW_Z,   PW_p,   PW_slope,   PW_sig,   PW_trend,
    TFPW_Z, TFPW_p, TFPW_slope, TFPW_sig, TFPW_trend,
    dZ_MMK,    dZ_PW,    dZ_TFPW,
    dSlope_MMK,dSlope_PW,dSlope_TFPW,
    all_agree     (bool: all 4 non-NaN Z values same sign/direction),
    n_sig_methods (int : number of methods with p < 0.05)

    Notes
    -----
    sig_* is formatted as "**" / "*" / "ns".
    dZ     = method_Z    - MK_Z
    dSlope = method_slope - MK_slope
    """
    # Method prefixes and their lookup keys in trend_df
    _methods = [
        ("Standard MK", "MK"),
        ("Modified MK", "MMK"),
        ("PW-MK",       "PW"),
        ("TFPW-MK",     "TFPW"),
    ]

    rows = []
    for (stn, sk), grp in trend_df.groupby(["Station", "Scale"]):
        # Pull each method row — tolerate missing methods gracefully
        m_rows = {}
        for method_name, prefix in _methods:
            sub = grp[grp["Method"] == method_name]
            m_rows[prefix] = sub.squeeze() if len(sub) == 1 else None

        mk_row = m_rows.get("MK")
        if mk_row is None:
            continue  # Need at least Standard MK

        def _get(row, key, default=np.nan):
            if row is None:
                return default
            val = row.get(key, default) if hasattr(row, "get") else default
            return val

        # Base identifiers come from MK row
        row_out = {
            "Station":    stn,
            "Code":       _get(mk_row, "Code", stn),
            "Scale":      sk,
            "Scale_Label":_get(mk_row, "Scale_Label", ""),
            "rho_1":      _get(mk_row, "rho_1"),
            "Sig_AC":     bool(_get(mk_row, "Sig_AC", False)),
        }

        mk_z     = _get(mk_row, "Z")
        mk_slope = _get(mk_row, "Slope_Q")

        for method_name, prefix in _methods:
            r = m_rows.get(prefix)
            z     = _get(r, "Z")
            p     = _get(r, "p_value")
            slope = _get(r, "Slope_Q")
            sig05 = bool(_get(r, "sig_05", False))
            sig01 = bool(_get(r, "sig_01", False))
            trend = _get(r, "Trend", "—")

            row_out[f"{prefix}_Z"]     = z
            row_out[f"{prefix}_p"]     = p
            row_out[f"{prefix}_slope"] = slope
            row_out[f"{prefix}_sig"]   = _sig_label(sig05, sig01)
            row_out[f"{prefix}_trend"] = trend

        # Delta columns (relative to Standard MK)
        for method_name, prefix in [("Modified MK","MMK"),("PW-MK","PW"),("TFPW-MK","TFPW")]:
            r = m_rows.get(prefix)
            z     = _get(r, "Z")
            slope = _get(r, "Slope_Q")
            row_out[f"dZ_{prefix}"]     = (
                round(float(z)     - float(mk_z),     4)
                if not (np.isnan(float(z))     if isinstance(z,     float) else np.isnan(z))
                   and not (np.isnan(float(mk_z)) if isinstance(mk_z, float) else np.isnan(mk_z))
                else np.nan
            )
            row_out[f"dSlope_{prefix}"] = (
                round(float(slope) - float(mk_slope), 4)
                if not (np.isnan(float(slope))     if isinstance(slope,     float) else np.isnan(slope))
                   and not (np.isnan(float(mk_slope)) if isinstance(mk_slope, float) else np.isnan(mk_slope))
                else np.nan
            )

        # all_agree: all 4 methods with valid Z agree on direction (sign)
        z_vals = [_get(m_rows.get(p), "Z") for _, p in _methods]
        z_valid = [float(z) for z in z_vals
                   if not (np.isnan(float(z)) if isinstance(z, float) else np.isnan(z))]
        if len(z_valid) >= 2:
            signs = [np.sign(z) for z in z_valid]
            row_out["all_agree"] = bool(len(set(signs)) == 1 and signs[0] != 0)
        else:
            row_out["all_agree"] = False

        # n_sig_methods: count of methods with p < 0.05
        p_vals = [_get(m_rows.get(p), "p_value") for _, p in _methods]
        n_sig = sum(
            1 for pv in p_vals
            if not (np.isnan(float(pv)) if isinstance(pv, float) else np.isnan(pv))
            and float(pv) < ALPHA_005
        )
        row_out["n_sig_methods"] = n_sig

        rows.append(row_out)

    return pd.DataFrame(rows)
