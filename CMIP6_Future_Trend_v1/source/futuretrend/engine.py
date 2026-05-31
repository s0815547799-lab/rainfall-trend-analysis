"""
futuretrend.engine — future-trend orchestration (Modules 1–6).

Runs the FROZEN trend stack (MK, Lag-K MMK, PW-MK, TFPW-MK, Sen) on FUTURE yearly
series (per variable × scenario × window × station × model), then derives
agreement (independent GCMs only, MME excluded), delta-based uncertainty, and
hotspot classes. No statistical re-implementation; association language only.
"""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd

from .trend_tests import standard_mk, pw_mk, tfpw_mk, sens_slope
from .lag_k_mmk import lag_k_mmk

log = logging.getLogger(__name__)

HOTSPOT_CLASSES = ["Low", "Moderate", "High", "Very High", "Extreme"]


def _trend_one(series: np.ndarray) -> dict:
    """Frozen 5-method stack on one yearly series."""
    x = series[~np.isnan(series)]
    if len(x) < 5:
        return {}
    mk = standard_mk(x); mmk = lag_k_mmk(x)
    pw = pw_mk(x); tf = tfpw_mk(x)
    q, _, _ = sens_slope(x)
    z = mmk.get("Z", mmk.get("z", np.nan))
    p = mmk.get("p_value", np.nan)
    return {
        "n": int(len(x)),
        "sen_slope": float(q) if q == q else np.nan,
        "direction": "increase" if q > 0 else ("decrease" if q < 0 else "none"),
        "z_mmk": float(z) if z == z else np.nan,
        "p_mmk": float(p) if p == p else np.nan,
        "significant": bool(p < 0.05) if p == p else False,
        "z_mk": float(mk.get("Z", np.nan)),
        "p_pw": float(pw.get("p_value", np.nan)),
        "p_tfpw": float(tf.get("p_value", np.nan)),
    }


def compute_trends(yearly: pd.DataFrame, value_col: str = "value") -> pd.DataFrame:
    """yearly: [variable, scenario, window, station, model, year, value] → trend rows."""
    keys = ["variable", "scenario", "window", "station", "model"]
    rows = []
    for key, g in yearly.groupby(keys, sort=False):
        g = g.sort_values("year")
        res = _trend_one(g[value_col].to_numpy(dtype=float))
        if res:
            rows.append(dict(zip(keys, key)) | res)
    out = pd.DataFrame(rows)
    log.info("compute_trends: %d trend rows", len(out))
    return out


def trend_agreement(trends: pd.DataFrame) -> pd.DataFrame:
    """Sign agreement across INDEPENDENT GCMs (MME excluded, Rule 2)."""
    t = trends[trends.model != "MME"]
    keys = ["variable", "scenario", "window", "station"]
    rows = []
    for key, g in t.groupby(keys):
        s = g.sen_slope.dropna()
        n = len(s)
        if n == 0:
            continue
        n_inc = int((s > 0).sum()); n_dec = int((s < 0).sum())
        frac = max(n_inc, n_dec) / n
        cls = "strong" if frac >= 0.80 else ("moderate" if frac >= 0.66 else "weak")
        rows.append(dict(zip(keys, key)) | {
            "n_models": n, "n_increase": n_inc, "n_decrease": n_dec,
            "agreement_fraction": round(frac, 3),
            "dominant_direction": "increase" if n_inc >= n_dec else "decrease",
            "agreement_class": cls})
    return pd.DataFrame(rows)


def trend_uncertainty(trends: pd.DataFrame) -> pd.DataFrame:
    """Delta-based spread of per-model Sen slope (MME excluded, Rule 2)."""
    t = trends[trends.model != "MME"]
    keys = ["variable", "scenario", "window", "station"]
    rows = []
    for key, g in t.groupby(keys):
        s = g.sen_slope.dropna().to_numpy()
        if s.size == 0:
            continue
        q25, q75 = np.percentile(s, [25, 75])
        rows.append(dict(zip(keys, key)) | {
            "n_models": int(s.size), "mean_slope": float(np.mean(s)),
            "sd_slope": float(np.std(s, ddof=1)) if s.size > 1 else 0.0,
            "iqr_slope": float(q75 - q25)})
    return pd.DataFrame(rows)


def trend_hotspots(agreement: pd.DataFrame, uncertainty: pd.DataFrame) -> pd.DataFrame:
    """Hotspot class from |mean slope| × agreement (quantile-based, per variable)."""
    m = agreement.merge(uncertainty, on=["variable", "scenario", "window", "station"], how="inner")
    m["abs_slope"] = m["mean_slope"].abs()
    out = []
    for var, g in m.groupby("variable"):
        q = g["abs_slope"].quantile([0.2, 0.4, 0.6, 0.8]).to_dict()
        def cls(v, frac):
            base = (HOTSPOT_CLASSES[0] if v <= q[0.2] else HOTSPOT_CLASSES[1] if v <= q[0.4]
                    else HOTSPOT_CLASSES[2] if v <= q[0.6] else HOTSPOT_CLASSES[3] if v <= q[0.8]
                    else HOTSPOT_CLASSES[4])
            # downgrade one class if agreement weak
            if frac < 0.66 and base != "Low":
                return HOTSPOT_CLASSES[HOTSPOT_CLASSES.index(base) - 1]
            return base
        g = g.copy()
        g["hotspot_class"] = [cls(v, f) for v, f in zip(g.abs_slope, g.agreement_fraction)]
        out.append(g)
    return pd.concat(out, ignore_index=True)[
        ["variable", "scenario", "window", "station", "mean_slope", "abs_slope",
         "agreement_fraction", "dominant_direction", "hotspot_class"]]
