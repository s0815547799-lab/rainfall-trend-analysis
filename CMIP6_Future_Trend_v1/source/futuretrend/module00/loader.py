"""
future_etccdi.module00.loader
=============================

Phase 1 — data layer for the future-change framework.

Reads the CSV dataset (Phetchaburi + Prachuap), discovers dataset / model /
scenario dynamically from filenames, removes 29-Feb, and produces a tidy frame:

    [dataset, model, scenario, station, date, pr]

dataset : "Raw" (pr_day_*) or "QDM" (bc_pr_day_*)
scenario : "historical", "ssp245", "ssp585", ... (never hard-coded)

Also provides future-window slicing (Near/Mid/Late) and an MME builder that
operates per (dataset, scenario).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .calendar_utils import remove_feb29

log = logging.getLogger(__name__)

__all__ = ["FutureFileSpec", "infer_future_filespec", "load_csv_wide_to_tidy",
           "load_dataset_dir", "build_mme", "slice_windows", "FUTURE_WINDOWS"]

# Future windows (approved). Overlapping, sliced from the continuous 2015-2100 series.
FUTURE_WINDOWS = {
    "Near": (2021, 2050),
    "Mid": (2041, 2070),
    "Late": (2071, 2100),
}


@dataclass
class FutureFileSpec:
    path: Path
    dataset: str     # Raw | QDM
    model: str
    scenario: str    # historical | ssp245 | ssp585 | ...


def infer_future_filespec(path: str | Path) -> FutureFileSpec:
    """Infer (dataset, model, scenario) from a CMIP6 CSV filename.

    Patterns:
        pr_day_<MODEL>_<SCENARIO>_...       -> Raw
        bc_pr_day_<MODEL>_<SCENARIO>_...    -> QDM
    Model and scenario are captured dynamically (no hard-coded names).
    """
    name = Path(path).name
    m = re.match(r"bc_pr_day_(.+?)_([A-Za-z0-9]+)_", name)
    if m:
        return FutureFileSpec(Path(path), "QDM", m.group(1), m.group(2))
    m = re.match(r"pr_day_(.+?)_([A-Za-z0-9]+)_", name)
    if m:
        return FutureFileSpec(Path(path), "Raw", m.group(1), m.group(2))
    raise ValueError(f"cannot infer dataset/model/scenario from: {name!r}")


def load_csv_wide_to_tidy(spec: FutureFileSpec) -> pd.DataFrame:
    """Load one wide CSV (YEAR,MONTH,DAY + station columns) into tidy long form."""
    df = pd.read_csv(spec.path)
    df = df.loc[:, [c for c in df.columns if not c.startswith("Unnamed")]]  # drop trailing comma col
    id_cols = ["YEAR", "MONTH", "DAY"]
    station_cols = [c for c in df.columns if c not in id_cols]
    long = df.melt(id_vars=id_cols, value_vars=station_cols,
                   var_name="station", value_name="pr")
    long["station"] = long["station"].astype(str).str.strip()
    long = long[long["station"].str.isdigit()]
    long["date"] = pd.to_datetime(dict(year=long.YEAR, month=long.MONTH, day=long.DAY),
                                  errors="coerce")
    long = long.dropna(subset=["date"])
    long["dataset"] = spec.dataset
    long["model"] = spec.model
    long["scenario"] = spec.scenario
    long, _ = remove_feb29(long, date_col="date")
    return long[["dataset", "model", "scenario", "station", "date", "pr"]]


def load_dataset_dir(root: str | Path) -> pd.DataFrame:
    """Discover and load every CSV under a directory tree into one tidy frame."""
    root = Path(root)
    files = sorted(root.rglob("*.csv"))
    frames = []
    seen = []
    for f in files:
        try:
            spec = infer_future_filespec(f)
        except ValueError:
            log.warning("skip unrecognized file: %s", f.name)
            continue
        frames.append(load_csv_wide_to_tidy(spec))
        seen.append((spec.dataset, spec.model, spec.scenario))
    tidy = pd.concat(frames, ignore_index=True)
    log.info("load_dataset_dir: %d files | models=%s scenarios=%s",
             len(seen), sorted({s[1] for s in seen}), sorted({s[2] for s in seen}))
    return tidy


def build_mme(tidy: pd.DataFrame) -> pd.DataFrame:
    """Append MME (pointwise mean across member models) per dataset & scenario."""
    parts = [tidy]
    for (ds, scn), sub in tidy.groupby(["dataset", "scenario"]):
        members = sub[sub["model"] != "MME"]
        if members["model"].nunique() < 1:
            continue
        mme = members.groupby(["station", "date"], as_index=False)["pr"].mean()
        mme["dataset"] = ds; mme["model"] = "MME"; mme["scenario"] = scn
        parts.append(mme[["dataset", "model", "scenario", "station", "date", "pr"]])
    return pd.concat(parts, ignore_index=True)


def slice_windows(tidy: pd.DataFrame) -> pd.DataFrame:
    """Tag each row with a 'window' label.

    historical rows -> window 'Historical'. Future (non-historical) rows are
    duplicated into each future window they fall into (windows overlap).
    """
    t = tidy.copy()
    t["year"] = pd.to_datetime(t["date"]).dt.year
    hist = t[t["scenario"] == "historical"].copy()
    hist["window"] = "Historical"
    out = [hist]
    fut = t[t["scenario"] != "historical"]
    for wname, (y0, y1) in FUTURE_WINDOWS.items():
        w = fut[(fut.year >= y0) & (fut.year <= y1)].copy()
        w["window"] = wname
        out.append(w)
    res = pd.concat(out, ignore_index=True)
    return res.drop(columns=["year"])
