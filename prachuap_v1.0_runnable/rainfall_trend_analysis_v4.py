"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  Rainfall Trend Analysis — Publication Edition v4.0                         ║
║  Study: Phetchaburi–Prachuap Khiri Khan River Basin, Western Thailand       ║
║  Period: 1981–2014  |  Daily Rainfall Data                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Q1-upgrade additions over v3:                                              ║
║    • PW-MK   : Prewhitening (Yue & Wang 2004)                               ║
║    • TFPW-MK : Trend-Free Prewhitening (Yue et al. 2002)                   ║
║    • 4-Method comparison table (MK / MMK / PW-MK / TFPW-MK)               ║
║    • Field significance (Walker 1914 + Livezey-Chen 1983 Monte Carlo)      ║
║    • Dry-season hydrological year validation                                ║
║    • Checkpoint / resume system                                             ║
║    • Station coordinates support (spatial maps)                             ║
║    • 6 new publication figures (Fig 9–14)                                  ║
║    • 9-sheet Excel (6 original + 3 new sheets)                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Backward compatibility:                                                    ║
║    • All Output_TrendV2_* files still generated (identical to v3)          ║
║    • New outputs use Output_TrendV4_* prefix                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Usage:                                                                     ║
║    python rainfall_trend_analysis_v4.py [folder] [--no-resume] [--no-pdf]  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import math
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── rta package ───────────────────────────────────────────────────────────────
from rta.config import (VERSION, C, SCALE_META, DPI, SAVE_PDF,
                         Z_005, Z_001, ALPHA_005, ALPHA_001, savefig)
from rta.io import (find_csv, load_daily, quality_control,
                    save_checkpoint, load_checkpoint, list_checkpoints,
                    load_coords)
from rta.aggregation import aggregate_all, descriptive_stats, validate_dry_season
from rta.autocorr import lag_k_autocorr, all_lag_autocorr, is_sig_autocorr
from rta.trend_tests import standard_mk, modified_mk, pw_mk, tfpw_mk, sens_slope
from rta.batch import (run_all, build_comparison, build_4method_comparison,
                       METHOD_FN)
from rta.field_sig import walker_test, livezey_chen_mc, field_sig_summary

# Original v3 figures (generate Output_TrendV2_* outputs)
from rta.figures.timeseries import fig1_annual_ts, fig2_wetdry_ts
from rta.figures.bars import fig3_sens_all
from rta.figures.comparison import fig4_mk_vs_mmk
from rta.figures.heatmaps import fig5_significance_heatmap
from rta.figures.acf_plots import fig6_autocorrelation
from rta.figures.climatology import fig7_monthly_climatology
from rta.figures.spatial import fig8_spatial_summary

# New v4 figures (generate Output_TrendV4_* outputs)
from rta.figures.taylor import fig9_taylor_diagram
from rta.figures.method_comparison import (fig10_z_comparison_matrix,
                                           fig11_method_comparison_scatter)
from rta.figures.acf_plots import fig12_acf_diagnostics
from rta.figures.field_sig_plot import fig13_field_significance
from rta.figures.spatial_maps import (fig14_spatial_maps,
                                      fig_station_distribution,
                                      fig_spatial_methods,
                                      fig_spatial_field_sig,
                                      fig_spatial_full)

# Output modules
from rta.excel_output import write_excel
from rta.markdown import write_summary_md


def short_labels(stns):
    return {str(s): f"S{i+1}" for i, s in enumerate(stns)}


def _parse_args():
    """Parse CLI arguments: [folder] [--no-resume] [--no-pdf]"""
    args = sys.argv[1:]
    folder = None
    no_resume = False
    no_pdf = False
    for a in args:
        if a == "--no-resume":
            no_resume = True
        elif a == "--no-pdf":
            no_pdf = True
        elif not a.startswith("--"):
            folder = a.strip('"').strip("'")
    if folder is None:
        try:
            folder = str(Path(os.path.abspath(__file__)).parent)
        except Exception:
            folder = os.getcwd()
    return folder, no_resume, no_pdf


