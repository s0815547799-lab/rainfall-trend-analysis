"""tables.results — 3-level results architecture + Q1/Q2 publication tables (v3.7).

Scientific-reporting upgrades (v3.7)
------------------------------------
Projected-change tables now report the FULL uncertainty needed to interpret a
CMIP6 MME result, not just the ensemble-mean ΔP%:

  • inter-model spread    : SD (ddof=1), min, max across the N models
  • ensemble percentiles  : P25, P75 of the per-model changes
  • confidence interval   : 95% t-based CI of the mean across models
  • significance          : one-sample t-test of H0: ΔP%=0 (p-value)
  • model agreement       : fraction (and count) of models whose sign matches
                            the MME-mean sign  → robustness classification
  • robust / significant flags per station

Caveat (documented for the manuscript, not hidden): the N CMIP6 models are not
independent draws from a population ("model democracy"), so the t-based CI and
p-value are reported as indicative inferential summaries alongside the
distribution-free agreement fraction, which is the primary robustness measure.

New publication-critical tables
  Table_00_Model_Ensemble        — ensemble composition / provenance
  Table_01_Station_Metadata      — + Pnn label (+ data coverage if obs supplied)
  Table_06_Validation_Summary    — area-level distributional skill per season

Every station is reported in every per-station table (missing values flagged,
never silently dropped).
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

SEASONS  = ["Annual", "Wet", "Dry"]
_STAT_COLS = ["mean", "std", "min", "max", "median", "p25", "p75"]

# t critical values (two-sided 95%) for small samples; fallback when SciPy absent
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
        8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 15: 2.131,
        20: 2.086, 25: 2.060, 30: 2.042}


def _t_crit(df: int) -> float:
    if df <= 0:
        return np.nan
    try:
        from scipy.stats import t
        return float(t.ppf(0.975, df))
    except Exception:
        keys = sorted(_T95)
        for k in keys:
            if df <= k:
                return _T95[k]
        return 1.96


def _ttest_p_vs_zero(x: np.ndarray) -> float:
    """Two-sided one-sample t-test p-value (H0: mean=0). NaN if undefined."""
    x = x[np.isfinite(x)]
    n = x.size
    if n < 2:
        return np.nan
    sd = x.std(ddof=1)
    if sd == 0:
        return 0.0 if x.mean() != 0 else np.nan
    tstat = x.mean() / (sd / np.sqrt(n))
    try:
        from scipy.stats import t
        return float(2 * t.sf(abs(tstat), n - 1))
    except Exception:
        return np.nan  # p-value needs the t CDF; report CI instead


def _stat_block(s: pd.Series) -> dict:
    a = np.asarray(s, dtype=float); a = a[np.isfinite(a)]
    if a.size == 0:
        return {k: np.nan for k in _STAT_COLS}
    return {"mean": float(a.mean()),
            "std": float(a.std(ddof=1)) if a.size > 1 else np.nan,
            "min": float(a.min()), "max": float(a.max()),
            "median": float(np.median(a)),
            "p25": float(np.percentile(a, 25)),
            "p75": float(np.percentile(a, 75))}


def _ensemble_stats(vals: np.ndarray, thr: float) -> dict:
    """Full inter-model uncertainty for one (station, scenario, season).

    vals = per-model ΔP% (one value per model). Returns spread, CI, significance,
    and sign-agreement against the ensemble-mean sign.
    """
    v = np.asarray(vals, float); v = v[np.isfinite(v)]
    n = v.size
    if n == 0:
        return {k: np.nan for k in
                ("change_pct", "inter_model_sd", "model_min", "model_max",
                 "ens_p25", "ens_p75", "ci95_low", "ci95_high",
                 "ttest_p", "n_models", "n_models_agree", "agreement_frac",
                 "robust", "significant")}
    mean = float(v.mean())
    sd   = float(v.std(ddof=1)) if n > 1 else np.nan
    if n > 1 and np.isfinite(sd):
        half = _t_crit(n - 1) * sd / np.sqrt(n)
        ci_lo, ci_hi = mean - half, mean + half
    else:
        ci_lo = ci_hi = np.nan
    sign = np.sign(mean)
    n_agree = int(np.sum(np.sign(v) == sign)) if sign != 0 else int(np.sum(v == 0))
    agree_frac = n_agree / n
    p = _ttest_p_vs_zero(v)
    ci_excl_zero = np.isfinite(ci_lo) and (ci_lo > 0 or ci_hi < 0)
    return {
        "change_pct":     round(mean, 2),
        "inter_model_sd": round(sd, 2) if np.isfinite(sd) else np.nan,
        "model_min":      round(float(v.min()), 2),
        "model_max":      round(float(v.max()), 2),
        "ens_p25":        round(float(np.percentile(v, 25)), 2),
        "ens_p75":        round(float(np.percentile(v, 75)), 2),
        "ci95_low":       round(ci_lo, 2) if np.isfinite(ci_lo) else np.nan,
        "ci95_high":      round(ci_hi, 2) if np.isfinite(ci_hi) else np.nan,
        "ttest_p":        round(p, 4) if np.isfinite(p) else np.nan,
        "n_models":       int(n),
        "n_models_agree": n_agree,
        "agreement_frac": round(agree_frac, 3),
        "robust":         bool(agree_frac >= thr),
        "significant":    bool(np.isfinite(p) and p < 0.05) or bool(ci_excl_zero),
    }


# ── Level 1–3 (unchanged) ─────────────────────────────────────────────────────

def level1_station_model(per: pd.DataFrame, out_dir: Path) -> list[Path]:
    d = out_dir / "station_model"; d.mkdir(parents=True, exist_ok=True)
    files = []
    for st, g in per.groupby("station"):
        rows = []
        for (model, scen, se), gg in g.groupby(["model", "scenario", "season"]):
            rows.append({"model": model, "scenario": scen, "season": se,
                         "n_years": gg.year.nunique(), **_stat_block(gg.rainfall)})
        p = d / f"Station_{st}.xlsx"
        pd.DataFrame(rows).to_excel(p, index=False); files.append(p)
    log.info("level1_station_model: %d station files", len(files))
    return files


def level2_station_mme(bc_mme, raw_mme, vm, change, out_dir, f0, f1):
    d = out_dir / "station_mme"; d.mkdir(parents=True, exist_ok=True)
    rows = []
    for (st, se, scen), g in bc_mme.groupby(["station", "season", "scenario"]):
        if scen != "historical":
            g = g[(g.year >= f0) & (g.year <= f1)]
        rows.append({"station": st, "season": se, "scenario": scen,
                     **_stat_block(g["mean"])})
    mme_stats = pd.DataFrame(rows)
    ch = change.rename(columns={"change_pct": "Change_%"})
    out = mme_stats.merge(ch[["station", "season", "scenario", "Change_%"]],
                          on=["station", "season", "scenario"], how="left")
    out = out.merge(vm, on=["station", "season"], how="left")
    p = d / "Station_MME_Results.xlsx"; out.to_excel(p, index=False)
    log.info("level2_station_mme: %d rows", len(out))
    return [p], out


def level3_area_summary(obs, bc_mme, change, out_dir, f0, f1, scenarios=None):
    if scenarios is None:
        scenarios = sorted(bc_mme[bc_mme.scenario != "historical"].scenario.unique())
    d = out_dir / "area_summary"; d.mkdir(parents=True, exist_ok=True)
    rows = []
    for se in SEASONS:
        o = obs[obs.season == se].groupby("year").rainfall.mean()
        rows.append({"season": se, "source": "Observed", **_stat_block(o)})
        for scen in ["historical"] + scenarios:
            m = bc_mme[(bc_mme.season == se) & (bc_mme.scenario == scen)]
            if scen != "historical":
                m = m[(m.year >= f0) & (m.year <= f1)]
            ser = m.groupby("year")["mean"].mean()
            blk = {"season": se, "source": f"BC-MME {scen}", **_stat_block(ser)}
            if scen in scenarios:
                blk["Change_%"] = (change[(change.season == se)
                                          & (change.scenario == scen)].change_pct.mean())
            rows.append(blk)
    df = pd.DataFrame(rows); p = d / "Area_Summary.xlsx"; df.to_excel(p, index=False)
    log.info("level3_area_summary: %d rows", len(df))
    return [p], df


# ── Publication tables (Q1/Q2 upgraded) ───────────────────────────────────────

def publication_tables(meta: pd.DataFrame, vm: pd.DataFrame,
                       change: pd.DataFrame, per: pd.DataFrame,
                       station_mme: pd.DataFrame, out_dir: Path,
                       change_models: pd.DataFrame | None = None,
                       provenance: dict | None = None,
                       scenarios: list[str] | None = None,
                       agreement_threshold: float = 0.7,
                       obs: pd.DataFrame | None = None,
                       ) -> dict[str, Path]:
    """Write all publication tables with full uncertainty / significance reporting."""
    d = out_dir / "publication_tables"; d.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    change_models = change_models if change_models is not None else pd.DataFrame()
    scenarios = scenarios or sorted(change.scenario.unique())

    # stable Pnn labels (sorted by station code)
    all_st = sorted(meta["station"].astype(str).unique())
    label = {s: f"P{i+1:02d}" for i, s in enumerate(all_st)}

    # ── Table 00 — Ensemble composition / provenance ─────────────────────────
    prov = provenance or {}
    models = sorted(change_models.model.unique()) if not change_models.empty \
        else prov.get("models", [])
    scen_present = {m: ", ".join(sorted(change_models[change_models.model == m]
                                        .scenario.unique())) if not change_models.empty else ""
                    for m in models}
    t0 = pd.DataFrame({
        "model": models,
        "realization":  prov.get("realization", ""),
        "grid_label":   prov.get("grid_label", ""),
        "calendar":     prov.get("calendar", ""),
        "scenarios_used": [scen_present.get(m, "") for m in models],
        # fill from ESGF metadata before submission (not assumed here):
        "institution":      "",
        "native_resolution":"",
        "data_doi":     prov.get("bias_correction", {}).get("data_doi", "") if prov else "",
    })
    t0.to_excel(d / "Table_00_Model_Ensemble.xlsx", index=False)
    paths["T0"] = d / "Table_00_Model_Ensemble.xlsx"

    # ── Table 01 — Station metadata (+ Pnn, + coverage if obs given) ──────────
    m1 = meta.copy()
    m1["station"] = m1["station"].astype(str)
    m1.insert(0, "label", m1["station"].map(label))
    if obs is not None and not obs.empty:
        cov = []
        for st, g in obs.groupby("station"):
            row = {"station": str(st)}
            for se in SEASONS:
                gg = g[g.season == se].dropna(subset=["rainfall"])
                row[f"n_valid_{se}"]   = int(gg.year.nunique())
            yy = g.dropna(subset=["rainfall"]).year
            row["year_first"] = int(yy.min()) if len(yy) else np.nan
            row["year_last"]  = int(yy.max()) if len(yy) else np.nan
            cov.append(row)
        m1 = m1.merge(pd.DataFrame(cov), on="station", how="left")
    m1 = m1.sort_values("label").reset_index(drop=True)
    m1.to_excel(d / "Table_01_Station_Metadata.xlsx", index=False)
    paths["T1"] = d / "Table_01_Station_Metadata.xlsx"

    # ── Table 02 — Validation metrics (ALL stations; excluded ones flagged) ───
    full = pd.MultiIndex.from_product([all_st, SEASONS], names=["station", "season"])
    if vm is not None and not vm.empty:
        vm2 = vm.copy(); vm2["station"] = vm2["station"].astype(str)
        vm2 = vm2.set_index(["station", "season"]).reindex(full).reset_index()
        vm2["evaluated"] = vm2["n_years"].notna() if "n_years" in vm2 else False
    else:
        vm2 = full.to_frame(index=False)
        vm2["n_years"] = np.nan
        vm2["evaluated"] = False
    vm2.insert(0, "label", vm2["station"].astype(str).map(label))
    vm2.to_excel(d / "Table_02_Validation_Metrics.xlsx", index=False)
    paths["T2"] = d / "Table_02_Validation_Metrics.xlsx"

    # ── Tables 03–05 — Projected change with FULL uncertainty/significance ────
    base = change.set_index(["station", "season", "scenario"])
    for n, se in [("03_Annual", "Annual"), ("04_Wet", "Wet"), ("05_Dry", "Dry")]:
        rows = []
        for st in all_st:
            for scen in scenarios:
                row = {"label": label[st], "station": st,
                       "season": se, "scenario": scen}
                # baselines from change table (mean fields)
                if (st, se, scen) in base.index:
                    b = base.loc[(st, se, scen)]
                    row.update({"obs_baseline_mm":  b.get("obs_baseline", np.nan),
                                "bc_hist_baseline_mm": b.get("bc_hist_baseline", np.nan),
                                "future_bc_mm":     b.get("future_bc", np.nan)})
                # per-model ensemble statistics
                if not change_models.empty:
                    vals = change_models[(change_models.station == st)
                                         & (change_models.season == se)
                                         & (change_models.scenario == scen)].change_pct.to_numpy()
                else:
                    vals = np.array([])
                row.update(_ensemble_stats(vals, agreement_threshold))
                rows.append(row)
        per_station = pd.DataFrame(rows)

        # summary across stations + ensemble-spread + robustness counts
        srows = []
        for scen, g in per_station.groupby("scenario"):
            cv = g.change_pct.dropna()
            srows.append({
                "scenario": scen, "n_stations": int(len(g)),
                "station_mean_change_pct": round(float(cv.mean()), 2) if len(cv) else np.nan,
                "spatial_sd": round(float(cv.std(ddof=1)), 2) if len(cv) > 1 else np.nan,
                "spatial_p25": round(float(np.percentile(cv, 25)), 2) if len(cv) else np.nan,
                "spatial_p75": round(float(np.percentile(cv, 75)), 2) if len(cv) else np.nan,
                "spatial_min": round(float(cv.min()), 2) if len(cv) else np.nan,
                "spatial_max": round(float(cv.max()), 2) if len(cv) else np.nan,
                "mean_inter_model_sd": round(float(g.inter_model_sd.mean()), 2),
                "pct_stations_robust": round(100 * float(g.robust.mean()), 1),
                "pct_stations_significant": round(100 * float(g.significant.mean()), 1),
                "pct_increase": round(100 * float((cv > 0).mean()), 1) if len(cv) else np.nan,
                "pct_decrease": round(100 * float((cv < 0).mean()), 1) if len(cv) else np.nan,
            })
        with pd.ExcelWriter(d / f"Table_{n}_Change.xlsx") as xw:
            per_station.to_excel(xw, sheet_name="per_station", index=False)
            pd.DataFrame(srows).to_excel(xw, sheet_name="summary", index=False)
        paths[n] = d / f"Table_{n}_Change.xlsx"

    # ── Table 06 — Area-level validation summary (distributional skill) ───────
    if not vm.empty:
        vs = []
        for se in SEASONS:
            a = vm[vm.season == se]
            def _med(col):
                return round(float(a[col].median()), 3) if col in a and len(a) else np.nan
            vs.append({
                "season": se, "n_stations_evaluated": int(len(a)),
                "median_PBIAS_BC_%": _med("PBIAS_BC"),
                "median_abs_PBIAS_BC_%": round(float(a["PBIAS_BC"].abs().median()), 3) if "PBIAS_BC" in a and len(a) else np.nan,
                "median_SDratio_BC": _med("SDratio_BC"),
                "median_PSS_BC": _med("PSS_BC"),
                "pct_stations_absPBIAS_lt10": round(100 * float((a["PBIAS_BC"].abs() < 10).mean()), 1) if "PBIAS_BC" in a and len(a) else np.nan,
            })
        pd.DataFrame(vs).to_excel(d / "Table_06_Validation_Summary.xlsx", index=False)
        paths["T6"] = d / "Table_06_Validation_Summary.xlsx"

    # ── Table S1 — per-model historical statistics ───────────────────────────
    if per is not None and not per.empty and "scenario" in per.columns:
        s1 = []
        for (model, se), g in per[per.scenario == "historical"].groupby(["model", "season"]):
            ser = g.groupby("year").rainfall.mean()
            s1.append({"model": model, "season": se, **_stat_block(ser)})
        pd.DataFrame(s1).to_excel(d / "Table_S1_Model_Performance.xlsx", index=False)
        paths["S1"] = d / "Table_S1_Model_Performance.xlsx"

    # ── Table S2 — full station MME results ──────────────────────────────────
    if station_mme is not None and not station_mme.empty:
        station_mme.to_excel(d / "Table_S2_Station_Model_Results.xlsx", index=False)
        paths["S2"] = d / "Table_S2_Station_Model_Results.xlsx"

    log.info("publication_tables: %d files (incl. ensemble, coverage, validation-summary)",
             len(paths))
    return paths
