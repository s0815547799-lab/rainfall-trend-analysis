"""Shared helper functions used across multiple figure modules."""

import numpy as np


def _sens_line(arr, slope, yrs):
    """Anchored Sen trend line at median."""
    if np.isnan(slope): return None
    y_bar  = float(np.nanmedian(arr))
    x_bar  = float(np.median(yrs))
    return slope * (yrs - x_bar) + y_bar


def _sig_label(sig05, sig01, Z):
    if sig01:  return "**"
    if sig05:  return "*"
    return "ns"


def _col_trend(sig05, Z):
    from ..config import C
    if sig05 and Z > 0: return C["inc"]
    if sig05 and Z < 0: return C["dec"]
    return C["ns_col"]
