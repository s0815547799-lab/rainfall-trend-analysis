"""
future_etccdi.module05.rainfall_context
========================================

RULE 4 (permanent) — rainfall context layer, memory-safe (streaming).

ETCCDI extremes must be read alongside rainfall *amount* trends. This module
streams each CSV column-wise (one wide file in memory at a time, never the melted
product), computes Annual/Rainy/Dry rainfall totals per hydrological year, then
runs the validated trend stack (MK, Lag-K MMK, PW-MK, TFPW-MK, Sen) on the
per-window yearly totals. Supporting hydroclimatological context only.

Windows reuse FUTURE_WINDOWS (Historical/Near/Mid/Late).
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import WET_MONTHS, DRY_MONTHS
from ..module00.loader import infer_future_filespec, FUTURE_WINDOWS
from ..trend_tests import standard_mk, pw_mk, tfpw_mk, sens_slope
from ..lag_k_mmk import lag_k_mmk

log = logging.getLogger(__name__)

__all__ = ["run_rainfall_context"]

_ID = ["YEAR", "MONTH", "DAY"]

# Expected non-leap days per season (Feb 29 stripped before all processing)
_EXP_ANNUAL = 365
_EXP_WET    = 184
_EXP_DRY    = 181

# Dry-season spans two calendar years: Nov(Y)+Dec(Y) → Jan–Apr(Y+1), labelled Y+1
_PREV_DRY = [11, 12]
_CURR_DRY = [1, 2, 3, 4]


def _safe_sum(arr: np.ndarray, expected: int, min_completeness: float = 0.80) -> float:
    n_valid = int(np.sum(~np.isnan(arr)))
    if n_valid == 0 or n_valid / expected < min_completeness:
        return np.nan
    return float(np.nansum(arr))


def _read_wide(path):
    df = pd.read_csv(path)
    df = df.loc[:, [c for c in df.columns if not c.startswith("Unnamed")]]
    stations = [c for c in df.columns if c not in _ID and str(c).strip().isdigit()]
    df = df[~((df.MONTH == 2) & (df.DAY == 29))].reset_index(drop=True)
    return df, stations


def _all_methods(x: np.ndarray) -> list[dict]:
    def norm(res, method):
        return {"method": method, "n": res.get("n", np.nan),
                "z": res.get("Z", res.get("z", np.nan)),
                "p_value": res.get("p_value", np.nan),
                "significant": bool(res.get("sig_05", res.get("significant", False))),
                "sen_slope": res.get("sen_slope", res.get("slope_Q", np.nan)),
                "n_effective": res.get("n_eff", res.get("n_effective", np.nan))}
    rows = [norm(standard_mk(x), "MK"), norm(lag_k_mmk(x), "Lag-K MMK"),
            norm(pw_mk(x), "PW-MK"), norm(tfpw_mk(x), "TFPW-MK")]
    q, _, _ = sens_slope(x)
    xc = x[~np.isnan(x)]
    rows.append({"method": "Sen", "n": int(len(xc)), "z": np.nan, "p_value": np.nan,
                 "significant": False,
                 "sen_slope": round(q, 4) if not np.isnan(q) else np.nan,
                 "n_effective": np.nan})
    return rows


def run_rainfall_context(input_dir: str | Path, out_dir: str | Path) -> pd.DataFrame:
    """Stream CSVs → seasonal totals per window → trend stack. Writes parquet."""
    input_dir = Path(input_dir); out_dir = Path(out_dir)
    files = sorted(input_dir.rglob("*.csv"))
    tot_rows = []
    for f in files:
        try:
            spec = infer_future_filespec(f)
        except ValueError:
            continue
        df, stations = _read_wide(f)
        df["year"] = df["YEAR"].astype(int)
        mon = df["MONTH"].to_numpy()
        yr  = df["year"].to_numpy()
        wet_mask      = np.isin(mon, WET_MONTHS)
        prev_dry_mask = np.isin(mon, _PREV_DRY)
        curr_dry_mask = np.isin(mon, _CURR_DRY)
        years_array = np.unique(yr)
        yr_set = set(years_array.tolist())

        for col in stations:
            pr = df[col].to_numpy(dtype=float)

            # ── Annual and Rainy (calendar-year) ────────────────────────────
            cal_rows: list[tuple] = []
            for year in years_array:
                ym = yr == year
                cal_rows.append((spec.dataset, spec.model, spec.scenario, str(col),
                                 "Annual", int(year), _safe_sum(pr[ym], _EXP_ANNUAL)))
                cal_rows.append((spec.dataset, spec.model, spec.scenario, str(col),
                                 "Rainy",  int(year), _safe_sum(pr[ym & wet_mask], _EXP_WET)))

            # ── Dry (hydrological year: Nov(Y)+Dec(Y)+Jan–Apr(Y+1), label Y+1) ──
            for y in years_array:
                if (y + 1) not in yr_set:
                    continue
                nd  = pr[(yr == y)       & prev_dry_mask]
                ja  = pr[(yr == (y + 1)) & curr_dry_mask]
                arr = np.concatenate([nd, ja])
                cal_rows.append((spec.dataset, spec.model, spec.scenario, str(col),
                                 "Dry", int(y + 1), _safe_sum(arr, _EXP_DRY)))

            # ── Window tagging (duplicate rows for overlapping windows) ─────
            for ds, mdl, scen, stn, season, year, val in cal_rows:
                for wname, (w0, w1) in FUTURE_WINDOWS.items():
                    if w0 <= year <= w1:
                        tot_rows.append((ds, mdl, scen, wname, stn, season, int(year), val))

        log.info("rainfall totals: %s/%s/%s done", spec.dataset, spec.model, spec.scenario)

    totals = pd.DataFrame(tot_rows, columns=["dataset", "model", "scenario", "window",
                                             "station", "season", "year", "total"])

    # trends per (dataset, model, scenario, window, station, season)
    records = []
    keys = ["dataset", "model", "scenario", "window", "station", "season"]
    for key, g in totals.groupby(keys, sort=False):
        g = g.sort_values("year")
        x = g["total"].to_numpy(dtype=float)
        if np.all(np.isnan(x)) or len(x) < 3:
            continue
        for row in _all_methods(x):
            row.update(dict(zip(keys, key)))
            records.append(row)
    out = pd.DataFrame(records)
    out_dir.mkdir(parents=True, exist_ok=True)
    out.to_parquet(out_dir / "Future_Trend_Assessment.parquet", index=False)
    log.info("run_rainfall_context: %d trend rows (RULE 4 context)", len(out))
    return out
