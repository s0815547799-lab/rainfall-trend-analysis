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
from src.ensemble.daily_mme import export_daily_mme_excel
from src.validation.metrics import validation_metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")


# ── Input validation ──────────────────────────────────────────────────────────

def _check_inputs(cfg: dict) -> list[str]:
    """Return list of missing/unreadable inputs REQUIRED for computation.

    The boundary shapefile is required only for the figure/GIS stage
    (final_run.py), not for the core computational pipeline, so its absence
    is reported as a warning rather than a fatal error here (v3.5)."""
    errors = []
    for key, path in [
        ("observed",         cfg["paths"]["observed"]),
        ("station_metadata", cfg["paths"]["station_metadata"]),
    ]:
        if not Path(path).exists():
            errors.append(f"  MISSING: {key} → '{path}'")
    csv_dir = Path(cfg["paths"]["cmip6_csv"])
    if not csv_dir.is_dir():
        errors.append(f"  MISSING: cmip6_csv directory → '{csv_dir}'")
    bnd = Path(cfg["paths"]["boundary"])
    if not bnd.exists():
        log.warning("boundary shapefile not found ('%s') — computation will run; "
                    "figure/GIS stage (final_run.py) will require it.", bnd)
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
    min_yrs  = cfg.get("quality", {}).get("min_years_validate", 10)
    ssp_ts0  = cfg["periods"].get("ssp_timeseries_start", f0)
    ssp_end  = cfg["periods"].get("ssp_load_end", 2100)   # load full SSP for time series

    out = Path(cfg["paths"]["outputs"])
    (out / "excel").mkdir(parents=True, exist_ok=True)

    def _save_table(df: pd.DataFrame, stem: str) -> None:
        """Write Parquet when an engine is available, else fall back to CSV.

        Parquet is preferred for pipeline-resume, but the pipeline must not
        fail on environments lacking pyarrow/fastparquet (FIX, v3.5)."""
        try:
            df.to_parquet(out / "excel" / f"{stem}.parquet", index=False)
        except Exception as exc:
            df.to_csv(out / "excel" / f"{stem}.csv", index=False)
            log.warning("Parquet unavailable (%s); wrote %s.csv instead", exc, stem)

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
        y0_load, y1_load = (b0, b1) if r.scenario == "historical" else (ssp_ts0, ssp_end)
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
    _save_table(mme, "MME")

    # ── Validation metrics ────────────────────────────────────────────────────
    log.info("Computing validation metrics…")
    vm = pd.concat(
        [validation_metrics(obs, raw_mme, bc_mme, s, min_years=min_yrs)
         for s in ["Annual", "Wet", "Dry"]],
        ignore_index=True,
    )
    _save_table(vm, "Validation_Metrics")

    # ── Change% (BC near-future vs BC-historical baseline, per model) ─────────
    # FIX-A (v3.5): The projected-change signal is computed relative to EACH
    # model's OWN bias-corrected historical baseline (mean over b0–b1), then
    # aggregated across distinct models to MME mean/P25/P75.  This is the
    # standard CMIP6 "delta-change" definition.  The previous version used the
    # OBSERVED baseline as denominator, which folds any residual bias-correction
    # error into the change signal and is only valid if BC-hist == obs exactly.
    # We additionally report obs_baseline and bc_hist_baseline so the
    # equivalence (BC-hist ≈ obs over the calibration period) is auditable in
    # the manuscript.
    log.info("Computing change%% per model (near-future %d–%d vs model BC-baseline %d–%d)…",
             f0, f1, b0, b1)
    obs_mean = obs.groupby(["station", "season"]).rainfall.mean()

    # Per-model BC historical baseline mean over the baseline window
    bc_hist = per[(per.dataset == "BC") & (per.scenario == "historical")
                  & (per.year >= b0) & (per.year <= b1)]
    bc_hist_mean = (bc_hist.groupby(["model", "station", "season"])
                    .rainfall.mean())

    bc_fut = per[(per.dataset == "BC")
                 & per.scenario.isin(cfg["scenarios"])
                 & (per.year >= f0) & (per.year <= f1)]

    change_rows = []
    if not bc_fut.empty:
        model_fut = (bc_fut.groupby(["model", "scenario", "station", "season"])
                     .rainfall.mean().reset_index())
        for (scen, st, se), g in model_fut.groupby(["scenario", "station", "season"]):
            per_model_change = []
            for _, row in g.iterrows():
                base = bc_hist_mean.get((row.model, st, se), np.nan)
                if not (np.isfinite(base) and base > 0):
                    continue   # model lacks a usable historical baseline
                per_model_change.append((row.rainfall - base) / base * 100.0)
            valid = np.array([c for c in per_model_change if np.isfinite(c)])
            if valid.size == 0:
                continue
            ob = obs_mean.get((st, se), np.nan)
            bh = float(np.nanmean([bc_hist_mean.get((m, st, se), np.nan)
                                   for m in g.model.unique()]))
            change_rows.append({
                "station":          st,
                "season":           se,
                "scenario":         scen,
                "obs_baseline":     round(float(ob), 2) if np.isfinite(ob) else np.nan,
                "bc_hist_baseline": round(bh, 2) if np.isfinite(bh) else np.nan,
                "future_bc":        round(float(g.rainfall.mean()), 2),
                "change_pct":       round(float(np.mean(valid)), 2),
                "change_pct_p25":   round(float(np.percentile(valid, 25)), 2),
                "change_pct_p75":   round(float(np.percentile(valid, 75)), 2),
                "n_models":         int(valid.size),
            })
    else:
        log.warning("No BC near-future data found for scenarios %s; change%% table empty",
                    cfg["scenarios"])

    change = pd.DataFrame(change_rows)
    _save_table(change, "Change")

    # ── Interpolation skill: leave-one-out CV of the IDW ΔP% field ────────────
    # Answers the Q1 reviewer's key question — "why interpolate from N stations?"
    # Reports LOOCV RMSE/MAE (%) per scenario×season for the IDW power used in maps.
    def _idw_loocv(pts: np.ndarray, v: np.ndarray, power: float = 3.0):
        n = len(v)
        if n < 4:
            return np.nan, np.nan
        err = []
        for i in range(n):
            k = np.arange(n) != i
            d = np.sqrt(((pts[k] - pts[i]) ** 2).sum(1))
            d = np.where(d < 1e-9, 1e-9, d)
            w = 1.0 / d ** power
            err.append((w * v[k]).sum() / w.sum() - v[i])
        err = np.array(err)
        return float(np.sqrt(np.mean(err ** 2))), float(np.mean(np.abs(err)))

    meta_xy = meta.set_index("station")[["lon", "lat"]] if "station" in meta.columns else meta[["lon", "lat"]]
    skill_rows = []
    if not change.empty:
        for (scen, se), g in change.groupby(["scenario", "season"]):
            g = g[g.station.isin(meta_xy.index)]
            if len(g) < 4:
                continue
            pts = meta_xy.loc[g.station][["lon", "lat"]].to_numpy()
            v   = g.change_pct.to_numpy()
            rmse, mae = _idw_loocv(pts, v)
            skill_rows.append({"scenario": scen, "season": se, "n_stations": len(g),
                               "mean_abs_change_pct": round(float(np.mean(np.abs(v))), 2),
                               "LOOCV_RMSE_pct": round(rmse, 2),
                               "LOOCV_MAE_pct": round(mae, 2)})
    skill = pd.DataFrame(skill_rows)
    if not skill.empty:
        _save_table(skill, "Interpolation_Skill")
        log.info("IDW LOOCV skill (ΔP%%): median RMSE=%.2f%%, median MAE=%.2f%%",
                 float(skill.LOOCV_RMSE_pct.median()), float(skill.LOOCV_MAE_pct.median()))

    # ── Per-model change% (for inter-model spread & sign-agreement figures) ───
    cm_rows = []
    if not bc_fut.empty:
        mf = (bc_fut.groupby(["model", "scenario", "station", "season"])
              .rainfall.mean().reset_index())
        for _, row in mf.iterrows():
            base = bc_hist_mean.get((row.model, row.station, row.season), np.nan)
            if np.isfinite(base) and base > 0:
                cm_rows.append({
                    "model": row.model, "scenario": row.scenario,
                    "station": row.station, "season": row.season,
                    "change_pct": round((row.rainfall - base) / base * 100.0, 2),
                })
    change_models = pd.DataFrame(cm_rows)
    _save_table(change_models, "Change_per_model")

    # ── BC-vs-OBS baseline agreement diagnostic (manuscript auditability) ─────
    if not change.empty and change[["obs_baseline", "bc_hist_baseline"]].notna().all(axis=1).any():
        d = change.dropna(subset=["obs_baseline", "bc_hist_baseline"])
        rel = (d.bc_hist_baseline - d.obs_baseline).abs() / d.obs_baseline.replace(0, np.nan) * 100
        log.info("BC-hist vs OBS baseline agreement: median |Δ|=%.1f%%, max |Δ|=%.1f%% "
                 "(report in methods to justify the delta-change reference)",
                 float(rel.median()), float(rel.max()))

    # ── Master Excel ──────────────────────────────────────────────────────────
    area_code = cfg["study_area"]["province_code"]
    # Model roster per (dataset, scenario) — documents the ensemble composition
    roster = (per.groupby(["dataset", "scenario"])["model"]
              .agg(lambda s: ", ".join(sorted(s.unique())))
              .reset_index().rename(columns={"model": "models"}))
    roster["n_models"] = (per.groupby(["dataset", "scenario"])["model"]
                          .nunique().reset_index(drop=True))
    # ── Comprehensive analysis tables for Q1 submission ───────────────────────
    # Inter-model spread, sign-agreement, and per-station uncertainty
    unc = pd.DataFrame()
    if not change_models.empty:
        sd = (change_models.groupby(["scenario", "season", "station"]).change_pct
              .agg(inter_model_sd="std", n_models="count",
                   model_min="min", model_max="max").reset_index())
        mme_sign = (change[["scenario", "season", "station", "change_pct"]]
                    .rename(columns={"change_pct": "mme_change_pct"}))
        cmj = change_models.merge(mme_sign, on=["scenario", "season", "station"], how="left")
        cmj["agree"] = np.sign(cmj.change_pct) == np.sign(cmj.mme_change_pct)
        agr = (cmj.groupby(["scenario", "season", "station"]).agree.mean()
               .reset_index().rename(columns={"agree": "agreement_frac"}))
        unc = (sd.merge(agr, on=["scenario", "season", "station"], how="left")
               .merge(mme_sign, on=["scenario", "season", "station"], how="left"))
        for c in ["inter_model_sd", "model_min", "model_max", "agreement_frac", "mme_change_pct"]:
            unc[c] = unc[c].round(3)

    # Area-level headline summary per (scenario, season) — the paper's key table
    area_rows = []
    for (scen, se), g in change.groupby(["scenario", "season"]):
        cv = g.change_pct.dropna()
        row = {"scenario": scen, "season": se, "n_stations": int(len(g)),
               "mme_change_pct_mean": round(float(cv.mean()), 2) if len(cv) else np.nan,
               "change_p25": round(float(np.percentile(cv, 25)), 2) if len(cv) else np.nan,
               "change_p75": round(float(np.percentile(cv, 75)), 2) if len(cv) else np.nan,
               "station_min": round(float(cv.min()), 2) if len(cv) else np.nan,
               "station_max": round(float(cv.max()), 2) if len(cv) else np.nan}
        if not unc.empty:
            u = unc[(unc.scenario == scen) & (unc.season == se)]
            row["mean_inter_model_sd"] = round(float(u.inter_model_sd.mean()), 2) if len(u) else np.nan
            row["pct_stations_agree_ge70"] = round(100 * float((u.agreement_frac >= 0.7).mean()), 1) if len(u) else np.nan
        area_rows.append(row)
    area_summary = pd.DataFrame(area_rows)

    with pd.ExcelWriter(out / "excel" / f"MASTER_RESULTS_{area_code}.xlsx") as xw:
        area_summary.to_excel(xw, sheet_name="Area_Summary",  index=False)
        # Station index: Pnn ↔ station code ↔ coordinates/elevation (traceability)
        _m = meta.copy()
        _m["station"] = _m["station"].astype(str)
        _m = _m.sort_values("station").reset_index(drop=True)
        _m.insert(0, "label", [f"P{i+1:02d}" for i in range(len(_m))])
        _m.to_excel(xw, sheet_name="Stations", index=False)
        roster.to_excel(xw, sheet_name="Models",      index=False)
        vm.to_excel(xw, sheet_name="Validation",    index=False)
        for se in ["Annual", "Wet", "Dry"]:
            change[change.season == se].to_excel(xw, sheet_name=f"Change_{se}", index=False)
        if not change_models.empty:
            change_models.to_excel(xw, sheet_name="Change_per_model", index=False)
        if not unc.empty:
            unc.to_excel(xw, sheet_name="Uncertainty", index=False)
        if not skill.empty:
            skill.to_excel(xw, sheet_name="Interpolation_Skill", index=False)
        mme.to_excel(xw, sheet_name="MME_summary",  index=False)
        meta.to_excel(xw, sheet_name="Metadata",    index=False)

    cfg_version = cfg.get("config_version", "unknown")

    # ── Daily MME export (wide, like observed input) — Raw & BC ───────────────
    exp = cfg.get("export", {})
    daily_paths: list = []
    if exp.get("daily_mme_excel", True):
        which = exp.get("daily_mme_stations", "all")   # "all" | "observed"
        st_subset = sorted(obs_st) if which == "observed" else None
        last_ssp_year = exp.get("ssp_export_end", 2100)
        windows = {"historical": (b0, b1), "ssp": (ssp_ts0, last_ssp_year)}
        scen_list = ["historical"] + list(cfg["scenarios"])
        log.info("Exporting daily MME (wide, like observed) for datasets Raw & BC "
                 "(stations=%s, ssp end=%d)…", which, last_ssp_year)
        daily_paths = export_daily_mme_excel(
            files, out / "excel", ["Raw", "BC"], scen_list, windows,
            area_code, stations=st_subset)

    log.info("Pipeline complete: config_version=%s | MME=%d | validation=%d | change=%d "
             "| daily_mme_files=%d",
             cfg_version, len(mme), len(vm), len(change), len(daily_paths))

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
        "change_models": change_models,
    }


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CMIP6 MME Rainfall Projection — computation pipeline")
    parser.add_argument("--cfg", default="config/config.yaml",
                        help="Path to config YAML (default: config/config.yaml)")
    args = parser.parse_args()
    run(args.cfg)
