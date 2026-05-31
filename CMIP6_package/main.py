"""
main.py — CMIP6 MME Rainfall Projection Framework (Near Future).

End-to-end: validate inputs → build Raw/BC yearly per model → MME (mean/median/
P25/P75) → validation (KGE/NSE/PBIAS, Raw vs BC) → change (%) Annual/Wet/Dry →
Excel + inventories. Strict scope: Annual/Wet/Dry rainfall only; Near Future only.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.utils.io import load_config, discover_csv, load_metadata
from src.rainfall.seasonal import observed_yearly, cmip6_yearly
from src.ensemble.mme import build_mme
from src.validation.metrics import validation_metrics

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("main")


def run(cfg_path="config/config.yaml"):
    cfg = load_config(cfg_path)
    wet = cfg["seasons"]["wet_months"]; dry = cfg["seasons"]["dry_months"]
    b0, b1 = cfg["periods"]["baseline"]; f0, f1 = cfg["periods"]["near_future"]
    ssp_ts0 = cfg["periods"].get("ssp_timeseries_start", f0)  # Fig3 timeline start
    out = Path(cfg["paths"]["outputs"])
    (out / "excel").mkdir(parents=True, exist_ok=True)
    (out / "tables").mkdir(parents=True, exist_ok=True)

    # metadata (dynamic stations)
    meta = load_metadata(cfg["paths"]["station_metadata"])
    log.info("stations in metadata: %d", len(meta))

    # observed baseline
    obs = observed_yearly(cfg["paths"]["observed"], wet, dry, b0, b1)
    obs_st = set(obs.station.unique())
    meta = meta[meta.station.isin(obs_st)].reset_index(drop=True)

    # discover + build per-model yearly (historical baseline yrs + near future)
    files = discover_csv(cfg["paths"]["cmip6_csv"])
    per = []
    for _, r in files.iterrows():
        if r.scenario == "historical":
            y0, y1 = b0, b1
        else:
            # keep full ssp record from ssp_ts0..f1 so Figure 3 timeline is continuous
            # (change maps/tables still filter to near_future 2021-2050 downstream)
            y0, y1 = ssp_ts0, f1
        yd = cmip6_yearly(r.path, wet, dry, y0, y1)
        yd["dataset"] = "BC" if r.dataset == "BC" else "Raw"
        yd["model"] = r.model; yd["scenario"] = r.scenario
        per.append(yd)
    per = pd.concat(per, ignore_index=True)
    per = per[per.station.isin(obs_st)]
    log.info("per-model yearly rows: %d", len(per))

    # MME
    mme = build_mme(per)
    raw_mme = mme[mme.dataset == "Raw"]; bc_mme = mme[mme.dataset == "BC"]
    mme.to_parquet(out / "excel" / "MME.parquet", index=False)

    # validation metrics (Raw vs BC) per season
    vm = pd.concat([validation_metrics(obs, raw_mme, bc_mme, s) for s in ["Annual", "Wet", "Dry"]],
                   ignore_index=True)
    vm.to_parquet(out / "excel" / "Validation_Metrics.parquet", index=False)

    # change (%) Near Future BC-MME vs Observed baseline, per station/season/scenario
    obs_mean = obs.groupby(["station", "season"]).rainfall.mean().rename("obs_base")
    rows = []
    for scen in cfg["scenarios"]:
        fut = bc_mme[(bc_mme.scenario == scen) & (bc_mme.year >= f0) & (bc_mme.year <= f1)] \
            .groupby(["station", "season"])["mean"].mean()
        for (st, se), fv in fut.items():
            ob = obs_mean.get((st, se), np.nan)
            if ob and ob == ob and ob != 0:
                rows.append({"station": st, "season": se, "scenario": scen,
                             "obs_baseline": ob, "future_bc": fv,
                             "change_pct": round((fv - ob) / ob * 100, 2)})
    change = pd.DataFrame(rows)
    change.to_parquet(out / "excel" / "Change.parquet", index=False)

    # MASTER_RESULTS.xlsx (sheets)
    with pd.ExcelWriter(out / "excel" / "MASTER_RESULTS.xlsx") as xw:
        vm.to_excel(xw, sheet_name="Validation", index=False)
        for se in ["Annual", "Wet", "Dry"]:
            change[change.season == se].to_excel(xw, sheet_name=se, index=False)
        mme.to_excel(xw, sheet_name="Spatial", index=False)
        meta.to_excel(xw, sheet_name="Metadata", index=False)

    log.info("PIPELINE COMPLETE: MME=%d validation=%d change=%d", len(mme), len(vm), len(change))
    return {"meta": meta, "obs": obs, "per": per, "mme": mme, "raw_mme": raw_mme,
            "bc_mme": bc_mme, "vm": vm, "change": change, "cfg": cfg}


if __name__ == "__main__":
    run()
