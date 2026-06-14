"""validation.metrics — climatological validation of (BC-)MME vs observed.

SCIENTIFIC BASIS (revised v3.7)
-------------------------------
CMIP6 *historical* simulations (realization r1i1p1f1) are FREE-RUNNING: their
internal interannual variability is **not** phase-locked to the observed
1981–2014 chronology. Therefore any metric that pairs observed year Y with
model year Y — Pearson r, KGE, NSE, a Taylor-diagram azimuth — is undefined as
a *skill* measure; it estimates random phase agreement and collapses toward
r≈0 / NSE<0 regardless of how good the model climatology is. (Confirmed in the
v3.6 run: median NSE_BC=-0.03, KGE_BC=+0.06, yet median |PBIAS_BC|=1.4%.)

A bias-corrected free-running GCM must instead be validated on the quantities
it is *designed* to reproduce — its CLIMATOLOGICAL DISTRIBUTION:

    • mean bias            → PBIAS (%)            [perfect = 0]
    • interannual variability ratio → SDratio = σ_sim/σ_obs   [perfect = 1]
    • distributional overlap → Perkins-style Skill Score PSS  [perfect = 1]
      (overlap of the obs vs sim histograms of the per-year totals)
    • distribution test    → two-sample KS statistic D + p    [diagnostic]

These are invariant to year ordering, so they are valid for free-running runs.

CIRCULARITY CAVEAT (must be reported in the manuscript)
-------------------------------------------------------
The BC product was calibrated to THIS observed record over THIS baseline
period. Metrics computed on the calibration period are therefore *consistency
checks*, not independent validation. Set `split_sample=(cal, val)` to evaluate
on a held-out sub-period, or report k-fold CV of the bias-correction upstream.
`validation_metrics` exposes `legacy_interannual=True` ONLY to reproduce the
old (invalid) KGE/NSE side-by-side so the difference is auditable.

References
----------
  Gupta et al. (2009), J. Hydrol. 377, 80–91.       (KGE definition)
  Nash & Sutcliffe (1970), J. Hydrol. 10, 282–290.  (NSE definition)
  Perkins et al. (2007), J. Climate 20, 4356–4376.  (PDF skill score)
  Maraun (2016), Curr. Clim. Change Rep.            (BC validation pitfalls)
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


# ── Distributional metric functions (order-invariant) ─────────────────────────

def pbias(obs: np.ndarray, sim: np.ndarray) -> float:
    """Percent bias (%). Perfect = 0; positive = model over-estimates."""
    m = np.isfinite(obs) & np.isfinite(sim)
    o, s = obs[m], sim[m]
    tot = np.sum(o)
    return float(100.0 * np.sum(s - o) / tot) if tot != 0 else np.nan


def sd_ratio(obs: np.ndarray, sim: np.ndarray) -> float:
    """Interannual variability ratio σ_sim/σ_obs (ddof=1). Perfect = 1.

    Order-invariant: measures whether the model reproduces the *magnitude* of
    year-to-year variability, not its timing."""
    m = np.isfinite(obs) & np.isfinite(sim)
    o, s = obs[m], sim[m]
    if len(o) < 2:
        return np.nan
    so = np.std(o, ddof=1)
    return float(np.std(s, ddof=1) / so) if so > 0 else np.nan


def perkins_ss(obs: np.ndarray, sim: np.ndarray, n_bins: int | None = None) -> float:
    """Perkins Skill Score: overlapping area of the two PDFs. Range [0,1], 1=identical.

    Histograms share common edges spanning both samples. With small annual
    samples (~30) this is coarse; it is a robust *distributional* agreement
    score, unaffected by year ordering."""
    m = np.isfinite(obs) & np.isfinite(sim)
    o, s = obs[m], sim[m]
    if len(o) < 5 or len(s) < 5:
        return np.nan
    lo, hi = float(min(o.min(), s.min())), float(max(o.max(), s.max()))
    if hi <= lo:
        return np.nan
    if n_bins is None:                       # Freedman–Diaconis-ish, capped
        n_bins = int(np.clip(np.sqrt(len(o)), 5, 20))
    edges = np.linspace(lo, hi, n_bins + 1)
    po, _ = np.histogram(o, bins=edges, density=False)
    ps, _ = np.histogram(s, bins=edges, density=False)
    po = po / po.sum(); ps = ps / ps.sum()
    return float(np.minimum(po, ps).sum())


def ks_stat(obs: np.ndarray, sim: np.ndarray) -> tuple[float, float]:
    """Two-sample Kolmogorov–Smirnov D and p-value (distribution-match diagnostic).

    Low D / high p ⇒ cannot reject equal distributions. Underpowered at n≈30,
    so reported as a diagnostic, not a pass/fail gate."""
    m1 = np.isfinite(obs); m2 = np.isfinite(sim)
    o, s = obs[m1], sim[m2]
    if len(o) < 5 or len(s) < 5:
        return np.nan, np.nan
    try:
        from scipy.stats import ks_2samp
        d, p = ks_2samp(o, s)
        return float(d), float(p)
    except Exception:
        # SciPy-free fallback: D only (no p-value)
        xs = np.sort(np.concatenate([o, s]))
        cdf_o = np.searchsorted(np.sort(o), xs, side="right") / len(o)
        cdf_s = np.searchsorted(np.sort(s), xs, side="right") / len(s)
        return float(np.max(np.abs(cdf_o - cdf_s))), np.nan


# ── Deprecated interannual metrics (free-running GCM ⇒ NOT valid skill) ────────

def _kge_interannual(obs: np.ndarray, sim: np.ndarray) -> float:
    """DEPRECATED. Year-matched KGE — invalid for free-running GCMs. Audit only."""
    m = np.isfinite(obs) & np.isfinite(sim)
    o, s = obs[m], sim[m]
    if len(o) < 2:
        return np.nan
    so, ss = np.std(o, ddof=1), np.std(s, ddof=1)
    if so == 0:
        return np.nan
    r = np.corrcoef(o, s)[0, 1] if ss > 0 else np.nan
    mo = np.mean(o)
    beta = np.mean(s) / mo if mo != 0 else np.nan
    if any(np.isnan(v) for v in (r, ss / so, beta)):
        return np.nan
    return float(1 - np.sqrt((r - 1) ** 2 + (ss / so - 1) ** 2 + (beta - 1) ** 2))


def _nse_interannual(obs: np.ndarray, sim: np.ndarray) -> float:
    """DEPRECATED. Year-matched NSE — invalid for free-running GCMs. Audit only."""
    m = np.isfinite(obs) & np.isfinite(sim)
    o, s = obs[m], sim[m]
    if len(o) < 2:
        return np.nan
    den = np.sum((o - np.mean(o)) ** 2)
    return float(1 - np.sum((s - o) ** 2) / den) if den != 0 else np.nan


# ── Public aliases (valid statistics; NOT used for free-running interannual skill) ──
# KGE and NSE are legitimate efficiency measures in general and are retained as
# importable utilities for unit-testing and for the optional legacy_interannual
# audit path. validation_metrics() does NOT use them by default, because their
# year-matched application to free-running GCMs is invalid (see module docstring).
kge = _kge_interannual
nse = _nse_interannual


# ── Per-station validation table ──────────────────────────────────────────────

def validation_metrics(obs_year: pd.DataFrame,
                       raw_mme: pd.DataFrame,
                       bc_mme:  pd.DataFrame,
                       season:  str = "Annual",
                       min_years: int = 10,
                       split_sample: tuple[tuple[int, int], tuple[int, int]] | None = None,
                       legacy_interannual: bool = False,
                       ) -> pd.DataFrame:
    """Climatological (order-invariant) validation of Raw/BC MME vs observed.

    Parameters
    ----------
    obs_year   : observed_yearly() output (station×year×season×rainfall).
    raw_mme,
    bc_mme     : build_mme() outputs filtered to dataset 'Raw' / 'BC'.
    season     : 'Annual' | 'Wet' | 'Dry'.
    min_years  : minimum common years required to report a station.
    split_sample : ((cal0,cal1),(val0,val1)) — if given, metrics are computed on
                   the VALIDATION window only (independent of the BC calibration
                   window). If None, metrics are calibration-period consistency
                   checks (state this in the manuscript).
    legacy_interannual : if True, also emit KGE_*/NSE_* (year-matched) flagged as
                   deprecated, so the invalid values can be compared.

    Returns
    -------
    One row per station with order-invariant skill for Raw and BC.
    """
    o = (obs_year[obs_year.season == season]
         .groupby(["station", "year"]).rainfall.mean().reset_index())

    val_win = split_sample[1] if split_sample else None

    def _clip(s: pd.Series) -> pd.Series:
        if val_win is None:
            return s
        v0, v1 = val_win
        return s[(s.index >= v0) & (s.index <= v1)]

    rows = []
    for st in o.station.unique():
        oo = _clip(o[o.station == st].set_index("year").rainfall)

        def _series(mme: pd.DataFrame) -> pd.Series:
            sub = mme[(mme.station == st) & (mme.season == season)
                      & (mme.scenario == "historical")]
            return _clip(sub.set_index("year")["mean"])

        rs, bs = _series(raw_mme), _series(bc_mme)
        idx = oo.index.intersection(rs.index).intersection(bs.index)
        if len(idx) < min_years:
            log.debug("station %s [%s]: %d common years < %d — skipped",
                      st, season, len(idx), min_years)
            continue
        ov, rv, bv = oo.loc[idx].to_numpy(), rs.loc[idx].to_numpy(), bs.loc[idx].to_numpy()

        d_raw, p_raw = ks_stat(ov, rv)
        d_bc,  p_bc  = ks_stat(ov, bv)
        row = {
            "station": st, "season": season, "n_years": len(idx),
            "obs_mean":   round(float(np.nanmean(ov)), 2),
            "PBIAS_Raw":  round(pbias(ov, rv), 2),
            "PBIAS_BC":   round(pbias(ov, bv), 2),
            "SDratio_Raw": round(sd_ratio(ov, rv), 3),
            "SDratio_BC":  round(sd_ratio(ov, bv), 3),
            "PSS_Raw":    round(perkins_ss(ov, rv), 3),
            "PSS_BC":     round(perkins_ss(ov, bv), 3),
            "KS_D_Raw":   round(d_raw, 3) if np.isfinite(d_raw) else np.nan,
            "KS_p_Raw":   round(p_raw, 3) if np.isfinite(p_raw) else np.nan,
            "KS_D_BC":    round(d_bc, 3)  if np.isfinite(d_bc)  else np.nan,
            "KS_p_BC":    round(p_bc, 3)  if np.isfinite(p_bc)  else np.nan,
        }
        if legacy_interannual:
            row.update({
                "KGE_Raw_DEPRECATED": round(_kge_interannual(ov, rv), 3),
                "KGE_BC_DEPRECATED":  round(_kge_interannual(ov, bv), 3),
                "NSE_Raw_DEPRECATED": round(_nse_interannual(ov, rv), 3),
                "NSE_BC_DEPRECATED":  round(_nse_interannual(ov, bv), 3),
            })
        rows.append(row)

    df = pd.DataFrame(rows)
    if len(df):
        # Distributional improvement from bias correction (order-invariant)
        raw_abs = df.PBIAS_Raw.abs()
        df["PBIAS_Improvement_%"] = (
            (raw_abs - df.PBIAS_BC.abs()) / raw_abs.replace(0, np.nan) * 100
        ).round(1)
        df["SDratio_err_Raw"] = (df.SDratio_Raw - 1).abs().round(3)
        df["SDratio_err_BC"]  = (df.SDratio_BC - 1).abs().round(3)

    mode = ("split-sample VAL=%s" % (val_win,)) if val_win else "calibration-period (consistency check)"
    if legacy_interannual:
        log.warning("validation_metrics [%s]: legacy interannual KGE/NSE emitted "
                    "as *_DEPRECATED — NOT valid skill for free-running GCMs.", season)
    log.info("validation_metrics [%s]: %d stations | %s | distributional metrics "
             "(PBIAS, SDratio, PSS, KS)", season, len(df), mode)
    return df
