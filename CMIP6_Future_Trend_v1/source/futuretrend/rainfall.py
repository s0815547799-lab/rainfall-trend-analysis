"""
futuretrend.rainfall — Module 1 rainfall totals (Annual/Wet/Dry), streaming.

Per Module 1 of the directive: compute REAL rainfall totals (not ETCCDI proxies).
Streams each CSV column-wise (memory-safe), sums daily precip to yearly Annual /
Wet-season / Dry-season totals, tags the future window, and returns a long table
[variable, scenario, window, station, model, year, value] ready for the SAME
frozen trend engine (compute_trends). Reuses the validated loader + calendar.

variables produced: RainTotal_Annual, RainTotal_Wet, RainTotal_Dry.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from .config import WET_MONTHS, DRY_MONTHS
from .module00.loader import infer_future_filespec, FUTURE_WINDOWS

log = logging.getLogger(__name__)

__all__ = ["rainfall_totals_yearly", "RAINFALL_VARS"]

RAINFALL_VARS = ["RainTotal_Annual", "RainTotal_Wet", "RainTotal_Dry"]
_ID = ["YEAR", "MONTH", "DAY"]

# Expected non-leap days per season (Feb 29 stripped before all processing)
_EXP_ANNUAL = 365          # Jan–Dec
_EXP_WET    = 184          # May 31 + Jun 30 + Jul 31 + Aug 31 + Sep 30 + Oct 31
_EXP_DRY    = 181          # Nov 30 + Dec 31 + Jan 31 + Feb 28 + Mar 31 + Apr 30

# Dry-season spans two calendar years: Nov(Y)+Dec(Y) → Jan–Apr(Y+1), labelled Y+1
_PREV_DRY = [11, 12]
_CURR_DRY = [1, 2, 3, 4]


def _safe_sum(arr: np.ndarray, expected: int, min_completeness: float = 0.80) -> float:
    """Return nansum(arr), or NaN when valid-day fraction < min_completeness."""
    n_valid = int(np.sum(~np.isnan(arr)))
    if n_valid == 0 or n_valid / expected < min_completeness:
        return np.nan
    return float(np.nansum(arr))


def _read_wide(path):
    df = pd.read_csv(path)
    df = df.loc[:, [c for c in df.columns if not str(c).startswith("Unnamed")]]
    stations = [c for c in df.columns if c not in _ID and str(c).strip().isdigit()]
    df = df[~((df.MONTH == 2) & (df.DAY == 29))].reset_index(drop=True)
    df["year"] = df["YEAR"].astype(int)
    return df, stations


def rainfall_totals_yearly(input_dir, dataset="QDM") -> pd.DataFrame:
    """Yearly Annual/Wet/Dry rainfall totals per station/model/scenario/window."""
    input_dir = Path(input_dir)
    files = sorted(input_dir.rglob("*.csv"))
    rows = []
    for f in files:
        try:
            spec = infer_future_filespec(f)
        except ValueError:
            continue
        if spec.dataset != dataset or spec.scenario == "historical":
            continue
        df, stations = _read_wide(f)
        mon = df["MONTH"].to_numpy()
        yr  = df["year"].to_numpy()
        wet_mask      = np.isin(mon, WET_MONTHS)
        prev_dry_mask = np.isin(mon, _PREV_DRY)   # Nov–Dec of calendar year Y
        curr_dry_mask = np.isin(mon, _CURR_DRY)   # Jan–Apr of calendar year Y+1
        years_array = np.unique(yr)
        yr_set = set(years_array.tolist())

        for col in stations:
            pr = df[col].to_numpy(dtype=float)

            # ── Annual and Wet (calendar-year) ──────────────────────────────
            cal_rows: list[tuple] = []
            for year in years_array:
                ym = yr == year
                cal_rows.append((spec.scenario, str(col), spec.model, int(year),
                                 "RainTotal_Annual", _safe_sum(pr[ym], _EXP_ANNUAL)))
                cal_rows.append((spec.scenario, str(col), spec.model, int(year),
                                 "RainTotal_Wet",    _safe_sum(pr[ym & wet_mask], _EXP_WET)))

            # ── Dry (hydrological year: Nov(Y)+Dec(Y)+Jan–Apr(Y+1), label Y+1) ──
            for y in years_array:
                if (y + 1) not in yr_set:
                    continue
                nd  = pr[(yr == y)       & prev_dry_mask]
                ja  = pr[(yr == (y + 1)) & curr_dry_mask]
                arr = np.concatenate([nd, ja])
                cal_rows.append((spec.scenario, str(col), spec.model, int(y + 1),
                                 "RainTotal_Dry", _safe_sum(arr, _EXP_DRY)))

            # ── Window tagging (duplicate rows for overlapping windows) ─────
            for scen, stn, mdl, year, var, val in cal_rows:
                for wname, (w0, w1) in FUTURE_WINDOWS.items():
                    if w0 <= year <= w1:
                        rows.append((scen, wname, stn, mdl, int(year), var, val))

        log.info("rainfall totals: %s/%s done", spec.model, spec.scenario)

    out = pd.DataFrame(rows, columns=["scenario", "window", "station", "model",
                                      "year", "variable", "value"])
    log.info("rainfall_totals_yearly: %d rows", len(out))
    return out
