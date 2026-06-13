"""Time series figures: Fig1 (annual) and Fig2 (wet/dry season)."""

import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D
import matplotlib.cm as cm
from scipy.stats import norm as scipy_norm
from ..config import (C, DPI, SAVE_PDF, SCALE_META, WET_MONTHS, DRY_MONTHS,
                      MONTH_ABBR, Z_005, Z_001, ALPHA_005, savefig)
from ..autocorr import lag_k_autocorr, all_lag_autocorr, is_sig_autocorr
from .helpers import _sens_line, _sig_label, _col_trend
from ..trend_tests import modified_mk


def fig1_annual_ts(scales, trend_df, stns, smap, period, out_dir, prefix):
    """Fig 1: Annual rainfall time series per station with MMK trend line."""
    df_ann = scales["annual"]
    stns   = [str(s) for s in stns]
    n_s    = len(stns)
    ncols  = min(4, n_s)
    nrows  = math.ceil(n_s / ncols)

    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(5.5*ncols, 4.0*nrows), squeeze=False)
    fig.subplots_adjust(hspace=0.55, wspace=0.30,
                        top=0.93, bottom=0.07, left=0.06, right=0.97)

    for si, stn in enumerate(stns):
        ax = axes[si//ncols][si%ncols]
        if stn not in df_ann.columns: ax.set_visible(False); continue
        s = df_ann[stn].dropna()
        if len(s) < 4: ax.set_visible(False); continue
        yrs  = s.index.year.values.astype(float)
        vals = s.values.astype(float)

        # retrieve MMK result
        sub = trend_df[(trend_df["Station"]==stn) &
                       (trend_df["Scale"]=="annual") &
                       (trend_df["Method"]=="Modified MK")]
        sig05 = bool(sub["sig_05"].values[0]) if len(sub) else False
        sig01 = bool(sub["sig_01"].values[0]) if len(sub) else False
        Z     = float(sub["Z"].values[0]) if len(sub) else np.nan
        slope = float(sub["Slope_Q"].values[0]) if len(sub) else np.nan
        lo    = float(sub["Slope_lo"].values[0]) if len(sub) else np.nan
        hi    = float(sub["Slope_hi"].values[0]) if len(sub) else np.nan
        p_val = float(sub["p_value"].values[0]) if len(sub) else np.nan
        col   = _col_trend(sig05, Z)
        slab  = _sig_label(sig05, sig01, Z)

        ax.bar(yrs, vals, width=0.75, color=col, alpha=0.45,
               edgecolor="none", zorder=2)
        ax.plot(yrs, vals, color=col, lw=1.5, alpha=0.85, zorder=3)

        tl = _sens_line(vals, slope, yrs)
        if tl is not None:
            ax.plot(yrs, tl, "k-", lw=2.2, zorder=5,
                    label=f"β={slope:+.1f} mm/yr")
            if not (np.isnan(lo) or np.isnan(hi)):
                ll = _sens_line(vals, lo, yrs)
                hl = _sens_line(vals, hi, yrs)
                ax.fill_between(yrs, ll, hl, color="grey",
                                alpha=0.18, zorder=4, label="95% CI")

        code = smap.get(stn, stn)
        ax.set_title(f"({chr(97+si)})  {code}  [{stn}]\n"
                     f"Z={Z:.2f}  p={p_val:.3f}  {slab}",
                     loc="left", fontsize=10.5, fontweight="bold", pad=3)
        ax.set_ylabel("mm yr⁻¹", fontsize=10)
        ax.set_xlabel("Year",    fontsize=10)
        ax.set_ylim(bottom=0)
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        ax.legend(fontsize=8, frameon=True, edgecolor="#B0BEC5",
                  loc="upper right", handlelength=1.8)

    for si in range(len(stns), nrows*ncols):
        axes[si//ncols][si%ncols].set_visible(False)

    hand = [mpatches.Patch(color=C["inc"],    label="Increasing (sig.)"),
            mpatches.Patch(color=C["dec"],    label="Decreasing (sig.)"),
            mpatches.Patch(color=C["ns_col"], label="Not significant"),
            Line2D([0],[0],color="black",lw=2.2,label="Sen's slope"),
            mpatches.Patch(color="grey",alpha=0.35,label="95% CI")]
    fig.legend(handles=hand, loc="lower center", ncol=5, fontsize=15,
               markerscale=1.5, frameon=True, edgecolor="#B0BEC5", bbox_to_anchor=(0.5,-0.02))
    savefig(fig, str(out_dir/f"{prefix}_Fig1_AnnualTimeSeries"))


def fig2_wetdry_ts(scales, trend_df, stns, smap, period, out_dir, prefix):
    """
    Fig 2: Regional-mean time series for Wet and Dry seasons.
    2×2 grid: (a)Wet regional, (b)Dry regional, (c)Wet per station, (d)Dry per station.
    """
    stns = [str(s) for s in stns]
    fig  = plt.figure(figsize=(18, 13))
    gs   = gridspec.GridSpec(2, 2, figure=fig, hspace=0.48, wspace=0.30,
                             top=0.91, bottom=0.08, left=0.07, right=0.97)
    ax1  = fig.add_subplot(gs[0, 0])   # Wet regional
    ax2  = fig.add_subplot(gs[0, 1])   # Dry regional
    ax3  = fig.add_subplot(gs[1, 0])   # Wet per station
    ax4  = fig.add_subplot(gs[1, 1])   # Dry per station

    for ax, sk, col_l, col_lt, panel, season_ttl in [
        (ax1,"wet", C["wet"], C["wet_lt"], "(a)", "Wet Season (May–Oct)"),
        (ax2,"dry", C["dry"], C["dry_lt"], "(b)", "Dry Season (Nov–Apr)"),
    ]:
        df_s  = scales[sk]
        cols  = [s for s in stns if s in df_s.columns]
        reg   = df_s[cols].mean(axis=1).dropna()
        if len(reg) < 4: continue
        yrs   = reg.index.year.values.astype(float)
        vals  = reg.values.astype(float)

        # Regional MMK
        res  = modified_mk(vals)
        Z    = res["Z"]; p   = res["p_value"]
        slope= res["slope_Q"]; lo = res["slope_lo"]; hi = res["slope_hi"]
        sig05= res["sig_05"]; sig01= res["sig_01"]
        slab = _sig_label(sig05, sig01, Z)
        col  = _col_trend(sig05, Z) if sig05 else col_l

        ax.fill_between(yrs, vals, alpha=0.25, color=col_l, zorder=2)
        ax.plot(yrs, vals, color=col_l, lw=2.0, zorder=3, label=season_ttl)
        tl = _sens_line(vals, slope, yrs)
        if tl is not None:
            ax.plot(yrs, tl, "k-", lw=2.2, zorder=5,
                    label=f"β={slope:+.1f} mm/yr")
            if not (np.isnan(lo) or np.isnan(hi)):
                ax.fill_between(yrs,
                                _sens_line(vals, lo, yrs),
                                _sens_line(vals, hi, yrs),
                                color="grey", alpha=0.18, zorder=4, label="95% CI")
        ax.set_title(
            f"{panel}  Regional Mean — {season_ttl}\n"
            f"MMK: Z={Z:.3f}  p={p:.4f}  {slab}",
            loc="left", fontsize=12, fontweight="bold", pad=5)
        ax.set_ylabel(SCALE_META[sk]["unit"], fontsize=11)
        ax.set_xlabel("Year", fontsize=11)
        ax.set_ylim(bottom=0)
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        ax.legend(fontsize=10, frameon=True, edgecolor="#B0BEC5",
                  loc="upper right", handlelength=1.8)

    # Per-station slope bars (panels c, d)
    x = np.arange(len(stns))
    codes = [smap.get(s, s) for s in stns]

    for ax, sk, col_l, col_lt, panel, season_ttl in [
        (ax3,"wet",C["wet"],C["wet_lt"],"(c)","Wet Season — Sen's Slope per Station"),
        (ax4,"dry",C["dry"],C["dry_lt"],"(d)","Dry Season — Sen's Slope per Station"),
    ]:
        slopes_v = []; lo_e = []; hi_e = []; bar_cols = []
        for stn in stns:
            sub = trend_df[(trend_df["Station"]==stn) &
                           (trend_df["Scale"]==sk) &
                           (trend_df["Method"]=="Modified MK")]
            if len(sub) == 0:
                slopes_v.append(np.nan); lo_e.append(0); hi_e.append(0)
                bar_cols.append(C["ns_col"]); continue
            sl  = float(sub["Slope_Q"].values[0])
            lo  = float(sub["Slope_lo"].values[0])
            hi  = float(sub["Slope_hi"].values[0])
            s05 = bool(sub["sig_05"].values[0])
            Z   = float(sub["Z"].values[0])
            slopes_v.append(sl)
            lo_e.append(abs(sl - lo) if not np.isnan(lo) else 0)
            hi_e.append(abs(hi - sl) if not np.isnan(hi) else 0)
            bar_cols.append(_col_trend(s05, Z))

        for xi, (sl, le, he, bc) in enumerate(
                zip(slopes_v, lo_e, hi_e, bar_cols)):
            if np.isnan(sl): continue
            ax.bar(xi, sl, width=0.65, color=bc, alpha=0.82,
                   edgecolor="white", linewidth=0.5, zorder=3)
            ax.errorbar(xi, sl, yerr=[[le],[he]],
                        fmt="none", color="black",
                        capsize=5, capthick=1.5, lw=1.5, zorder=5)
        ax.axhline(0, color="black", lw=0.9, ls="--", alpha=0.45)
        ax.set_xticks(x); ax.set_xticklabels(codes,rotation=0,fontsize=11)
        ax.set_ylabel("β (mm yr⁻¹)", fontsize=11)
        ax.set_xlabel("Station", fontsize=11)
        ax.set_title(f"{panel}  {season_ttl}\n"
                     "Error bars: 95% CI  |  * p<0.05  ** p<0.01",
                     loc="left", fontsize=12, fontweight="bold", pad=5)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())

        for xi, stn in enumerate(stns):
            sub = trend_df[(trend_df["Station"]==stn) &
                           (trend_df["Scale"]==sk) &
                           (trend_df["Method"]=="Modified MK")]
            if len(sub)==0: continue
            s01=bool(sub["sig_01"].values[0]); s05=bool(sub["sig_05"].values[0])
            sl=float(sub["Slope_Q"].values[0])
            if np.isnan(sl): continue
            sig_s="**" if s01 else ("*" if s05 else "")
            if sig_s:
                ax.text(xi, sl+(1.0 if sl>=0 else -2.0), sig_s,
                        ha="center", fontsize=11, fontweight="bold")

    hand = [mpatches.Patch(color=C["inc"],    label="Increasing (sig.)"),
            mpatches.Patch(color=C["dec"],    label="Decreasing (sig.)"),
            mpatches.Patch(color=C["ns_col"], label="Not significant"),
            Line2D([0],[0],color="black",lw=2.2,label="Sen's slope / 95% CI")]
    fig.legend(handles=hand, loc="lower center", ncol=5, fontsize=15,
               markerscale=1.5, frameon=True, edgecolor="#B0BEC5", bbox_to_anchor=(0.5,-0.02))
    savefig(fig, str(out_dir/f"{prefix}_Fig2_WetDryTimeSeries"))
