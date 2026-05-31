"""utils.io — config + dynamic discovery (no hard-coding)."""
from __future__ import annotations

import re
import yaml
import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)


def load_config(path: str = "config/config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


# Accept both lowercase and uppercase scenario tokens (e.g. ssp245 or SSP245).
# The `$` anchor prevents matching filenames with extra suffixes after the .csv.
_FN = re.compile(
    r"(bc_)?pr_day_(?P<model>[A-Za-z0-9\-]+)_(?P<scn>[A-Za-z0-9\-\.]+)_.*\.csv$",
    re.IGNORECASE,
)


def parse_csv(path: str | Path) -> dict | None:
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
    rows = [parse_csv(p) for p in Path(csv_dir).rglob("*.csv")]
    df = pd.DataFrame([r for r in rows if r])
    if len(df):
        log.info("discovered %d CSV files (%d BC, %d Raw)",
                 len(df),
                 (df.dataset == "BC").sum(),
                 (df.dataset == "Raw").sum())
    return df


# Required column names after normalisation (lowercase, stripped)
_REQUIRED = {"station", "lat", "lon", "elevation"}

# Map from normalised Excel column name → target name
_COL_MAP = {
    "station":   "station",
    "latitude":  "lat",
    "longitude": "lon",
    "lon":       "lon",
    "lat":       "lat",
    "altitude":  "elevation",
    "elevation": "elevation",
    "elev":      "elevation",
}


def load_metadata(path: str | Path) -> pd.DataFrame:
    d = pd.read_excel(path)
    # Normalise column names to lowercase, strip whitespace
    d.columns = [str(c).strip().lower() for c in d.columns]
    d = d.rename(columns=_COL_MAP)

    missing = _REQUIRED - set(d.columns)
    if missing:
        raise KeyError(
            f"load_metadata: missing columns {missing} in '{path}'. "
            f"Available (after normalisation): {list(d.columns)}"
        )

    d["station"] = d["station"].astype(str).str.strip()
    return d[["station", "lat", "lon", "elevation"]]
