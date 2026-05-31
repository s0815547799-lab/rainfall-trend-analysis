"""tables.results — 3-level results architecture + publication tables.

Level 1: Station × Model   → station_model/Station_<ID>.xlsx
Level 2: Station × MME     → station_mme/Station_MME_Results.xlsx
Level 3: Area summary      → area_summary/Area_Summary.xlsx
Publication tables:
  Table_01_Station_Metadata.xlsx
  Table_02_Validation_Metrics.xlsx
  Table_03_Annual_Change.xlsx
  Table_04_Wet_Change.xlsx
  Table_05_Dry_Change.xlsx
  Table_S1_Model_Performance.xlsx
  Table_S2_Station_Model_Results.xlsx
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

SEASONS  = ["Annual", "Wet", "Dry"]
_STAT_COLS = ["mean", "std", "min", "max", "median", "p25", "p75"]


def _stat_block(s: pd.Series) -> dict:
    """Summary statistics for a numeric series (sample std, ddof=1)."""
    a = s.to_numpy(dtype=float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return {k: np.nan for k in _STAT_COLS}
    return {
        "mean":   float(a.mean()),
        "std":    float(a.std(ddof=1)) if a.size > 1 else np.nan,
        "min":    float(a.min()),
        "max":    float(a.max()),
        "median": float(np.median(a)),
        "p25":    float(np.percentile(a, 25)),
        "p75":    float(np.percentile(a, 75)),
    }


# ── Level 1: Station × Model ──────────────────────────────────────────────────

def level1_station_model(per: pd.DataFrame, out_dir: Path) -> list[Path]:
    """One Excel file per station; rows = model × scenario × season statistics."""
    d = out_dir / "station_model"
    d.mkdir(parents=True, exist_ok=True)
    files = []
    for st, g in per.groupby("station"):
        rows = []
        for (model, scen, se), gg in g.groupby(["model", "scenario", "season"]):
            rows.append({"model": model, "scenario": scen, "season": se,
                         "n_years": gg.year.nunique(),
                         **_stat_block(gg.rainfall)})
        df = pd.DataFrame(rows)
        p  = d / f"Station_{st}.xlsx"
        df.to_excel(p, index=False)
        files.append(p)
    log.info("level1_station_model: %d station files", len(files))
    return files


# ── Level 2: Station × MME ────────────────────────────────────────────────────

def level2_station_mme(bc_mme: pd.DataFrame, raw_mme: pd.DataFrame,
                       vm: pd.DataFrame, change: pd.DataFrame,
                       out_dir: Path, f0: int, f1: int,
                       ) -> tuple[list[Path], pd.DataFrame]:
    """Per-station MME statistics + Change% + validation metrics."""
    d = out_dir / "station_mme"
    d.mkdir(parents=True, exist_ok=True)

    rows = []
    for (st, se, scen), g in bc_mme.groupby(["station", "season", "scenario"]):
        if scen != "historical":
            g = g[(g.year >= f0) & (g.year <= f1)]
        rows.append({"station": st, "season": se, "scenario": scen,
                     **_stat_block(g["mean"])})
    mme_stats = pd.DataFrame(rows)

    ch  = change.rename(columns={"change_pct": "Change_%"})
    out = mme_stats.merge(
        ch[["station", "season", "scenario", "Change_%"]],
        on=["station", "season", "scenario"], how="left",
    )
    out = out.merge(vm, on=["station", "season"], how="left")

    p = d / "Station_MME_Results.xlsx"
    out.to_excel(p, index=False)
    log.info("level2_station_mme: %d rows", len(out))
    return [p], out


# ── Level 3: Area summary ─────────────────────────────────────────────────────

def level3_area_summary(obs: pd.DataFrame, bc_mme: pd.DataFrame,
                        change: pd.DataFrame,
                        out_dir: Path, f0: int, f1: int,
                        scenarios: list[str] | None = None,
                        ) -> tuple[list[Path], pd.DataFrame]:
    """Study-area summary: Observed / Hist-BC / SSP245 / SSP585 per season + Change%."""
    if scenarios is None:
        scenarios = sorted(bc_mme[bc_mme.scenario != "historical"].scenario.unique())
    d = out_dir / "area_summary"
    d.mkdir(parents=True, exist_ok=True)
    rows = []
    for se in SEASONS:
        o   = obs[obs.season == se].groupby("year").rainfall.mean()
        rows.append({"season": se, "source": "Observed", **_stat_block(o)})
        for scen in ["historical"] + scenarios:
            m = bc_mme[(bc_mme.season == se) & (bc_mme.scenario == scen)]
            if scen != "historical":
                m = m[(m.year >= f0) & (m.year <= f1)]
            ser = m.groupby("year")["mean"].mean()
            blk = {"season": se, "source": f"BC-MME {scen}", **_stat_block(ser)}
            if scen in scenarios:
                blk["Change_%"] = (change[(change.season == se)
                                          & (change.scenario == scen)]
                                   .change_pct.mean())
            rows.append(blk)
    df = pd.DataFrame(rows)
    p  = d / "Area_Summary.xlsx"
    df.to_excel(p, index=False)
    log.info("level3_area_summary: %d rows", len(df))
    return [p], df


# ── Publication tables ────────────────────────────────────────────────────────

def publication_tables(meta: pd.DataFrame, vm: pd.DataFrame,
                       change: pd.DataFrame, per: pd.DataFrame,
                       station_mme: pd.DataFrame,
                       out_dir: Path) -> dict[str, Path]:
    """Write Tables 01–05 and S1, S2 for publication."""
    d = out_dir / "publication_tables"
    d.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    # Table 01 — Station metadata
    meta.to_excel(d / "Table_01_Station_Metadata.xlsx", index=False)
    paths["T1"] = d / "Table_01_Station_Metadata.xlsx"

    # Table 02 — Validation metrics (Annual season as primary)
    vm.to_excel(d / "Table_02_Validation_Metrics.xlsx", index=False)
    paths["T2"] = d / "Table_02_Validation_Metrics.xlsx"

    # Tables 03–05 — Change% per season
    for n, se in [("03_Annual", "Annual"), ("04_Wet", "Wet"), ("05_Dry", "Dry")]:
        sub = change[change.season == se].copy()
        stat_rows = []
        for scen, g in sub.groupby("scenario"):
            stat_rows.append({"scenario": scen, **_stat_block(g.change_pct)})
        with pd.ExcelWriter(d / f"Table_{n}_Change.xlsx") as xw:
            sub.to_excel(xw, sheet_name="per_station", index=False)
            pd.DataFrame(stat_rows).to_excel(xw, sheet_name="summary", index=False)
        paths[n] = d / f"Table_{n}_Change.xlsx"

    # Table S1 — Per-model historical performance
    s1 = []
    for (model, se), g in per[per.scenario == "historical"].groupby(["model", "season"]):
        ser = g.groupby("year").rainfall.mean()
        s1.append({"model": model, "season": se, **_stat_block(ser)})
    pd.DataFrame(s1).to_excel(d / "Table_S1_Model_Performance.xlsx", index=False)
    paths["S1"] = d / "Table_S1_Model_Performance.xlsx"

    # Table S2 — Full station MME results
    station_mme.to_excel(d / "Table_S2_Station_Model_Results.xlsx", index=False)
    paths["S2"] = d / "Table_S2_Station_Model_Results.xlsx"

    log.info("publication_tables: %d files written", len(paths))
    return paths
