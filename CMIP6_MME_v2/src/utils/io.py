"""utils.io — Config loading, CSV discovery, and metadata loading.

การปรับใช้กับพื้นที่ใหม่:
  - load_config: อ่าน config/config.yaml (ไม่ต้องแก้ไข)
  - discover_csv: ค้นหา CMIP6 CSV อัตโนมัติจาก folder (ไม่ต้องแก้ไข)
  - load_metadata: รองรับชื่อคอลัมน์ทั้ง upper/lowercase โดยอัตโนมัติ

รูปแบบชื่อไฟล์ CMIP6 CSV ที่รองรับ:
  Raw:  pr_day_<MODEL>_<scenario>_<realization>*.csv
  BC:   bc_pr_day_<MODEL>_<scenario>_<realization>*.csv

รูปแบบ metadata Excel ที่รองรับ (ชื่อคอลัมน์ case-insensitive):
  station / Station / STATION
  latitude / Latitude / lat / Lat
  longitude / Longitude / lon / Lon
  altitude / Altitude / elevation / Elevation / elev
"""
from __future__ import annotations

import re
import yaml
import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

def load_config(path: str | Path = "config/config.yaml") -> dict:
    """Load and return the YAML configuration."""
    with open(path) as f:
        cfg = yaml.safe_load(f)
    log.info("Config loaded: study_area=%s", cfg["study_area"]["name"])
    return cfg

# ── CSV Discovery ─────────────────────────────────────────────────────────────

# Accepts both lowercase and uppercase scenario tokens (ssp245, SSP245, SSP5-8.5).
# The $ anchor prevents matching filenames with extra suffixes after .csv.
_FN = re.compile(
    r"(bc_)?pr_day_(?P<model>[A-Za-z0-9\-]+)_(?P<scn>[A-Za-z0-9\-\.]+)_.*\.csv$",
    re.IGNORECASE,
)

def parse_csv(path: str | Path) -> dict | None:
    """Parse a single CMIP6 CSV filename → metadata dict, or None if not matched."""
    name = Path(path).name
    m = _FN.match(name)
    if not m:
        return None
    return {
        "dataset":  "BC" if m.group(1) else "Raw",
        "model":    m.group("model"),
        "scenario": m.group("scn").lower(),   # normalise to lowercase
        "path":     str(path),
    }

def discover_csv(csv_dir: str | Path) -> pd.DataFrame:
    """Recursively discover all CMIP6 CSV files in csv_dir.

    Returns DataFrame with columns: dataset, model, scenario, path.
    Skips files that do not match the expected naming pattern.
    """
    rows = [parse_csv(p) for p in Path(csv_dir).rglob("*.csv")]
    df = pd.DataFrame([r for r in rows if r])
    if df.empty:
        log.warning("discover_csv: no matching CSV files found in '%s'", csv_dir)
        return df
    log.info("discover_csv: %d files found (%d BC, %d Raw) | scenarios: %s",
             len(df),
             (df.dataset == "BC").sum(),
             (df.dataset == "Raw").sum(),
             sorted(df.scenario.unique()))
    return df

# ── Metadata Loading ──────────────────────────────────────────────────────────

# Mapping from all recognised column spellings → canonical name
_COL_MAP = {
    "station":   "station",
    "id":        "station",
    "station_id":"station",
    "latitude":  "lat",
    "lat":       "lat",
    "longitude": "lon",
    "lon":       "lon",
    "long":      "lon",
    "altitude":  "elevation",
    "elevation": "elevation",
    "elev":      "elevation",
    "dem":       "elevation",
    "height":    "elevation",
}
_REQUIRED = {"station", "lat", "lon", "elevation"}


def load_metadata(path: str | Path) -> pd.DataFrame:
    """Load station metadata from Excel file.

    Accepts any capitalisation of column names (Station, LATITUDE, etc.).
    Raises a clear KeyError if required columns are missing.

    Required columns (case-insensitive):
        station (or id / station_id)
        latitude (or lat)
        longitude (or lon / long)
        altitude  (or elevation / elev / dem / height)

    Returns DataFrame with columns: station (str), lat, lon, elevation.
    """
    suffix = Path(path).suffix.lower()
    if suffix in (".xlsx", ".xls"):
        d = pd.read_excel(path)
    elif suffix == ".csv":
        d = pd.read_csv(path)
    else:
        raise ValueError(f"load_metadata: unsupported file format '{suffix}'. Use .xlsx or .csv")

    # Normalise: strip whitespace, lowercase
    d.columns = [str(c).strip().lower() for c in d.columns]
    d = d.rename(columns=_COL_MAP)

    missing = _REQUIRED - set(d.columns)
    if missing:
        raise KeyError(
            f"load_metadata: missing columns {sorted(missing)} in '{path}'.\n"
            f"  Available columns (after normalisation): {sorted(d.columns)}\n"
            f"  Expected (case-insensitive): station, latitude, longitude, altitude"
        )

    d["station"] = d["station"].astype(str).str.strip()
    d["lat"]       = pd.to_numeric(d["lat"],       errors="coerce")
    d["lon"]       = pd.to_numeric(d["lon"],        errors="coerce")
    d["elevation"] = pd.to_numeric(d["elevation"],  errors="coerce")

    n_before = len(d)
    d = d.dropna(subset=["lat", "lon"])
    if len(d) < n_before:
        log.warning("load_metadata: dropped %d rows with missing lat/lon", n_before - len(d))

    log.info("load_metadata: %d stations loaded from '%s'", len(d), Path(path).name)
    return d[["station", "lat", "lon", "elevation"]]
