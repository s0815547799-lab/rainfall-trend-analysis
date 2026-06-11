"""
main.py — CMIP6 MME Rainfall Projection Framework (end-to-end pipeline).

Pipeline:
  1. Load config
  2. Load station metadata + observed data
  3. Discover + load CMIP6 model CSVs (Raw + BC)
  4. Aggregate to yearly seasonal totals (Annual/Wet/Dry)
  5. Build Raw MME and BC-MME (mean/median/P25/P75)
  6. Compute validation metrics (KGE/NSE/PBIAS, Raw vs BC)
  7. Compute change% (BC near-future vs observed baseline)
  8. Save intermediate results to Excel + Parquet

วิธีรัน:
  python main.py                      # ใช้ config/config.yaml
  python main.py --cfg path/to/config.yaml

ดูผลลัพธ์ทั้งหมดได้ที่ outputs/ หรือ run final_run.py เพื่อผลลัพธ์ระดับ publication
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.utils.io      import load_config, discover_csv, load_metadata
from src.rainfall.seasonal import observed_yearly, cmip6_yearly
from src.ensemble.mme      import build_mme
from src.validation.metrics import validation_metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")


# ── Input validation ──────────────────────────────────────────────────────────

def _check_inputs(cfg: dict) -> list[str]:
    """Return list of missing/unreadable required files."""
    errors = []
    for key, path in [
        ("observed",         cfg["paths"]["observed"]),
        ("station_metadata", cfg["paths"]["station_metadata"]),
        ("boundary",         cfg["paths"]["boundary"]),
    ]:
        if not Path(path).exists():
            errors.append(f"  MISSING: {key} → '{path}'")
    csv_dir = Path(cfg["paths"]["cmip6_csv"])
    if not csv_dir.is_dir():
        errors.append(f"  MISSING: cmip6_csv directory → '{csv_dir}'")
    return errors


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run(cfg_path: str = "config/config.yaml") -> dict:
    """Execute the full computation pipeline and return all results as a dict.

    Parameters
    ----------
    cfg_path : path to config YAML (default: config/config.yaml)

    Returns
    -------
    dict with keys:
        cfg, meta, obs, per, mme, raw_mme, bc_mme, vm, change
    """
    cfg = load_config(cfg_path)
    log.info("=" * 60)
    log.info("Study area : %s", cfg["study_area"]["name"])
    log.info("Baseline   : %s – %s", *cfg["periods"]["baseline"])
    log.info("Near future: %s – %s", *cfg["periods"]["near_future"])
    log.info("Scenarios  : %s", cfg["scenarios"])
    log.info("=" * 60)

    # Validate inputs
    errors = _check_inputs(cfg)
    if errors:
        log.error("Input validation FAILED:\n%s", "\n".join(errors))
        log.error("Please check config.yaml paths and ensure all data files exist.")
        sys.exit(1)

    wet  = cfg["seasons"]["wet_months"]
    dry  = cfg["seasons"]["dry_months"]
    b0, b1 = cfg["periods"]["baseline"]
    f0, f1 = cfg["periods"]["near_future"]
    min_comp = cfg.get("quality", {}).get("min_completeness", 0.80)
    min_yrs  = cfg.get("quality", {}).get("min_years_validate", 2)
    ssp_ts0  = cfg["periods"].get("ssp_timeseries_start", f0)

    out = Path(cfg["paths"]["outputs"])
    (out / "excel").mkdir(parents=True, exist_ok=True)

    # ── Station metadata ──────────────────────────────────────────────────────
    meta = load_metadata(cfg["paths"]["station_metadata"])
    log.info("Metadata: %d stations", len(meta))

    # ── Observed data ─────────────────────────────────────────────────────────
    log.info("Loading observed data (%d–%d)…", b0, b1)
    obs = observed_yearly(cfg["paths"]["observed"], wet, dry, b0, b1,
                          min_completeness=min_comp)
    obs_st = set(obs.station.unique())
    log.info("Observed: %d station-year-season rows | %d stations",
             len(obs), len(obs_st))

    # Filter metadata to stations present in observations
    meta = meta[meta.station.isin(obs_st)].reset_index(drop=True)
    log.info("Metadata after filter: %d stations", len(meta))

    # ── CMIP6 model files ─────────────────────────────────────────────────────
    log.info("Discovering CMIP6 CSV files in '%s'…", cfg["paths"]["cmip6_csv"])
    files = discover_csv(cfg["paths"]["cmip6_csv"])
    if files.empty:
        log.error("No CMIP6 CSV files found. Exiting.")
        sys.exit(1)

    per_list = []
    for _, r in files.iterrows():
        y0_load, y1_load = (b0, b1) if r.scenario == "historical" else (ssp_ts0, f1)
        try:
            yd = cmip6_yearly(r.path, wet, dry, y0_load, y1_load,
                              min_completeness=min_comp)
        except Exception as exc:
            log.warning("Skipping '%s': %s", Path(r.path).name, exc)
            continue

        # ── CMIP6 period coverage validation (CLAUDE.md §12.5) ────────────
        # Warn and exclude models that do not span the full required period.
        if not yd.empty:
            ann_years = yd[yd.season == "Annual"].year.unique()
            if len(ann_years) > 0:
                req_start = b0 if r.scenario == "historical" else f0
                req_end   = b1 if r.scenario == "historical" else f1
                if int(ann_years.min()) > req_start or int(ann_years.max()) < req_end:
                    log.warning(
                        "Excluding '%s' (scenario=%s, dataset=%s): "
                        "Annual coverage [%d–%d] does not span required [%d–%d]",
                        Path(r.path).name, r.scenario, r.dataset,
                        int(ann_years.min()), int(ann_years.max()),
                        req_start, req_end,
                    )
                    continue
        # ──────────────────────────────────────────────────────────────────

        yd["dataset"]  = r.dataset
        yd["model"]    = r.model
        yd["scenario"] = r.scenario
        per_list.append(yd)

    if not per_list:
        log.error("No model data loaded successfully. Exiting.")
        sys.exit(1)

    per = pd.concat(per_list, ignore_index=True)
    per = per[per.station.isin(obs_st)]
    log.info("Per-model data: %d rows | %d models",
             len(per), per.model.nunique())

    # ── Multi-Model Ensemble ──────────────────────────────────────────────────
    log.info("Building MME…")
    mme     = build_mme(per)
    raw_mme = mme[mme.dataset == "Raw"].copy()
    bc_mme  = mme[mme.dataset == "BC"].copy()
    mme.to_parquet(out / "excel" / "MME.parquet", index=False)

    # ── Validation metrics ────────────────────────────────────────────────────
    log.info("Computing validation metrics…")
    vm = pd.concat(
        [validation_metrics(obs, raw_mme, bc_mme, s, min_years=min_yrs)
         for s in ["Annual", "Wet", "Dry"]],
        ignore_index=True,
    )
    vm.to_parquet(out / "excel" / "Validation_Metrics.parquet", index=False)

    # ── Change% (BC near-future vs observed baseline) ─────────────────────────
    # Per CLAUDE.md §12.5: change% computed per-model first, then aggregated to
    # MME statistics (mean, P25, P75).  Computing change% on the MME mean
    # conflates inter-model spread with the change signal.
    log.info("Computing change%% per model (near-future %d–%d vs baseline %d–%d)…",
             f0, f1, b0, b1)
    obs_mean = obs.groupby(["station", "season"]).rainfall.mean()

    bc_fut = per[(per.dataset == "BC")
                 & per.scenario.isin(cfg["scenarios"])
                 & (per.year >= f0) & (per.year <= f1)]

    change_rows = []
    if not bc_fut.empty:
        model_fut = (bc_fut.groupby(["model", "scenario", "station", "season"])
                     .rainfall.mean().reset_index())
        for (scen, st, se), g in model_fut.groupby(["scenario", "station", "season"]):
            ob = obs_mean.get((st, se), np.nan)
            if not (np.isfinite(ob) and ob > 0):
                continue
            per_pct = ((g.rainfall.values - ob) / ob * 100)
            valid   = per_pct[np.isfinite(per_pct)]
            if len(valid) == 0:
                continue
            change_rows.append({
                "station":        st,
                "season":         se,
                "scenario":       scen,
                "obs_baseline":   round(float(ob), 2),
                "future_bc":      round(float(g.rainfall.values.mean()), 2),
                "change_pct":     round(float(np.mean(valid)), 2),
                "change_pct_p25": round(float(np.percentile(valid, 25)), 2),
                "change_pct_p75": round(float(np.percentile(valid, 75)), 2),
                "n_models":       int(len(valid)),
            })
    else:
        log.warning("No BC near-future data found for scenarios %s; change%% table empty",
                    cfg["scenarios"])

    change = pd.DataFrame(change_rows)
    change.to_parquet(out / "excel" / "Change.parquet", index=False)

    # ── Master Excel ──────────────────────────────────────────────────────────
    area_code = cfg["study_area"]["province_code"]
    with pd.ExcelWriter(out / "excel" / f"MASTER_RESULTS_{area_code}.xlsx") as xw:
        vm.to_excel(xw, sheet_name="Validation",    index=False)
        for se in ["Annual", "Wet", "Dry"]:
            change[change.season == se].to_excel(xw, sheet_name=se, index=False)
        mme.to_excel(xw, sheet_name="MME_summary",  index=False)
        meta.to_excel(xw, sheet_name="Metadata",    index=False)

    cfg_version = cfg.get("config_version", "unknown")
    log.info("Pipeline complete: config_version=%s | MME=%d | validation=%d | change=%d",
             cfg_version, len(mme), len(vm), len(change))

    return {
        "cfg":     cfg,
        "meta":    meta,
        "obs":     obs,
        "per":     per,
        "mme":     mme,
        "raw_mme": raw_mme,
        "bc_mme":  bc_mme,
        "vm":      vm,
        "change":  change,
    }


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CMIP6 MME Rainfall Projection — computation pipeline")
    parser.add_argument("--cfg", default="config/config.yaml",
                        help="Path to config YAML (default: config/config.yaml)")
    args = parser.parse_args()
    run(args.cfg)
