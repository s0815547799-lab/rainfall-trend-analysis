"""
rta.io — Data I/O, quality control, checkpoint system, station coordinates.

Data loading / QC extracted from rainfall_trend_analysis_v3.py §1 (lines 189–244).
Checkpoint system and station-coordinates loader are new additions for v4.
"""

# ── Standard library ──────────────────────────────────────────────────────────
import os
import math
import sys
import warnings
import pickle
from pathlib import Path

# ── Scientific stack ──────────────────────────────────────────────────────────
import numpy as np
import pandas as pd

# ── Package config ────────────────────────────────────────────────────────────
from .config import MISS_FLAGS, WET_THR


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §1a  CSV discovery                                                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def find_csv(folder: str) -> str:
    """
    Auto-discover daily rainfall CSV in folder.

    Preference order:
      1. Files whose names contain "observed" or "rain" (case-insensitive).
      2. Any remaining CSV file.

    Files whose names begin with "Output_" are always skipped.

    Returns the path as a string, or exits with an error if none found.
    """
    csvs = sorted(
        f for f in Path(folder).glob("*.csv")
        if not f.name.startswith("Output_")
    )
    obs = [f for f in csvs
           if "observed" in f.name.lower() or "rain" in f.name.lower()]
    result = obs or csvs
    if not result:
        sys.exit("No CSV found")
    return str(result[0])


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §1b  Daily loader                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def load_daily(path: str) -> pd.DataFrame:
    """
    Load daily rainfall CSV → DatetimeIndex DataFrame.

    Expects columns YEAR, MONTH, DAY plus one column per station.
    Missing-value flags listed in MISS_FLAGS are replaced with NaN.
    Any remaining negative values are also set to NaN.

    Returns a DataFrame indexed by date with station columns only.
    """
    df = pd.read_csv(path)
    for mv in MISS_FLAGS:
        df.replace(mv, np.nan, inplace=True)
    df.columns = [str(c) for c in df.columns]
    stns = [c for c in df.columns if c not in ("YEAR", "MONTH", "DAY")]
    for s in stns:
        df.loc[df[s] < 0, s] = np.nan
    df["date"] = pd.to_datetime(
        {"year": df["YEAR"], "month": df["MONTH"], "day": df["DAY"]}
    )
    return df.set_index("date")[stns]


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §1c  Quality control                                                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def quality_control(df: pd.DataFrame) -> tuple:
    """
    QC pipeline: report missing values, detect outliers (IQR 3×),
    fill short gaps (≤5 consecutive days) by linear interpolation.

    Outlier detection uses the IQR of wet-day values (≥ WET_THR mm).
    Upper fence = Q3 + 3.0 × IQR.  Values above this fence are flagged
    (counted) but NOT removed — only NaN gaps up to 5 days are filled.

    Parameters
    ----------
    df : pd.DataFrame
        Daily rainfall DataFrame with DatetimeIndex (from load_daily).

    Returns
    -------
    df_clean : pd.DataFrame
        Copy of df with short NaN gaps linearly interpolated.
    qc_dict : dict
        Per-station QC report:
          n_total     — total rows
          n_missing   — missing before interpolation
          pct_miss    — % missing before interpolation
          n_outlier   — values above the IQR upper fence
          upper_fence — IQR upper fence value (mm/day)
          n_filled    — number of gaps filled by interpolation
    """
    stns = df.columns.tolist()
    qc   = {}
    df   = df.copy()
    for s in stns:
        series      = df[s].copy()
        n_miss      = int(series.isna().sum())
        wet_vals    = series[(series >= WET_THR) & series.notna()]
        q1, q3      = float(wet_vals.quantile(0.25)), float(wet_vals.quantile(0.75))
        iqr         = q3 - q1
        upper_fence = q3 + 3.0 * iqr
        n_out       = int((series > upper_fence).sum())
        filled      = series.interpolate(method="time", limit=5,
                                         limit_direction="both")
        n_fill      = int(filled.notna().sum()) - int(series.notna().sum())
        df[s]       = filled
        qc[s] = dict(
            n_total     = len(series),
            n_missing   = n_miss,
            pct_miss    = round(n_miss / len(series) * 100, 2),
            n_outlier   = n_out,
            upper_fence = round(upper_fence, 1),
            n_filled    = n_fill,
        )
    return df, qc


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §1d  Checkpoint system                                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def save_checkpoint(name: str, data, cp_dir: Path) -> None:
    """
    Pickle *data* to ``cp_dir/ckpt_{name}.pkl``.

    Creates cp_dir if it does not already exist.

    Parameters
    ----------
    name   : str   Logical checkpoint name (e.g. "aggregation").
    data   : any   Picklable Python object.
    cp_dir : Path  Directory in which to store checkpoint files.
    """
    cp_dir = Path(cp_dir)
    cp_dir.mkdir(parents=True, exist_ok=True)
    pkl_path = cp_dir / f"ckpt_{name}.pkl"
    with open(pkl_path, "wb") as fh:
        pickle.dump(data, fh, protocol=pickle.HIGHEST_PROTOCOL)


