"""
cmip6_trend.module00.calendar_utils
===================================

Calendar utilities for Module 00 (Preprocessing).

Implements the LOCKED temporal framework (per IMPLEMENTATION_PLAN, Directive):

    Water Year  : 1 May (Y)  ->  30 Apr (Y+1)   labelled by starting year Y
    Rainy season: May - October          (months 5..10)
    Dry season  : November - April        (months 11,12,1,2,3,4)

    Nesting identity (must hold):  Annual(WY) == Rainy(WY) + Dry(WY)

Leap-day handling (LOCKED): 29 February is removed from ALL datasets so that
observed (proleptic Gregorian) and CMIP6 (no-leap / 365-day) calendars align
to a common 365-day year. The number of dropped rows is logged by the caller.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from ..config import WET_MONTHS, DRY_MONTHS, WATER_YEAR_START_MONTH

log = logging.getLogger(__name__)

__all__ = [
    "remove_feb29",
    "assign_water_year",
    "assign_season",
    "SEASON_RAINY",
    "SEASON_DRY",
]

SEASON_RAINY = "Rainy"
SEASON_DRY = "Dry"


def remove_feb29(df: pd.DataFrame, date_col: str = "date") -> tuple[pd.DataFrame, int]:
    """Remove 29 February rows so every year has 365 days.

    Parameters
    ----------
    df : DataFrame with a datetime column ``date_col``.
    date_col : name of the datetime column.

    Returns
    -------
    (filtered_df, n_removed) : DataFrame without 29-Feb rows and the count
    of removed rows (for logging / reproducibility).
    """
    if date_col not in df.columns:
        raise KeyError(f"date column {date_col!r} not found")
    dt = pd.to_datetime(df[date_col])
    mask_feb29 = (dt.dt.month == 2) & (dt.dt.day == 29)
    n_removed = int(mask_feb29.sum())
    out = df.loc[~mask_feb29].copy()
    if n_removed:
        log.info("remove_feb29: dropped %d rows (29-Feb) -> 365-day years", n_removed)
    return out, n_removed


def assign_water_year(dates: pd.Series, start_month: int = WATER_YEAR_START_MONTH) -> pd.Series:
    """Map each date to its Water-Year label (the starting calendar year).

    Water year begins on 1 ``start_month`` (default May). Dates in months
    >= start_month belong to water year = calendar year; earlier months
    (Jan-Apr) belong to the previous calendar year's water year.

    Example (start_month=5):
        2000-05-01 .. 2001-04-30  -> water year 2000
    """
    dt = pd.to_datetime(dates)
    wy = dt.dt.year.where(dt.dt.month >= start_month, dt.dt.year - 1)
    return wy.astype("int64")


def assign_season(dates: pd.Series) -> pd.Series:
    """Classify each date into Rainy (May-Oct) or Dry (Nov-Apr).

    Uses the locked month definitions from config. Returns a string Series
    with values in {"Rainy", "Dry"}.
    """
    dt = pd.to_datetime(dates)
    month = dt.dt.month
    season = pd.Series(np.where(month.isin(WET_MONTHS), SEASON_RAINY, SEASON_DRY),
                       index=dt.index)
    # Defensive check: every month must fall in exactly one season set.
    covered = set(WET_MONTHS) | set(DRY_MONTHS)
    if covered != set(range(1, 13)):
        raise ValueError(f"season month sets do not cover all 12 months: {sorted(covered)}")
    return season
