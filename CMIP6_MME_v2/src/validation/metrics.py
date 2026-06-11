"""validation.metrics — KGE, NSE, PBIAS per station; Raw vs BC improvement.

All metrics (KGE, NSE, PBIAS) are computed on the three-way common year
index (obs ∩ raw_mme ∩ bc_mme) so Raw and BC statistics are directly
comparable on identical samples.

Improvement reporting:
  KGE  → ΔKGE (absolute difference, valid for negative baselines)
  PBIAS → PBIAS_Improvement_% (reduction in |bias| relative to |Raw bias|)

References:
  Gupta et al. (2009) Decomposition of the mean squared error and NSE.
  Nash & Sutcliffe (1970) River flow forecasting through conceptual models.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


# ── Scalar metric functions ───────────────────────────────────────────────────

def kge(obs: np.ndarray, sim: np.ndarray) -> float:
    """Kling-Gupta Efficiency (Gupta et al. 2009).  Range: (−∞, 1], perfect = 1.

    Uses sample std (ddof=1) per CLAUDE.md §12.10 mandate.  Note: α = σ_s/σ_o
    is a ratio so the KGE value is numerically identical for ddof=0 or ddof=1;
    ddof=1 is used for formal consistency with the Gupta et al. formulation as
    required by the project scientific standards.
    """
    m = np.isfinite(obs) & np.isfinite(sim)
    o, s = obs[m], sim[m]
    if len(o) < 2:
        return np.nan
    std_o = np.std(o, ddof=1)
    std_s = np.std(s, ddof=1)
    if std_o == 0:
        return np.nan   # undefined when observations are constant
    r     = np.corrcoef(o, s)[0, 1] if std_s > 0 else np.nan
    alpha = std_s / std_o
    mu_o  = np.mean(o)
    beta  = np.mean(s) / mu_o if mu_o != 0 else np.nan
    if any(np.isnan(v) for v in [r, alpha, beta]):
        return np.nan
    return float(1 - np.sqrt((r - 1) ** 2 + (alpha - 1) ** 2 + (beta - 1) ** 2))


def nse(obs: np.ndarray, sim: np.ndarray) -> float:
    """Nash-Sutcliffe Efficiency.  Range: (−∞, 1], perfect = 1."""
    m = np.isfinite(obs) & np.isfinite(sim)
    o, s = obs[m], sim[m]
    if len(o) < 2:
        return np.nan
    denom = np.sum((o - np.mean(o)) ** 2)
    if denom == 0:
        return np.nan
    return float(1 - np.sum((s - o) ** 2) / denom)


def pbias(obs: np.ndarray, sim: np.ndarray) -> float:
    """Percent Bias (%).  Perfect = 0, positive = model over-estimates."""
    m = np.isfinite(obs) & np.isfinite(sim)
    o, s = obs[m], sim[m]
    total = np.sum(o)
    if total == 0:
        return np.nan
    return float(100 * np.sum(s - o) / total)


# ── Per-station validation table ──────────────────────────────────────────────

def validation_metrics(obs_year: pd.DataFrame,
                       raw_mme: pd.DataFrame,
                       bc_mme:  pd.DataFrame,
                       season:  str = "Annual",
                       min_years: int = 2,
                       ) -> pd.DataFrame:
    """Per-station KGE/NSE/PBIAS for Raw MME and BC-MME vs Observed.

    Uses the three-way common year index (obs ∩ raw ∩ bc) so all six metric
    values in each row are computed on identical samples.

    Parameters
    ----------
    obs_year   : output of observed_yearly() — station×year×season
    raw_mme    : build_mme() output filtered to dataset='Raw'
    bc_mme     : build_mme() output filtered to dataset='BC'
    season     : "Annual", "Wet", or "Dry"
    min_years  : minimum common years to compute metrics (default 2)
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

        # Three-way intersection: identical sample for all metrics
        idx = oo.index.intersection(rs.index).intersection(bs.index)
        if len(idx) < min_years:
            log.debug("station %s season %s: only %d common years, skipping",
                      st, season, len(idx))
            continue

        ov = oo.loc[idx].to_numpy()
        rv = rs.loc[idx].to_numpy()
        bv = bs.loc[idx].to_numpy()

        kge_raw = kge(ov, rv)
        kge_bc  = kge(ov, bv)
        rows.append({
            "station":   st,
            "season":    season,
            "n_years":   len(idx),
            "KGE_Raw":   kge_raw,
            "KGE_BC":    kge_bc,
            "NSE_Raw":   nse(ov, rv),
            "NSE_BC":    nse(ov, bv),
            "PBIAS_Raw": pbias(ov, rv),
            "PBIAS_BC":  pbias(ov, bv),
        })

    df = pd.DataFrame(rows)
    if len(df):
        # Absolute ΔKGE — valid regardless of baseline sign
        df["ΔKGE"] = (df.KGE_BC - df.KGE_Raw).round(3)
        # PBIAS improvement: reduction in |bias| / |Raw bias| × 100
        raw_abs = df.PBIAS_Raw.abs()
        df["PBIAS_Improvement_%"] = (
            (raw_abs - df.PBIAS_BC.abs()) / raw_abs.replace(0, np.nan) * 100
        ).round(1)

    log.info("validation_metrics [%s]: %d stations, %s",
             season, len(df),
             "OK" if len(df) else "NO DATA")
    return df
