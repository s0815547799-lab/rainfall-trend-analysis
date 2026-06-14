"""rainfall.seasonal — Annual/Wet/Dry rainfall totals (config-driven seasons).

การรองรับพื้นที่ใหม่:
  wet_months และ dry_months ส่งมาจาก config.yaml โดยตรง
  ไม่มีค่า hardcode ใดๆ — ปรับฤดูกาลใน config เพียงอย่างเดียว

Dry-season hydrological-year convention:
  The dry season spans two calendar years (e.g., Nov–Apr).
  Nov(Y) + Dec(Y) are the opening of the dry block that ends Apr(Y+1).
  We label the entire Nov(Y)–Apr(Y+1) block as hydrological year Y+1,
  matching the convention used throughout tropical monsoon hydrology.

Completeness gate:
  Season totals below MIN_COMPLETENESS (default 80%) valid-day coverage
  are set to NaN rather than a misleadingly low sum.
"""
from __future__ import annotations

import logging
from calendar import monthrange

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)
_ID = ["YEAR", "MONTH", "DAY"]

# Default; overridden by cfg["quality"]["min_completeness"] at runtime
_DEFAULT_MIN_COMPLETENESS = 0.80


# ── Helpers ───────────────────────────────────────────────────────────────────

def _month_days(year: int, month: int) -> int:
    """Days in month, excluding the leap day (Feb-29 is stripped upstream)."""
    days = monthrange(year, month)[1]
    return 28 if (month == 2 and days == 29) else days


def _expected_days(season: str, hydro_year: int,
                   wet: list[int], dry: list[int]) -> int:
    """Expected non-leap day count for the season in the given hydrological year."""
    if season == "Annual":
        return 365
    if season == "Wet":
        return sum(_month_days(hydro_year, m) for m in wet)
    # Dry: prev_year's Nov+Dec  +  current year's Jan–Apr
    dry_prev = [m for m in dry if m >= 11]
    dry_curr = [m for m in dry if m <= 4]
    n  = sum(_month_days(hydro_year - 1, m) for m in dry_prev)
    n += sum(_month_days(hydro_year,     m) for m in dry_curr)
    return n


def _safe_sum(arr: np.ndarray, expected: int,
              min_completeness: float = _DEFAULT_MIN_COMPLETENESS) -> float:
    """Return nansum only when valid-data fraction ≥ min_completeness, else NaN."""
    if expected <= 0:
        return np.nan
    n_valid = int(np.count_nonzero(np.isfinite(arr)))
    if n_valid / expected < min_completeness:
        return np.nan
    return float(np.nansum(arr))


# ── Core aggregation ──────────────────────────────────────────────────────────

def _wide_to_yearly(df: pd.DataFrame, wet: list[int], dry: list[int],
                    y0: int, y1: int,
                    min_completeness: float = _DEFAULT_MIN_COMPLETENESS,
                    ) -> pd.DataFrame:
    """Convert wide daily DataFrame to long station×year×season rainfall totals.

    Parameters
    ----------
    df              : daily rainfall DataFrame with columns YEAR, MONTH, DAY, <stations>
    wet             : list of wet-season month numbers  (from config)
    dry             : list of dry-season month numbers  (from config)
    y0, y1          : year range to process
    min_completeness: fraction of days that must be non-NaN for a valid season total
    """
    # Remove leap days for stable expected-day counts
    df = df[~((df.MONTH == 2) & (df.DAY == 29))].copy()
    df = df[(df.YEAR >= y0) & (df.YEAR <= y1)]

    # Auto-detect station columns: numeric IDs (e.g., 500001) or any non-ID column
    stations = [c for c in df.columns
                if c not in _ID and str(c).strip().isdigit()]
    if not stations:
        # Fallback: treat all non-ID columns as stations
        stations = [c for c in df.columns if c not in _ID]
        log.warning("_wide_to_yearly: no purely-numeric station columns found; "
                    "treating ALL non-ID columns (%d) as stations", len(stations))

    yr  = df.YEAR.to_numpy(int)
    mon = df.MONTH.to_numpy(int)
    wm  = df.MONTH.isin(wet).to_numpy()

    dry_prev_months = [m for m in dry if m >= 11]   # Nov, Dec
    dry_curr_months = [m for m in dry if m <= 4]    # Jan–Apr

    years = np.unique(yr)
    rows: list[tuple] = []

    for col in stations:
        pr = df[col].to_numpy(float)

        # Annual (calendar year)
        for y in years:
            ym = yr == y
            rows.append((str(col), int(y), "Annual",
                         _safe_sum(pr[ym], _expected_days("Annual", y, wet, dry),
                                   min_completeness)))

        # Wet season (within calendar year)
        for y in years:
            ym = (yr == y) & wm
            rows.append((str(col), int(y), "Wet",
                         _safe_sum(pr[ym], _expected_days("Wet", y, wet, dry),
                                   min_completeness)))

        # Dry season — HYDROLOGICAL YEAR (label = year the season ends)
        # Block: Nov(y) + Dec(y)  →  Jan(y+1) … Apr(y+1)  →  labelled y+1
        for y in years:
            if y + 1 > y1:
                continue
            nd = pr[(yr == y)       & np.isin(mon, dry_prev_months)]
            ja = pr[(yr == (y + 1)) & np.isin(mon, dry_curr_months)]
            block    = np.concatenate([nd, ja])
            hydro_yr = y + 1
            rows.append((str(col), int(hydro_yr), "Dry",
                         _safe_sum(block, _expected_days("Dry", hydro_yr, wet, dry),
                                   min_completeness)))

    return pd.DataFrame(rows, columns=["station", "year", "season", "rainfall"])


# ── Public entry points ───────────────────────────────────────────────────────

def observed_yearly(path: str, wet: list[int], dry: list[int],
                    y0: int, y1: int,
                    min_completeness: float = _DEFAULT_MIN_COMPLETENESS,
                    ) -> pd.DataFrame:
    """Load observed daily Excel and aggregate to yearly seasonal totals."""
    suffix = str(path).lower()
    if suffix.endswith(".csv"):
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)
    return _wide_to_yearly(df, wet, dry, y0, y1, min_completeness)


def cmip6_yearly(path: str, wet: list[int], dry: list[int],
                 y0: int, y1: int,
                 min_completeness: float = _DEFAULT_MIN_COMPLETENESS,
                 ) -> pd.DataFrame:
    """Load a CMIP6 model CSV and aggregate to yearly seasonal totals."""
    df = pd.read_csv(path)
    df = df.loc[:, [c for c in df.columns if not str(c).startswith("Unnamed")]]
    return _wide_to_yearly(df, wet, dry, y0, y1, min_completeness)
