"""
rta.spatial — Station coordinates support for spatial trend analysis.

Provides coordinate loading, validation, and utility helpers used by
both the main pipeline and spatial map figures.
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

__all__ = ["load_coords", "validate_coords", "coords_to_df"]


# ── Coordinate file discovery ─────────────────────────────────────────────────

_COORD_PATTERNS = ("*coord*.csv", "*coordinates*.csv",
                   "*station*.csv", "*stations*.csv")

_COL_STATION = ("station", "name", "id", "stn")
_COL_LAT     = ("lat", "latitude", "y")
_COL_LON     = ("lon", "longitude", "long", "x")


def _find_coord_col(cols_lower: list, candidates: tuple) -> "str | None":
    for name in candidates:
        if name in cols_lower:
            return name
    return None


def load_coords(folder: str) -> "dict | None":
    """
    Auto-detect and load a station-coordinates CSV from *folder*.

    Discovery
    ---------
    Searches for files matching any of:
        *coord*.csv  *coordinates*.csv  *station*.csv  *stations*.csv
    (case-insensitive; files starting with "Output_" are skipped).

    Expected columns (case-insensitive matching)
    --------------------------------------------
    Station : "Station", "Name", "ID", "Stn"
    Latitude : "Lat", "Latitude", "Y"
    Longitude : "Lon", "Longitude", "Long", "X"

    Returns
    -------
    dict  {station_name: (lat, lon)}
      or None if no suitable file is found.
    """
    folder = Path(folder)
    candidates: list[Path] = []
    for pattern in _COORD_PATTERNS:
        candidates.extend(
            f for f in folder.glob(pattern)
            if not f.name.startswith("Output_")
        )
    # Deduplicate while preserving order
    seen: set = set()
    unique: list[Path] = []
    for p in candidates:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    for path in unique:
        try:
            df = pd.read_csv(path, dtype=str)
        except Exception:
            continue

        cols_lower = [c.lower() for c in df.columns]
        stn_col = _find_coord_col(cols_lower, _COL_STATION)
        lat_col = _find_coord_col(cols_lower, _COL_LAT)
        lon_col = _find_coord_col(cols_lower, _COL_LON)

        if stn_col is None or lat_col is None or lon_col is None:
            continue

        # Map back to original column names
        col_map = {c.lower(): c for c in df.columns}
        try:
            df_sub = df[[col_map[stn_col],
                         col_map[lat_col],
                         col_map[lon_col]]].copy()
            df_sub.columns = ["station", "lat", "lon"]
            df_sub = df_sub.dropna(subset=["lat", "lon"])
            result = {
                str(row["station"]).strip(): (float(row["lat"]), float(row["lon"]))
                for _, row in df_sub.iterrows()
            }
            if result:
                return result
        except Exception:
            continue

    return None


def validate_coords(coords: dict, stns: list) -> dict:
    """
    Validate that all stations in *stns* have coordinates in *coords*.

    Returns
    -------
    dict with keys:
        matched   (list) — stations present in both stns and coords
        missing   (list) — stations in stns but NOT in coords
        extra     (list) — stations in coords but NOT in stns
        coverage  (float) — fraction of stns with coordinates
    """
    stns   = [str(s) for s in stns]
    coord_keys = set(str(k) for k in coords.keys()) if coords else set()

    matched = [s for s in stns if s in coord_keys]
    missing = [s for s in stns if s not in coord_keys]
    extra   = [k for k in coord_keys if k not in set(stns)]

    if missing:
        warnings.warn(
            f"rta.spatial: {len(missing)} station(s) have no coordinates: "
            f"{missing[:5]}{'...' if len(missing)>5 else ''}",
            UserWarning, stacklevel=2
        )

    return {
        "matched":  matched,
        "missing":  missing,
        "extra":    extra,
        "coverage": round(len(matched) / max(len(stns), 1), 4),
    }


def coords_to_df(coords: dict) -> pd.DataFrame:
    """
    Convert a coords dict to a tidy DataFrame with columns
    (Station, Lat, Lon).
    """
    rows = [{"Station": str(k), "Lat": v[0], "Lon": v[1]}
            for k, v in coords.items()]
    return pd.DataFrame(rows)
