"""
src.tables.results — 3-level results architecture + publication tables.

Level 1: Station × Model  (per-station, per-model; Annual/Wet/Dry × scenarios) → station_model/
Level 2: Station × MME    (per-station MME + Change% + KGE/NSE/PBIAS)          → station_mme/
Level 3: Area summary      (study-area Observed/Hist-MME/SSP245/585 + Change%)  → area_summary/
Publication tables (Table_01..05 + S1,S2) with Mean/Std/Min/Max/Median/P25/P75.
No statistics changed — these reshape existing computed results.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

SEASONS = ["Annual", "Wet", "Dry"]
_STAT_COLS = ["mean", "std", "min", "max", "median", "p25", "p75"]


def _stat_block(s: pd.Series) -> dict:
    a = s.to_numpy(dtype=float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return {k: np.nan for k in _STAT_COLS}
    return {"mean": a.mean(), "std": a.std(ddof=1) if a.size > 1 else 0.0,
            "min": a.min(), "max": a.max(), "median": np.median(a),
            "p25": np.percentile(a, 25), "p75": np.percentile(a, 75)}


def level1_station_model(per: pd.DataFrame, out_dir: Path):
    """Per station: one file; rows = model×scenario×season yearly stats."""
    d = out_dir / "station_model"; d.mkdir(parents=True, exist_ok=True)
    files = []
    for st, g in per.groupby("station"):
        rows = []
        for (model, scen, se), gg in g.groupby(["model", "scenario", "season"]):
            rows.append({"model": model, "scenario": scen, "season": se,
                         "n_years": gg.year.nunique(), **_stat_block(gg.rainfall)})
        df = pd.DataFrame(rows)
        p = d / f"Station_{st}.xlsx"
        df.to_excel(p, index=False)
        files.append(p)
    log.info("level1 station_model: %d station files", len(files))
    return files


def level2_station_mme(bc_mme, raw_mme, vm, change, out_dir: Path, f0, f1):
    """Per station: MME stats (Annual/Wet/Dry × scenario) + Change% + validation."""
    d = out_dir / "station_mme"; d.mkdir(parents=True, exist_ok=True)
    rows = []
    for (st, se, scen), g in bc_mme.groupby(["station", "season", "scenario"]):
        if scen != "historical":
            g = g[(g.year >= f0) & (g.year <= f1)]
        rows.append({"station": st, "season": se, "scenario": scen, **_stat_block(g["mean"])})
    mme_stats = pd.DataFrame(rows)
    ch = change.rename(columns={"change_pct": "Change_%"})
    out = mme_stats.merge(ch[["station", "season", "scenario", "Change_%"]],
                          on=["station", "season", "scenario"], how="left")
    out = out.merge(vm, on=["station", "season"], how="left")
    p = d / "Station_MME_Results.xlsx"
    out.to_excel(p, index=False)
    log.info("level2 station_mme: %d rows", len(out))
    return [p], out


def level3_area_summary(obs, bc_mme, change, out_dir: Path, f0, f1):
    """Study-area summary: Observed/Hist-MME/SSP245/SSP585 per season + Change%."""
    d = out_dir / "area_summary"; d.mkdir(parents=True, exist_ok=True)
    rows = []
    for se in SEASONS:
        o = obs[obs.season == se].groupby("year").rainfall.mean()
        rows.append({"season": se, "source": "Observed", **_stat_block(o)})
        for scen in ["historical", "ssp245", "ssp585"]:
            m = bc_mme[(bc_mme.season == se) & (bc_mme.scenario == scen)]
            if scen != "historical":
                m = m[(m.year >= f0) & (m.year <= f1)]
            ser = m.groupby("year")["mean"].mean()
            blk = {"season": se, "source": f"BC-MME {scen}", **_stat_block(ser)}
            if scen in ("ssp245", "ssp585"):
                blk["Change_%"] = change[(change.season == se) & (change.scenario == scen)].change_pct.mean()
            rows.append(blk)
    df = pd.DataFrame(rows)
    p = d / "Area_Summary.xlsx"
    df.to_excel(p, index=False)
    log.info("level3 area_summary: %d rows", len(df))
    return [p], df


def publication_tables(meta, vm, change, per, station_mme, out_dir: Path):
    """Table_01..05 + S1,S2 with stat columns where applicable."""
    d = out_dir / "publication_tables"; d.mkdir(parents=True, exist_ok=True)
    paths = {}
    meta.to_excel(d / "Table_01_Station_Metadata.xlsx", index=False); paths["T1"] = d / "Table_01_Station_Metadata.xlsx"
    vm.to_excel(d / "Table_02_Validation_Metrics.xlsx", index=False); paths["T2"] = d / "Table_02_Validation_Metrics.xlsx"
    for n, se in [("03_Annual", "Annual"), ("04_Wet", "Wet"), ("05_Dry", "Dry")]:
        sub = change[change.season == se].copy()
        # add stat block of change across stations per scenario
        stat_rows = []
        for scen, g in sub.groupby("scenario"):
            stat_rows.append({"scenario": scen, **_stat_block(g.change_pct)})
        with pd.ExcelWriter(d / f"Table_{n}_Change.xlsx") as xw:
            sub.to_excel(xw, sheet_name="per_station", index=False)
            pd.DataFrame(stat_rows).to_excel(xw, sheet_name="summary", index=False)
        paths[n] = d / f"Table_{n}_Change.xlsx"
    # S1 model performance (per-model historical stats vs observed-area)
    s1 = []
    for (model, se), g in per[per.scenario == "historical"].groupby(["model", "season"]):
        ser = g.groupby("year").rainfall.mean()
        s1.append({"model": model, "season": se, **_stat_block(ser)})
    pd.DataFrame(s1).to_excel(d / "Table_S1_Model_Performance.xlsx", index=False)
    paths["S1"] = d / "Table_S1_Model_Performance.xlsx"
    # S2 station×model results (full)
    station_mme.to_excel(d / "Table_S2_Station_Model_Results.xlsx", index=False)
    paths["S2"] = d / "Table_S2_Station_Model_Results.xlsx"
    log.info("publication_tables: %d files", len(paths))
    return paths
