"""rainfall.seasonal — Annual/Wet/Dry rainfall totals (config-driven seasons).

Dry-season hydrological-year convention:
  The Nov–Apr dry season straddles two calendar years.
  Nov(Y) and Dec(Y) are the tail of the dry block that begins Nov(Y) and ends
  Apr(Y+1).  We label that whole block as hydrological year Y+1 — matching
  the convention used in the observed-data pipeline (rainfall_trend_analysis_v3).

Completeness gate:
  A season total is set to NaN when fewer than MIN_COMPLETENESS (80 %) of the
  expected non-leap days have finite (non-NaN) values.  This prevents years
  with large data gaps from appearing as genuine low-rainfall years.
"""
from __future__ import annotations

import logging
from calendar import monthrange

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)
_ID = ["YEAR", "MONTH", "DAY"]

MIN_COMPLETENESS = 0.80   # fraction of expected days that must be finite


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _month_days(year: int, month: int) -> int:
    """Days in month, ignoring the leap day (we strip Feb-29 upstream)."""
    days = monthrange(year, month)[1]
    if month == 2 and days == 29:
        days = 28
    return days


def _expected_days(season: str, hydro_year: int,
                   wet: list[int], dry: list[int]) -> int:
    """Expected non-leap day count for the season in the given hydrological year."""
    if season == "Annual":
        return 365
    if season == "Wet":
        return sum(_month_days(hydro_year, m) for m in wet)
    # Dry: Nov(hydro_year-1) + Dec(hydro_year-1) + Jan..Apr(hydro_year)
    dry_prev = [m for m in dry if m >= 11]
    dry_curr = [m for m in dry if m <= 4]
    n = sum(_month_days(hydro_year - 1, m) for m in dry_prev)
    n += sum(_month_days(hydro_year, m) for m in dry_curr)
    return n


def _safe_sum(arr: np.ndarray, expected: int) -> float:
    """nansum with completeness gate.  Returns NaN when data coverage < 80 %."""
    if expected <= 0:
        return np.nan
    n_valid = int(np.count_nonzero(np.isfinite(arr)))
    if n_valid / expected < MIN_COMPLETENESS:
        return np.nan
    return float(np.nansum(arr))


# ---------------------------------------------------------------------------
# core aggregation
# ---------------------------------------------------------------------------

def _wide_to_yearly(df: pd.DataFrame, wet: list[int], dry: list[int],
                    y0: int, y1: int) -> pd.DataFrame:
    # Remove leap days so expected-day counts are stable
    df = df[~((df.MONTH == 2) & (df.DAY == 29))].copy()
    df = df[(df.YEAR >= y0) & (df.YEAR <= y1)]

    stations = [c for c in df.columns
                if c not in _ID and str(c).strip().isdigit()]

    yr = df.YEAR.to_numpy(int)
    mon = df.MONTH.to_numpy(int)
    wm = df.MONTH.isin(wet).to_numpy()

    dry_prev_months = [m for m in dry if m >= 11]   # Nov, Dec
    dry_curr_months = [m for m in dry if m <= 4]    # Jan–Apr

    years = np.unique(yr)
    rows: list[tuple] = []

    for col in stations:
        pr = df[col].to_numpy(float)

        # ── Annual (calendar year) ──────────────────────────────────────────
        for y in years:
            ym = yr == y
            rows.append((str(col), int(y), "Annual",
                         _safe_sum(pr[ym], _expected_days("Annual", y, wet, dry))))

        # ── Wet season (May–Oct within calendar year) ───────────────────────
        for y in years:
            ym = (yr == y) & wm
            rows.append((str(col), int(y), "Wet",
                         _safe_sum(pr[ym], _expected_days("Wet", y, wet, dry))))

        # ── Dry season — HYDROLOGICAL YEAR (label = year the season ends) ──
        # Block:  Nov(y) + Dec(y)  +  Jan(y+1)..Apr(y+1)  → labelled y+1
        for y in years:
            if y + 1 > y1:
                continue    # Jan–Apr of y+1 fall outside the loaded period
            nd = pr[(yr == y) & np.isin(mon, dry_prev_months)]       # Nov, Dec of y
            ja = pr[(yr == (y + 1)) & np.isin(mon, dry_curr_months)] # Jan–Apr of y+1
            block = np.concatenate([nd, ja])
            hydro_yr = y + 1
            rows.append((str(col), int(hydro_yr), "Dry",
                         _safe_sum(block, _expected_days("Dry", hydro_yr, wet, dry))))

    return pd.DataFrame(rows, columns=["station", "year", "season", "rainfall"])


# ---------------------------------------------------------------------------
# public entry points
# ---------------------------------------------------------------------------

def observed_yearly(path: str, wet: list[int], dry: list[int],
                    y0: int, y1: int) -> pd.DataFrame:
    df = pd.read_excel(path)
    return _wide_to_yearly(df, wet, dry, y0, y1)


def cmip6_yearly(path: str, wet: list[int], dry: list[int],
                 y0: int, y1: int) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.loc[:, [c for c in df.columns if not str(c).startswith("Unnamed")]]
    return _wide_to_yearly(df, wet, dry, y0, y1)
