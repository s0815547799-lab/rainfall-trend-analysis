"""validation.metrics — KGE, NSE, PBIAS per station; Raw vs BC improvement.

All three metrics (KGE, NSE, PBIAS) are computed on the same common-year
window (obs ∩ raw_mme ∩ bc_mme) so Raw and BC statistics are strictly
comparable.

KGE improvement is reported as absolute ΔKGE (BC − Raw) because KGE can be
negative, making percentage-of-baseline meaningless.  PBIAS improvement is
reported as the reduction in absolute bias (%).
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# scalar metric functions
# ---------------------------------------------------------------------------

def kge(obs: np.ndarray, sim: np.ndarray) -> float:
    """Kling-Gupta Efficiency (Gupta et al. 2009)."""
    m = np.isfinite(obs) & np.isfinite(sim)
    o, s = obs[m], sim[m]
    if len(o) < 2:
        return np.nan
    std_o = np.std(o, ddof=0)
    std_s = np.std(s, ddof=0)
    r = np.corrcoef(o, s)[0, 1] if std_o > 0 and std_s > 0 else np.nan
    alpha = std_s / std_o if std_o > 0 else np.nan
    beta = np.mean(s) / np.mean(o) if np.mean(o) != 0 else np.nan
    if any(np.isnan(v) for v in [r, alpha, beta]):
        return np.nan
    return float(1 - np.sqrt((r - 1) ** 2 + (alpha - 1) ** 2 + (beta - 1) ** 2))


def nse(obs: np.ndarray, sim: np.ndarray) -> float:
    """Nash-Sutcliffe Efficiency."""
    m = np.isfinite(obs) & np.isfinite(sim)
    o, s = obs[m], sim[m]
    if len(o) < 2:
        return np.nan
    denom = np.sum((o - np.mean(o)) ** 2)
    if denom == 0:
        return np.nan
    return float(1 - np.sum((s - o) ** 2) / denom)


def pbias(obs: np.ndarray, sim: np.ndarray) -> float:
    """Percent bias (%)."""
    m = np.isfinite(obs) & np.isfinite(sim)
    o, s = obs[m], sim[m]
    total_obs = np.sum(o)
    if total_obs == 0:
        return np.nan
    return float(100 * np.sum(s - o) / total_obs)


# ---------------------------------------------------------------------------
# per-station validation table
# ---------------------------------------------------------------------------

def validation_metrics(obs_year: pd.DataFrame, raw_mme: pd.DataFrame,
                       bc_mme: pd.DataFrame, season: str = "Annual") -> pd.DataFrame:
    """Per-station KGE/NSE/PBIAS for Raw MME and BC-MME vs Observed.

    Uses the three-way common year index (obs ∩ raw ∩ bc) so all six metric
    values in each row are computed on identical samples.
    """
    o = (obs_year[obs_year.season == season]
         .groupby(["station", "year"]).rainfall.mean()
         .reset_index())

    rows = []
    for st in o.station.unique():
        oo = o[o.station == st].set_index("year").rainfall

        def _series(mme: pd.DataFrame) -> pd.Series:
            sub = mme[(mme.station == st) & (mme.season == season)
                      & (mme.scenario == "historical")]
            return sub.set_index("year")["mean"]

        rs = _series(raw_mme)
        bs = _series(bc_mme)

        # Three-way intersection: all metrics computed on the same years
        idx = oo.index.intersection(rs.index).intersection(bs.index)
        if len(idx) < 2:
            log.debug("station %s season %s: only %d common years, skipping", st, season, len(idx))
            continue

        ov = oo.loc[idx].to_numpy()
        rv = rs.loc[idx].to_numpy()
        bv = bs.loc[idx].to_numpy()

        kge_raw = kge(ov, rv)
        kge_bc  = kge(ov, bv)
        rows.append({
            "station":    st,
            "season":     season,
            "n_years":    len(idx),
            "KGE_Raw":    kge_raw,
            "KGE_BC":     kge_bc,
            "NSE_Raw":    nse(ov, rv),
            "NSE_BC":     nse(ov, bv),
            "PBIAS_Raw":  pbias(ov, rv),
            "PBIAS_BC":   pbias(ov, bv),
        })

    df = pd.DataFrame(rows)
    if len(df):
        # Absolute ΔKGE — valid regardless of baseline sign
        df["ΔKGE"] = (df.KGE_BC - df.KGE_Raw).round(3)

        # PBIAS improvement: reduction in |bias|, expressed as a fraction of
        # |Raw bias|.  Only meaningful when Raw bias ≠ 0.
        raw_abs = df.PBIAS_Raw.abs()
        df["PBIAS_Improvement_%"] = (
            (raw_abs - df.PBIAS_BC.abs()) / raw_abs.replace(0, np.nan) * 100
        ).round(1)

    return df
