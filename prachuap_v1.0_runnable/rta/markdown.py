"""
rta.markdown — Markdown research summary for rainfall trend analysis.

Extracted and extended from rainfall_trend_analysis_v3.py §17 (lines 1777–2091).
Original sections 1–6 are preserved exactly.
New optional sections 3.8 (4-Method Comparison) and 3.9 (Field Significance)
are appended when the corresponding DataFrames are supplied.
The global `scales_global` dependency is replaced by a `scales` parameter.
"""

import math
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

from .config import VERSION, WET_THR, SCALE_META
from .autocorr import lag_k_autocorr, is_sig_autocorr


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  write_summary_md                                                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def write_summary_md(out_md: Path,
                     stns, smap, trend_df, comp_df, desc_df,
                     period, n_sig_mk, n_sig_mmk, n_total, any_sig_ac,
                     scales=None,
                     comp4_df=None,
                     field_sig_df=None):
    """
    Write a comprehensive Markdown research summary ready for paper writing.

    Includes: Study area, methods, key results, tables, statistical summary.

    Parameters
    ----------
    out_md       : Path — output .md file path
    stns         : list of station IDs
    smap         : dict {station_id → short_code}
    trend_df     : DataFrame (Standard MK + Modified MK rows)
    comp_df      : DataFrame (MK vs MMK comparison)
    desc_df      : DataFrame (descriptive stats, indexed by station)
    period       : str  e.g. "1981–2020"
    n_sig_mk     : int  number of significant trends (Standard MK, p<0.05)
    n_sig_mmk    : int  number of significant trends (Modified MK, p<0.05)
    n_total      : int  total station × scale combinations tested
    any_sig_ac   : bool True if any station shows significant autocorrelation
    scales       : dict {scale_key → DataFrame/array}  — replaces scales_global
    comp4_df     : DataFrame or None  — 4-method comparison (section 3.8)
    field_sig_df : DataFrame or None  — field significance (section 3.9)
    """
    stns  = [str(s) for s in stns]
    codes = [smap.get(s, s) for s in stns]
    n_s   = len(stns)
    now   = datetime.now().strftime("%Y-%m-%d")

    def fmt_row(stn, sk, method):
        sub = trend_df[(trend_df["Station"] == stn) &
                       (trend_df["Scale"]   == sk) &
                       (trend_df["Method"]  == method)]
        if len(sub) == 0:
            return "—", "—", "—", "—"
        r   = sub.iloc[0]
        sig = "**" if r["sig_01"] else ("*" if r["sig_05"] else "ns")
        sl  = f"{r['Slope_Q']:+.2f}" if not np.isnan(r["Slope_Q"]) else "—"
        Z   = f"{r['Z']:.3f}"
        p   = f"{r['p_value']:.4f}"
        return Z, p, sig, sl

    lines = []

    # ── §1 Header & study area ─────────────────────────────────────────────
    lines += [
        "# Rainfall Trend Analysis — Research Summary",
        "",
        f"> **Generated**: {now}  |  "
        f"**Study Period**: {period}  |  "
        f"**Script**: Rainfall Trend Analysis v{VERSION}",
        "",
        "---",
        "",
        "## 1. Study Area and Data",
        "",
        "- **Study area**: Phetchaburi–Prachuap Khiri Khan River Basin, "
        "Western Thailand",
        f"- **Data**: Daily observed rainfall from {n_s} meteorological "
        "stations",
        f"- **Period**: {period}",
        f"- **Stations**: "
        f"{', '.join([f'{c} ({s})' for c, s in zip(codes, stns)])}",
        f"- **Wet-day threshold**: ≥{WET_THR} mm day⁻¹ (WMO standard)",
        "",
        "## 2. Methods",
        "",
        "### 2.1 Temporal Scales (Hydrological Year)",
        "",
        "| Scale | Period | Description |",
        "|-------|--------|-------------|",
        "| Annual | Jan–Dec | Calendar year total |",
        "| Wet Season | May–Oct | Monsoon / wet season (6 months) |",
        "| Dry Season | Nov–Apr | Dry season — hydrological year approach "
        "(6 months) |",
        "",
        "### 2.2 Statistical Methods",
        "",
        "**Standard Mann–Kendall Test** (Mann 1945; Kendall 1975):",
        "- Non-parametric trend test for monotonic trends in time series.",
        "- S statistic with tie correction; Z-statistic from standard normal.",
        "- *Limitation*: Does not account for serial autocorrelation.",
        "",
        "**Modified Mann–Kendall Test** (Hamed & Rao 1998):",
        "- Corrects Var(S) using autocorrelation of the ranked series.",
        "- Effective sample size: "
        "$n^* = n / [1 + (2/n) \\sum_{k=1}^{n-1}(n-k)\\rho_k]$",
        "- Adjusted variance: "
        "$\\text{Var}^*(S) = \\text{Var}(S) \\times (n/n^*)$",
        f"- **Autocorrelation detected**: "
        f"{'Yes → Modified MK essential' if any_sig_ac else 'No → both methods appropriate'}",
        "",
        "**Pre-Whitening Mann–Kendall Test** (Yue & Wang 2004):",
        "- Removes lag-1 autocorrelation by pre-whitening the series "
        "before applying the MK test.",
        "- $x'_t = x_t - \\hat{\\rho}_1 x_{t-1}$ (AR(1) pre-whitening).",
        "- Can underestimate trends when trend and autocorrelation coexist.",
        "",
        "**Trend-Free Pre-Whitening Mann–Kendall Test** (TFPW-MK; "
        "Yue et al. 2002):",
        "- Removes the Sen's slope trend component before pre-whitening, "
        "then restores it.",
        "- Reduces bias of the PW-MK method when trends are present.",
        "",
        "**Sen's Slope Estimator** (Sen 1968):",
        "- $Q = \\text{median}\\left[\\frac{x_j - x_i}{j - i}\\right]$ "
        "for all $j > i$",
        "- 95% CI: rank-based method (Gilbert 1987)",
        "- Interpretation: magnitude of change in mm per year",
        "",
        "**Significance levels**: α = 0.05 (|Z| > 1.96) and "
        "α = 0.01 (|Z| > 2.58)",
        "",
        "## 3. Results",
        "",
        "### 3.1 Descriptive Statistics",
        "",
        "| Station | Code | Mean (mm) | Std (mm) | CV (%) | Wet-days/yr |",
        "|---------|------|-----------|----------|--------|-------------|",
    ]

    for stn in stns:
        if stn not in desc_df.index:
            continue
        d = desc_df.loc[stn]
        lines.append(
            f"| {stn} | {smap.get(stn, stn)} | "
            f"{d['Mean (mm)']:.1f} | {d['Std (mm)']:.1f} | "
            f"{d['CV (%)']:.1f} | {d['Wet-days/yr']:.1f} |")

    lines += [
        "",
        f"*Regional mean annual rainfall: "
        f"{desc_df['Mean (mm)'].mean():.1f} mm/yr "
        f"(range: {desc_df['Mean (mm)'].min():.1f}–"
        f"{desc_df['Mean (mm)'].max():.1f} mm/yr)*",
        "",
        "### 3.2 Autocorrelation Results",
        "",
        "| Station | Code | r₁ (Annual) | Significant? | → Modified MK? |",
        "|---------|------|-------------|--------------|----------------|",
    ]

    for stn in stns:
        # Use the `scales` parameter instead of the removed scales_global
        arr = (scales or {}).get("annual", {})
        if (hasattr(arr, "__contains__") and
                hasattr(arr, "columns") and
                stn in arr.columns):
            a = arr[stn].dropna().values.astype(float)
        else:
            a = np.array([])
        r1  = lag_k_autocorr(a) if len(a) > 4 else np.nan
        sig = is_sig_autocorr(r1, len(a)) if not np.isnan(r1) else False
        r1_str = f"{r1:.4f}" if not np.isnan(r1) else "—"
        lines.append(
            f"| {stn} | {smap.get(stn, stn)} | "
            f"{r1_str} | "
            f"{'Yes ***' if sig else 'No'} | "
            f"{'Recommended' if sig else 'Optional'} |")

    # ── §3.3 Annual ─────────────────────────────────────────────────────────
    lines += [
        "",
        "### 3.3 Trend Analysis — Annual Scale",
        "",
        "| Station | Code | MK Z | MK p | MMK Z | MMK p | β (mm/yr) | "
        "Trend | Sig. |",
        "|---------|------|------|------|-------|-------|-----------|"
        "-------|------|",
    ]
    for stn in stns:
        mk_Z,  mk_p, mk_sig, _  = fmt_row(stn, "annual", "Standard MK")
        mmk_Z, mmk_p, mmk_sig, sl = fmt_row(stn, "annual", "Modified MK")
        code = smap.get(stn, stn)
        sub  = trend_df[(trend_df["Station"] == stn) &
                        (trend_df["Scale"]   == "annual") &
                        (trend_df["Method"]  == "Modified MK")]
        tr   = str(sub["Trend"].values[0]) if len(sub) else "—"
        lines.append(
            f"| {stn} | {code} | {mk_Z} | {mk_p} | "
            f"{mmk_Z} | {mmk_p} | {sl} | {tr} | {mmk_sig} |")

    # ── §3.4 Wet season ─────────────────────────────────────────────────────
    lines += [
        "",
        "### 3.4 Trend Analysis — Wet Season (May–Oct)",
        "",
        "| Station | Code | MK Z | MMK Z | MMK p | β (mm/yr) | Trend | Sig. |",
        "|---------|------|------|-------|-------|-----------|-------|------|",
    ]
    for stn in stns:
        mk_Z,  _, _, _            = fmt_row(stn, "wet", "Standard MK")
        mmk_Z, mmk_p, mmk_sig, sl = fmt_row(stn, "wet", "Modified MK")
        code = smap.get(stn, stn)
        sub  = trend_df[(trend_df["Station"] == stn) &
                        (trend_df["Scale"]   == "wet") &
                        (trend_df["Method"]  == "Modified MK")]
        tr   = str(sub["Trend"].values[0]) if len(sub) else "—"
        lines.append(
            f"| {stn} | {code} | {mk_Z} | {mmk_Z} | {mmk_p} | "
            f"{sl} | {tr} | {mmk_sig} |")

    # ── §3.5 Dry season ─────────────────────────────────────────────────────
    lines += [
        "",
        "### 3.5 Trend Analysis — Dry Season (Nov–Apr)",
        "",
        "| Station | Code | MK Z | MMK Z | MMK p | β (mm/yr) | Trend | Sig. |",
        "|---------|------|------|-------|-------|-----------|-------|------|",
    ]
    for stn in stns:
        mk_Z,  _, _, _            = fmt_row(stn, "dry", "Standard MK")
        mmk_Z, mmk_p, mmk_sig, sl = fmt_row(stn, "dry", "Modified MK")
        code = smap.get(stn, stn)
        sub  = trend_df[(trend_df["Station"] == stn) &
                        (trend_df["Scale"]   == "dry") &
                        (trend_df["Method"]  == "Modified MK")]
        tr   = str(sub["Trend"].values[0]) if len(sub) else "—"
        lines.append(
            f"| {stn} | {code} | {mk_Z} | {mmk_Z} | {mmk_p} | "
            f"{sl} | {tr} | {mmk_sig} |")

    # ── §3.6 Agreement summary ───────────────────────────────────────────────
    n_agree       = int(comp_df["Agree"].sum())
    n_total_comp  = len(comp_df)
    n_changed     = n_total_comp - n_agree
    lines += [
        "",
        "### 3.6 MK vs Modified MK Comparison",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total comparisons (station × scale) | {n_total_comp} |",
        f"| Agreement (same trend conclusion) | "
        f"{n_agree} ({100 * n_agree / n_total_comp:.1f}%) |",
        f"| Changed by autocorrelation correction | "
        f"{n_changed} ({100 * n_changed / n_total_comp:.1f}%) |",
        f"| Stations with significant autocorr. (annual) | "
        f"{sum(1 for _, r in comp_df[comp_df['Scale'] == 'annual'].iterrows() if r['Sig_AC'])} "
        f"/ {n_s} |",
        f"| Sig. trends (Standard MK, p<0.05) | {n_sig_mk} / {n_total} |",
        f"| Sig. trends (Modified MK, p<0.05) | {n_sig_mmk} / {n_total} |",
        "",
        "### 3.7 Key Findings",
        "",
    ]

    # Auto-generate key findings from data
    inc_ann = trend_df[(trend_df["Scale"]  == "annual") &
                       (trend_df["Method"] == "Modified MK") &
                       (trend_df["sig_05"] == True) &
                       (trend_df["Z"] > 0)]
    dec_ann = trend_df[(trend_df["Scale"]  == "annual") &
                       (trend_df["Method"] == "Modified MK") &
                       (trend_df["sig_05"] == True) &
                       (trend_df["Z"] < 0)]
    inc_wet = trend_df[(trend_df["Scale"]  == "wet") &
                       (trend_df["Method"] == "Modified MK") &
                       (trend_df["sig_05"] == True) &
                       (trend_df["Z"] > 0)]
    dec_dry = trend_df[(trend_df["Scale"]  == "dry") &
                       (trend_df["Method"] == "Modified MK") &
                       (trend_df["sig_05"] == True) &
                       (trend_df["Z"] < 0)]

    if len(inc_ann) > 0:
        sl_mean   = float(inc_ann["Slope_Q"].mean())
        stns_inc  = [smap.get(str(s), str(s)) for s in inc_ann["Station"]]
        lines.append(
            f"- **Annual increasing trend**: {', '.join(stns_inc)} show "
            f"significant increasing trends "
            f"(mean β = {sl_mean:+.2f} mm/yr, p<0.05).")
    if len(dec_ann) > 0:
        sl_mean   = float(dec_ann["Slope_Q"].mean())
        stns_dec  = [smap.get(str(s), str(s)) for s in dec_ann["Station"]]
        lines.append(
            f"- **Annual decreasing trend**: {', '.join(stns_dec)} show "
            f"significant decreasing trends "
            f"(mean β = {sl_mean:+.2f} mm/yr, p<0.05).")
    if len(inc_ann) == 0 and len(dec_ann) == 0:
        lines.append(
            "- **Annual**: No statistically significant trends detected "
            "at p<0.05 level in annual rainfall.")
    if len(inc_wet) > 0:
        stns_iw = [smap.get(str(s), str(s)) for s in inc_wet["Station"]]
        lines.append(
            f"- **Wet season**: {', '.join(stns_iw)} show increasing trends.")
    else:
        lines.append("- **Wet season**: No significant trends detected.")
    if len(dec_dry) > 0:
        stns_dd = [smap.get(str(s), str(s)) for s in dec_dry["Station"]]
        lines.append(
            f"- **Dry season**: {', '.join(stns_dd)} show decreasing trends.")
    else:
        lines.append("- **Dry season**: No significant trends detected.")
    if any_sig_ac:
        lines.append(
            "- **Autocorrelation effect**: Serial autocorrelation was "
            "significant in several stations. Modified MK corrects for this "
            f"bias; {n_changed} trend conclusions changed after applying "
            "the correction.")
    else:
        lines.append(
            "- **Autocorrelation**: No significant autocorrelation detected; "
            "Standard MK and Modified MK results are highly consistent.")

    # ── §3.8 4-Method Comparison (optional) ──────────────────────────────────
    if comp4_df is not None:
        lines += [
            "",
            "### 3.8 4-Method Comparison",
            "",
            "Summary of agreement across all four methods "
            "(MK, MMK, PW-MK, TFPW-MK) per temporal scale:",
            "",
            "| Scale | N rows | All-agree | Partial | None-agree |",
            "|-------|--------|-----------|---------|------------|",
        ]
        for sk in ["annual", "wet", "dry"]:
            sk_df = comp4_df[comp4_df.get("Scale", comp4_df.columns[2]) == sk] \
                if "Scale" in comp4_df.columns else comp4_df
            if "Scale" in comp4_df.columns:
                sk_df = comp4_df[comp4_df["Scale"] == sk]
            else:
                sk_df = pd.DataFrame()
            n_rows      = len(sk_df)
            if n_rows == 0:
                continue
            n_all_agree = int(sk_df["all_agree"].sum()) \
                if "all_agree" in sk_df.columns else 0
            n_sig_any   = int((sk_df.get("n_sig_methods", 0) > 0).sum()) \
                if "n_sig_methods" in sk_df.columns else 0
            n_none      = n_rows - n_all_agree - (n_sig_any - n_all_agree)
            n_partial   = n_sig_any - n_all_agree
            sk_label    = SCALE_META.get(sk, {}).get("label", sk)
            lines.append(
                f"| {sk_label} | {n_rows} | {n_all_agree} | "
                f"{n_partial} | {max(n_none, 0)} |")

        lines += [
            "",
            "**Interpretation**: rows where `all_agree = Yes` indicate "
            "robust trend conclusions unaffected by autocorrelation "
            "correction method. Disagreement warrants deeper inspection.",
        ]

    # ── §3.9 Field Significance (optional) ───────────────────────────────────
    if field_sig_df is not None:
        lines += [
            "",
            "### 3.9 Field Significance",
            "",
            "Tests whether the number of locally-significant stations "
            "exceeds the rate expected by chance alone (Walker 1914; "
            "Livezey & Chen 1983):",
            "",
            "| Scale | N_stations | N_sig_MK | Frac_sig_MK | "
            "Walker_sig | LC_sig |",
            "|-------|------------|----------|-------------|"
            "-----------|--------|",
        ]
        for _, row in field_sig_df.iterrows():
            sk        = str(row.get("Scale", "—"))
            sk_label  = SCALE_META.get(sk, {}).get("label", sk)
            n_st      = row.get("N_stations", "—")
            n_sig     = row.get("N_sig_MK", "—")
            frac      = row.get("Frac_sig_MK", np.nan)
            frac_str  = f"{frac:.3f}" if not (isinstance(frac, float) and
                                               np.isnan(frac)) else "—"
            w_sig     = "Yes*" if bool(row.get("Walker_sig_MK", False)) else "No"
            lc_sig    = "Yes*" if bool(row.get("LC_sig_MK", False)) else "No"
            lines.append(
                f"| {sk_label} | {n_st} | {n_sig} | {frac_str} | "
                f"{w_sig} | {lc_sig} |")

        lines += [
            "",
            "**Note**: Field significance corrects for the multiplicity of "
            "simultaneous hypothesis tests. A result is field-significant "
            "when the fraction of locally-significant stations exceeds the "
            "5 % level under the Walker / Livezey–Chen criterion.",
        ]

    # ── §4 Discussion ────────────────────────────────────────────────────────
    lines += [
        "",
        "## 4. Discussion Points",
        "",
        "- The Modified Mann–Kendall test (Hamed & Rao 1998) is the "
        "recommended approach when serial autocorrelation is present in "
        "hydro-climatic time series data.",
        "- Positive serial autocorrelation inflates the Standard MK "
        "Z-statistic, leading to false positive trend detection "
        "(Type I error inflation).",
        "- Sen's slope provides a physically meaningful estimate of the "
        "rate of change, which is essential for water resource planning.",
        "- Wet/dry season separation is hydrologically important: "
        "changes in wet season rainfall affect flood risk, "
        "while dry season trends affect irrigation demand and reservoir "
        "management.",
        "- The 95% CI of Sen's slope should be reported alongside trend "
        "significance to convey the uncertainty in the magnitude of change.",
        "",
        "## 5. Suggested Paper Language",
        "",
        "### Methods Section (Draft)",
        "",
        "Long-term trends in daily, annual, and seasonal rainfall were "
        "analysed using the Modified Mann–Kendall (MMK) trend test proposed "
        "by Hamed and Rao (1998), which accounts for the effect of positive "
        "serial autocorrelation commonly found in hydro-climatic time series. "
        "The standard Mann–Kendall test (Mann 1945; Kendall 1975) was also "
        "applied for comparison. To further assess the influence of "
        "autocorrelation on trend detection, two additional methods were "
        "employed: the Pre-Whitening Mann–Kendall test (PW-MK; Yue & Wang "
        "2004) and the Trend-Free Pre-Whitening Mann–Kendall test "
        "(TFPW-MK; Yue et al. 2002). The magnitude of detected trends was "
        "quantified using the non-parametric Sen's slope estimator "
        "(Sen 1968), together with its 95% confidence interval derived from "
        "the rank-based method of Gilbert (1987). All analyses were conducted "
        "separately for the annual "
        f"({period}) and two hydrological seasons: the wet season "
        "(May–October) and the dry season (November–April). Significance was "
        "assessed at the 5% (α = 0.05) and 1% (α = 0.01) levels.",
        "",
        "### Results Section (Template)",
        "",
        "Of the {N} station–scale combinations tested, {n_sig_mmk} showed "
        "statistically significant trends (p < 0.05) according to the "
        "Modified MK test. The serial autocorrelation analysis indicated that "
        "{n_ac} stations exhibited significant Lag-1 autocorrelation at the "
        "annual scale, justifying the use of the Modified MK correction. "
        "Agreement between Standard MK and Modified MK was high "
        "({n_agree}/{n_total_comp} combinations, {pct:.1f}%), indicating "
        "that autocorrelation had a limited but non-negligible effect on "
        "trend conclusions.",
        "",
        "## 6. References",
        "",
        "- Mann, H. B. (1945). Nonparametric tests against trend. "
        "*Econometrica*, 13, 245–259.",
        "- Kendall, M. G. (1975). *Rank Correlation Methods* (4th ed.). "
        "Griffin, London.",
        "- Sen, P. K. (1968). Estimates of regression coefficient based on "
        "Kendall's tau. *Journal of the American Statistical Association*, "
        "63, 1379–1389.",
        "- Hamed, K. H., & Rao, A. R. (1998). A modified Mann–Kendall trend "
        "test for autocorrelated data. *Journal of Hydrology*, 204, 182–196.",
        "- Gilbert, R. O. (1987). *Statistical Methods for Environmental "
        "Pollution Monitoring*. Van Nostrand Reinhold, New York.",
        "- Önöz, B., & Bayazit, M. (2003). The power of statistical tests "
        "for trend detection. *Hydrological Sciences Journal*, 48, 93–98.",
        "- Yue, S., Pilon, P., Phinney, B., & Cavadias, G. (2002). The "
        "influence of autocorrelation on the ability to detect trend in "
        "hydrological series. *Hydrological Processes*, 16, 1807–1829.",
        "- Yue, S., & Wang, C. (2004). The Mann–Kendall test modified by "
        "effective sample size to detect trend in serially correlated "
        "hydrological series. *Water Resources Research*, 40, W08307.",
        "- WMO (2008). *Guide to Hydrological Practices* (WMO-No. 168). "
        "World Meteorological Organization, Geneva.",
        "",
        "---",
        f"*End of Research Summary  |  Generated: {now}  |  "
        f"Script v{VERSION}*",
    ]

    # ── fill in template placeholders ────────────────────────────────────────
    n_ac_sig  = sum(1 for _, r in comp_df[comp_df["Scale"] == "annual"].iterrows()
                    if r["Sig_AC"])
    pct_agree = 100 * n_agree / n_total_comp if n_total_comp > 0 else 0.0
    text = "\n".join(lines)
    text = (text
            .replace("{N}",           str(n_total))
            .replace("{n_sig_mmk}",   str(n_sig_mmk))
            .replace("{n_ac}",        str(n_ac_sig))
            .replace("{n_agree}",     str(n_agree))
            .replace("{n_total_comp}", str(n_total_comp))
            .replace("{pct:.1f}",     f"{pct_agree:.1f}"))

    Path(out_md).write_text(text, encoding="utf-8")
    print(f"  ✓  Summary: {Path(out_md).name}")