def main():
    SEP = "═" * 76
    print(SEP)
    print(f"  Rainfall Trend Analysis  v{VERSION}  — Q1 Publication Edition")
    print("  MK + MMK (H&R98) + PW-MK (Yue&Wang 2004) + TFPW-MK + Sen's Slope")
    print("  Field Significance: Walker (1914) + Livezey-Chen (1983) MC")
    print("  Output: 14 Figures (8 v3 + 6 new) + 9-sheet Excel + Research MD")
    print(SEP)

    work_dir, no_resume, no_pdf = _parse_args()

    # Temporarily override SAVE_PDF based on CLI flag
    import rta.config as _cfg
    if no_pdf:
        _cfg.SAVE_PDF = False

    out_dir  = Path(work_dir)
    cp_dir   = out_dir / "checkpoints"
    cp_dir.mkdir(exist_ok=True)

    csv_path = find_csv(work_dir)
    base     = Path(csv_path).stem
    prefix_v3 = f"Output_TrendV2_{base}"   # backward-compatible prefix
    prefix_v4 = f"Output_TrendV4_{base}"   # new outputs

    print(f"\n  Input  : {csv_path}")
    print(f"  Output : {work_dir}")
    print(f"  Checkpoints: {cp_dir}")

    # ── Detect existing checkpoints ──────────────────────────────────────────
    ckpts = list_checkpoints(cp_dir)
    resume_from = 0
    if ckpts and not no_resume:
        step_map = {
            "01_qc": 1, "02_aggregation": 2, "03_acf": 3,
            "04_trends": 4, "05_comparison": 5, "06_field_sig": 6,
        }
        for name, step in sorted(step_map.items(), key=lambda x: -x[1]):
            if name in ckpts:
                print(f"\n  ⚡ Checkpoint found: step {step} ({name})")
                ans = input(f"     Resume from step {step+1}? [Y/n]: ").strip().lower()
                if ans in ("", "y", "yes"):
                    resume_from = step
                break
        if resume_from > 0:
            print(f"  → Resuming from step {resume_from + 1}\n")
        else:
            print("  → Starting fresh\n")

    # ════════════════════════════════════════════════════════════════════════
    # Step 1: Load + QC
    # ════════════════════════════════════════════════════════════════════════
    if resume_from >= 1:
        print("  Step 1: Loading QC checkpoint ...")
        ck1 = load_checkpoint("01_qc", cp_dir)
        df, qc_dict, stns_str, smap, period = (
            ck1["df"], ck1["qc_dict"], ck1["stns_str"],
            ck1["smap"], ck1["period"])
    else:
        print("  Step 1: Loading data and Quality Control ...")
        df_raw      = load_daily(csv_path)
        df, qc_dict = quality_control(df_raw.copy())
        stns_str    = [str(s) for s in df.columns.tolist()]
        smap        = short_labels(stns_str)
        period      = f"{df.index[0].year}–{df.index[-1].year}"
        save_checkpoint("01_qc",
                        {"df": df, "qc_dict": qc_dict,
                         "stns_str": stns_str, "smap": smap, "period": period},
                        cp_dir)

    print(f"  Stations: {len(stns_str)} | Period: {period} | Records: {len(df):,}")
    for s, q in qc_dict.items():
        print(f"    {smap.get(s,s):5s} [{s}]  "
              f"missing={q['n_missing']}d ({q['pct_miss']}%)  "
              f"outliers={q['n_outlier']}  filled={q['n_filled']}d")

    # ════════════════════════════════════════════════════════════════════════
    # Step 2: Temporal Aggregation + Dry-Season Validation
    # ════════════════════════════════════════════════════════════════════════
    if resume_from >= 2:
        print("\n  Step 2: Loading aggregation checkpoint ...")
        ck2 = load_checkpoint("02_aggregation", cp_dir)
        scales = ck2["scales"]
        desc_df = ck2["desc_df"]
        dry_validation = ck2["dry_validation"]
    else:
        print("\n  Step 2: Temporal aggregation + dry-season validation ...")
        scales = aggregate_all(df)
        for sk in ["annual", "wet", "dry"]:
            df_s = scales[sk]
            print(f"    {SCALE_META[sk]['label']:22s}: "
                  f"{len(df_s)} years × {df_s.shape[1]} stations")

        # Dry-season hydrological year validation
        val_path = out_dir / f"{prefix_v4}_DrySeasonValidation.txt"
        dry_validation = validate_dry_season(scales, out_path=val_path)
        if dry_validation["valid"]:
            print(f"    ✓ Dry-season validation passed "
                  f"({dry_validation['n_blocks']} blocks, "
                  f"{dry_validation['years'][0]}–{dry_validation['years'][-1]})")
        else:
            print(f"    ✗ Dry-season validation ERRORS: {dry_validation['errors']}")

        print("\n  Step 2b: Descriptive statistics ...")
        desc_df = descriptive_stats(scales, df)
        print(desc_df[["Mean (mm)", "CV (%)", "Wet-days/yr", "Skewness"]].to_string())
        save_checkpoint("02_aggregation",
                        {"scales": scales, "desc_df": desc_df,
                         "dry_validation": dry_validation},
                        cp_dir)

    # ════════════════════════════════════════════════════════════════════════
    # Step 3: Autocorrelation
    # ════════════════════════════════════════════════════════════════════════
    if resume_from >= 3:
        print("\n  Step 3: Loading ACF checkpoint ...")
        ck3 = load_checkpoint("03_acf", cp_dir)
        any_sig_ac = ck3["any_sig_ac"]
    else:
        print("\n  Step 3: Lag-1 Autocorrelation (annual scale) ...")
        any_sig_ac = False
        print(f"  {'Code':6s} [{' Station ':12s}]  {'r₁':>8s}  {'Sig.':>6s}")
        for stn in stns_str:
            arr = (scales["annual"][stn].dropna().values.astype(float)
                   if stn in scales["annual"].columns else np.array([]))
            r1  = lag_k_autocorr(arr)
            sig = is_sig_autocorr(r1, len(arr))
            if sig:
                any_sig_ac = True
            print(f"  {smap[stn]:6s} [{stn:12s}]  "
                  f"{r1:8.4f}  {'Yes ***' if sig else 'No':>6s}")
        print(f"\n  → {'Significant AC detected → Modified MK essential' if any_sig_ac else 'No significant AC'}")
        save_checkpoint("03_acf", {"any_sig_ac": any_sig_ac}, cp_dir)

    # ════════════════════════════════════════════════════════════════════════
    # Step 4: Run all 4 methods (MK + MMK + PW-MK + TFPW-MK)
    # ════════════════════════════════════════════════════════════════════════
    if resume_from >= 4:
        print("\n  Step 4: Loading trend results checkpoint ...")
        ck4 = load_checkpoint("04_trends", cp_dir)
        trend_df = ck4["trend_df"]
    else:
        print("\n  Step 4: Running all 4 trend tests × stations × scales ...")
        trend_df = run_all(scales, stns_str, smap)

        # Print summary
        print(f"\n  {'Code':6s} {'Scale':10s} {'Method':12s} "
              f"{'Z':>7s} {'p':>7s} {'β mm/yr':>8s}  Trend")
        print("  " + "-" * 62)
        for sk in ["annual", "wet", "dry"]:
            for meth in ["Standard MK", "Modified MK", "PW-MK", "TFPW-MK"]:
                sub = trend_df[(trend_df["Scale"] == sk) &
                               (trend_df["Method"] == meth)]
                for _, row in sub.iterrows():
                    sig_s = ("**" if row["sig_01"] else
                             ("*" if row["sig_05"] else "ns"))
                    beta  = (f"{row['Slope_Q']:+.2f}"
                             if not np.isnan(row["Slope_Q"]) else "—")
                    print(f"  {row['Code']:6s} {sk:10s} {meth[:12]:12s} "
                          f"{row['Z']:7.3f} {row['p_value']:7.4f} "
                          f"{beta:>8s}  {row['Trend']} {sig_s}")
            print()

        for meth in ["Standard MK", "Modified MK", "PW-MK", "TFPW-MK"]:
            n_s = int(trend_df[trend_df["Method"] == meth]["sig_05"].sum())
            n_t = int((trend_df["Method"] == meth).sum())
            print(f"  Sig. (p<0.05) {meth}: {n_s}/{n_t}")

        save_checkpoint("04_trends", {"trend_df": trend_df}, cp_dir)

    n_sig_mk  = int(trend_df[trend_df["Method"] == "Standard MK"]["sig_05"].sum())
    n_sig_mmk = int(trend_df[trend_df["Method"] == "Modified MK"]["sig_05"].sum())
    n_total   = int((trend_df["Method"] == "Standard MK").sum())

    # ════════════════════════════════════════════════════════════════════════
    # Step 5: Build comparison tables
    # ════════════════════════════════════════════════════════════════════════
    if resume_from >= 5:
        print("\n  Step 5: Loading comparison checkpoint ...")
        ck5 = load_checkpoint("05_comparison", cp_dir)
        comp_df  = ck5["comp_df"]
        comp4_df = ck5["comp4_df"]
    else:
        print("\n  Step 5: Building comparison tables ...")
        comp_df  = build_comparison(trend_df)
        comp4_df = build_4method_comparison(trend_df)
        n_agree  = int(comp_df["Agree"].sum())
        print(f"  MK vs MMK agreement: {n_agree}/{len(comp_df)} "
              f"({100*n_agree/len(comp_df):.1f}%)")
        changed = comp_df[~comp_df["Agree"]]
        if len(changed) > 0:
            print(f"  ⚠  {len(changed)} cases where AC correction changed trend:")
            for _, r in changed.iterrows():
                code = smap.get(r["Station"], r["Station"])
                print(f"     {code} ({r['Scale']}): "
                      f"MK={r['MK_Trend']}  MMK={r['MMK_Trend']}")

        # 4-method agreement summary
        n_full_agree = int(comp4_df["all_agree"].sum()) if len(comp4_df) > 0 else 0
        print(f"  4-method full agreement: {n_full_agree}/{len(comp4_df)}")
        save_checkpoint("05_comparison",
                        {"comp_df": comp_df, "comp4_df": comp4_df}, cp_dir)

    # ════════════════════════════════════════════════════════════════════════
    # Step 6: Field Significance
    # ════════════════════════════════════════════════════════════════════════
    if resume_from >= 6:
        print("\n  Step 6: Loading field significance checkpoint ...")
        ck6 = load_checkpoint("06_field_sig", cp_dir)
        field_sig_df = ck6["field_sig_df"]
    else:
        print("\n  Step 6: Field significance (Walker + Livezey-Chen MC) ...")
        print("  (Monte Carlo permutation test — this may take a moment)")
        field_sig_df = field_sig_summary(scales, stns_str,
                                         alpha=ALPHA_005, n_perm=1000)
        print(field_sig_df[["Scale", "N_sig_MK", "N_sig_MMK",
                             "Walker_sig_MK", "LC_sig_MK"]].to_string(index=False))
        save_checkpoint("06_field_sig", {"field_sig_df": field_sig_df}, cp_dir)

    # ════════════════════════════════════════════════════════════════════════
    # Step 7: Station coordinates (optional)
    # ════════════════════════════════════════════════════════════════════════
    coords = load_coords(work_dir)
    if coords:
        print(f"\n  ✓ Station coordinates found for {len(coords)} stations")
    else:
        print("\n  ℹ  No station coordinates file found — "
              "Fig 14 will use index-based axes")

    # ════════════════════════════════════════════════════════════════════════
    # Step 8: Figures (v3-compatible, prefix Output_TrendV2_)
    # ════════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*76}")
    print("  Step 8: Generating publication figures (v3 compatible, 600 DPI) ...")

    print("\n  Figure 1: Annual Time Series ...")
    fig1_annual_ts(scales, trend_df, stns_str, smap, period,
                   out_dir, prefix_v3)

    print("\n  Figure 2: Wet & Dry Season Time Series ...")
    fig2_wetdry_ts(scales, trend_df, stns_str, smap, period,
                   out_dir, prefix_v3)

    print("\n  Figure 3: Sen's Slope All Scales ...")
    fig3_sens_all(trend_df, stns_str, smap, period, out_dir, prefix_v3)

    print("\n  Figure 4: MK vs MMK Comparison ...")
    fig4_mk_vs_mmk(comp_df, stns_str, smap, period, out_dir, prefix_v3)

    print("\n  Figure 5: Significance Heatmap ...")
    fig5_significance_heatmap(trend_df, stns_str, smap, period,
                              out_dir, prefix_v3)

    print("\n  Figure 6: Autocorrelation ...")
    fig6_autocorrelation(scales, stns_str, smap, period, out_dir, prefix_v3)

    print("\n  Figure 7: Monthly Climatology ...")
    fig7_monthly_climatology(scales, stns_str, smap, period,
                             out_dir, prefix_v3)

    print("\n  Figure 8: Spatial Trend Summary ...")
    fig8_spatial_summary(trend_df, comp_df, stns_str, smap, period,
                         out_dir, prefix_v3)

    # ════════════════════════════════════════════════════════════════════════
    # Step 9: New v4 Figures (prefix Output_TrendV4_)
    # ════════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*76}")
    print("  Step 9: Generating new v4 publication figures ...")

    print("\n  Figure 9: Taylor Diagram ...")
    fig9_taylor_diagram(scales, stns_str, smap, period, out_dir, prefix_v4)

    print("\n  Figure 10: Z-Comparison Matrix (4 methods) ...")
    fig10_z_comparison_matrix(trend_df, stns_str, smap, period,
                              out_dir, prefix_v4)

    print("\n  Figure 11: Method Comparison Scatter ...")
    fig11_method_comparison_scatter(trend_df, stns_str, smap, period,
                                    out_dir, prefix_v4)

    print("\n  Figure 12: ACF Diagnostics ...")
    fig12_acf_diagnostics(scales, stns_str, smap, period, out_dir, prefix_v4)

    print("\n  Figure 13: Field Significance ...")
    fig13_field_significance(field_sig_df, period, out_dir, prefix_v4)

    print("\n  Figure 14: Spatial Trend Maps (geographic, MMK) ...")
    fig14_spatial_maps(trend_df, stns_str, smap, coords, period,
                       out_dir, prefix_v4)

    if coords:
        print("\n  Figure 14b: Station Distribution Map ...")
        fig_station_distribution(coords, stns_str, smap, period,
                                 out_dir, prefix_v4)

        print("\n  Figure 14c: All-Methods Spatial Maps ...")
        fig_spatial_methods(trend_df, stns_str, smap, coords, period,
                            out_dir, prefix_v4)

        print("\n  Figure 14d: Field Significance Spatial Map ...")
        fig_spatial_field_sig(trend_df, field_sig_df, stns_str, smap,
                              coords, period, out_dir, prefix_v4)

        print("\n  Figure 14e: Comprehensive Spatial Overview ...")
        fig_spatial_full(trend_df, stns_str, smap, coords, field_sig_df,
                         period, out_dir, prefix_v4)

    # ════════════════════════════════════════════════════════════════════════
    # Step 10: Excel (9 sheets)
    # ════════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*76}")
    out_xlsx_v4 = out_dir / f"{prefix_v4}_Results.xlsx"
    print(f"  Step 10: Building 9-sheet Excel → {out_xlsx_v4.name} ...")
    write_excel(out_xlsx_v4, stns_str, smap, trend_df, comp_df,
                desc_df, qc_dict, period,
                comp4_df=comp4_df,
                field_sig_df=field_sig_df,
                dry_validation=dry_validation)

    # ════════════════════════════════════════════════════════════════════════
    # Step 11: Research Summary Markdown
    # ════════════════════════════════════════════════════════════════════════
    print(f"\n  Step 11: Writing Research Summary ...")
    out_md_v4 = out_dir / f"{prefix_v4}_Research_Summary.md"
    write_summary_md(out_md_v4, stns_str, smap, trend_df, comp_df,
                     desc_df, period, n_sig_mk, n_sig_mmk, n_total,
                     any_sig_ac, scales=scales,
                     comp4_df=comp4_df, field_sig_df=field_sig_df)

    # ════════════════════════════════════════════════════════════════════════
    # Final Summary
    # ════════════════════════════════════════════════════════════════════════
    n_fig_v3 = len(list(out_dir.glob(f"{prefix_v3}_Fig*.png")))
    n_fig_v4 = len(list(out_dir.glob(f"{prefix_v4}_Fig*.png")))
    n_agree_final = int(comp_df["Agree"].sum())
    pct_agree     = 100 * n_agree_final / len(comp_df) if len(comp_df) > 0 else 0.0

    print()
    print(SEP)
    print(f"  ✓  DONE — Rainfall Trend Analysis v{VERSION}")
    print(f"  {'─'*68}")
    print(f"  Period          : {period}")
    print(f"  Stations        : {len(stns_str)}  ({', '.join(smap.values())})")
    print(f"  Temporal scales : Annual / Wet (May–Oct) / Dry (Nov–Apr)")
    print(f"  Methods         : Standard MK + MMK (H&R98) + PW-MK + TFPW-MK")
    print(f"  Sig. (p<0.05)   : MK={n_sig_mk}  MMK={n_sig_mmk}  (of {n_total} tests)")
    print(f"  MK vs MMK agree : {n_agree_final}/{len(comp_df)} ({pct_agree:.1f}%)")
    fs_row = field_sig_df[field_sig_df["Scale"] == "annual"]
    if len(fs_row) > 0:
        r = fs_row.iloc[0]
        print(f"  Field sig (ann) : Walker={'Yes' if r['Walker_sig_MK'] else 'No'}  "
              f"LC={'Yes' if r['LC_sig_MK'] else 'No'}")
    print(f"  Figures (v3)    : {n_fig_v3} PNG  {prefix_v3}_Fig*.png")
    print(f"  Figures (v4)    : {n_fig_v4} PNG  {prefix_v4}_Fig*.png")
    print(f"  Excel (9 sheets): {out_xlsx_v4.name}")
    print(f"  Summary (MD)    : {out_md_v4.name}")
    print(f"  Saved in        : {work_dir}")
    print(SEP)


if __name__ == "__main__":
    main()