def load_checkpoint(name: str, cp_dir: Path):
    """
    Return unpickled data from ``cp_dir/ckpt_{name}.pkl``.

    Returns None if the file does not exist, allowing callers to
    detect a cache miss without raising an exception.

    Parameters
    ----------
    name   : str   Logical checkpoint name matching a prior save_checkpoint call.
    cp_dir : Path  Directory containing checkpoint files.

    Returns
    -------
    data or None
    """
    pkl_path = Path(cp_dir) / f"ckpt_{name}.pkl"
    if not pkl_path.exists():
        return None
    with open(pkl_path, "rb") as fh:
        return pickle.load(fh)


def list_checkpoints(cp_dir: Path) -> list:
    """
    Return a sorted list of checkpoint names found in cp_dir.

    Only files matching the pattern ``ckpt_*.pkl`` are included.
    The returned names have the ``ckpt_`` prefix and ``.pkl`` suffix
    stripped — i.e. they match the *name* argument of save_checkpoint.

    Parameters
    ----------
    cp_dir : Path  Directory to scan.

    Returns
    -------
    list of str  Sorted checkpoint names (empty list if none found).
    """
    cp_dir = Path(cp_dir)
    if not cp_dir.exists():
        return []
    names = sorted(
        p.stem[len("ckpt_"):]
        for p in cp_dir.glob("ckpt_*.pkl")
    )
    return names


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §1e  Station coordinates loader                                         ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def load_coords(folder: str) -> "dict | None":
    """
    Auto-detect a CSV with station coordinates in *folder*.

    Discovery
    ---------
    Looks for files matching ``*coord*.csv`` or ``*station*.csv``
    (case-insensitive, skipping files that start with "Output_").

    Expected columns
    ----------------
    Station column : "Station" or "Name" (case-insensitive).
    Latitude       : "Lat" or "Latitude" (case-insensitive).
    Longitude      : "Lon" or "Longitude" (case-insensitive).

    Returns
    -------
    dict  {station_name: (lat, lon)}  — or None if no suitable file is found
    or required columns are missing.
    """
    folder = Path(folder)
    candidates = []
    for pattern in ("*coord*.csv", "*station*.csv"):
        candidates.extend(
            f for f in folder.glob(pattern)
            if not f.name.startswith("Output_")
        )
    # Case-insensitive fallback: re-scan all CSVs for the patterns
    if not candidates:
        for f in folder.glob("*.csv"):
            if f.name.startswith("Output_"):
                continue
            lower = f.name.lower()
            if "coord" in lower or "station" in lower:
                candidates.append(f)

    if not candidates:
        return None

    coord_file = sorted(candidates)[0]

    try:
        df = pd.read_csv(coord_file)
    except Exception:
        return None

    # Normalise column names for matching
    col_map = {c.lower().strip(): c for c in df.columns}

    # Identify station column
    stn_col = None
    for candidate in ("station", "name"):
        if candidate in col_map:
            stn_col = col_map[candidate]
            break

    # Identify latitude column
    lat_col = None
    for candidate in ("lat", "latitude"):
        if candidate in col_map:
            lat_col = col_map[candidate]
            break

    # Identify longitude column
    lon_col = None
    for candidate in ("lon", "longitude"):
        if candidate in col_map:
            lon_col = col_map[candidate]
            break

    if stn_col is None or lat_col is None or lon_col is None:
        warnings.warn(
            f"load_coords: file '{coord_file.name}' found but required columns "
            "(Station/Name, Lat/Latitude, Lon/Longitude) are missing.",
            UserWarning,
            stacklevel=2,
        )
        return None

    coords = {}
    for _, row in df.iterrows():
        try:
            name = str(row[stn_col]).strip()
            lat  = float(row[lat_col])
            lon  = float(row[lon_col])
            coords[name] = (lat, lon)
        except (ValueError, TypeError):
            continue

    return coords if coords else None
