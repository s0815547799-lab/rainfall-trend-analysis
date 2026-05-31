"""
futuretrend.assemble — build yearly series from validated outputs (reuse only).

Produces a unified long table [variable, scenario, window, station, model, year,
value] for three sources, all already validated:
  - ETCCDI extremes  (Future_ETCCDI.parquet)   → Rx1day,Rx5day,R95pTOT,R99pTOT,CDD,CWD,SDII
  - SPI drought      (SPI_Assessment.parquet)   → SPI-3,SPI-6,SPI-12 (annual mean per year)
  - Rainfall totals  (recomputed yearly, reuse) → Annual,Wet,Dry  [optional source]

No recomputation of indices; we only reshape validated per-year values and tag
the future window each year belongs to. Dynamic: models/scenarios/stations from data.
"""

from __future__ import annotations

import logging
import pandas as pd

log = logging.getLogger(__name__)

FUTURE_WINDOWS = {"Near": (2021, 2050), "Mid": (2041, 2070), "Late": (2071, 2100)}
ETCCDI_VARS = ["Rx1day", "Rx5day", "R95pTOT", "R99pTOT", "CDD", "CWD", "SDII"]
SPI_VARS = ["SPI-3", "SPI-6", "SPI-12"]


def _tag_windows(df):
    out = []
    for w, (y0, y1) in FUTURE_WINDOWS.items():
        s = df[(df.year >= y0) & (df.year <= y1)].copy()
        s["window"] = w
        out.append(s)
    return pd.concat(out, ignore_index=True)


def from_etccdi(path, dataset="QDM"):
    idx = pd.read_parquet(path)
    idx = idx[(idx.dataset == dataset) & (idx.scenario != "historical") &
              (idx["index"].isin(ETCCDI_VARS))]
    idx = idx.rename(columns={"index": "variable"})
    df = idx[["variable", "scenario", "station", "model", "year", "value"]].copy()
    df["station"] = df["station"].astype(str)
    return _tag_windows(df)


def from_spi(path, dataset="QDM"):
    spi = pd.read_parquet(path, columns=["dataset", "scenario", "station", "model",
                                         "year", "spi_scale", "spi"])
    spi = spi[(spi.dataset == dataset) & (spi.scenario != "historical") &
              (spi.spi_scale.isin(SPI_VARS))]
    # annual mean SPI per year (from monthly SPI)
    g = (spi.groupby(["spi_scale", "scenario", "station", "model", "year"], as_index=False)
         .spi.mean().rename(columns={"spi_scale": "variable", "spi": "value"}))
    g["station"] = g["station"].astype(str)
    return _tag_windows(g)


def assemble(etccdi_path=None, spi_path=None):
    parts = []
    if etccdi_path:
        parts.append(from_etccdi(etccdi_path))
        log.info("assembled ETCCDI variables")
    if spi_path:
        parts.append(from_spi(spi_path))
        log.info("assembled SPI variables")
    out = pd.concat(parts, ignore_index=True)
    log.info("assemble: %d yearly rows, %d variables", len(out), out.variable.nunique())
    return out
