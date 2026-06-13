"""Spatial summary figures: Fig8 (spatial trend summary)."""

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
from .helpers import _sig_label, _col_trend


def fig8_spatial_summary(trend_df, comp_df, stns, smap, period,
                          out_dir, prefix):
    """
    Fig 8: Multi-panel spatial trend summary.
    (a) Bubble chart: x=Sen's slope, y=Z, size=n, colour=scale.
    (b) Stacked bar: % increasing / decreasing / no-trend per scale+method.
    (c) ΔSlope (Wet−Dry) per station.
    (d) Slope ratio heatmap (station × scale × method).
    """
    stns  = [str(s) for s in stns]
    codes = [smap.get(s, s) for s in stns]
    n_s   = len(stns)
    scales_plot = ["annual","wet","dry"]

    fig = plt.figure(figsize=(20,14))
    gs  = gridspec.GridSpec(2,2,figure=fig,hspace=0.48,wspace=0.32,
                            top=0.91,bottom=0.08,left=0.07,right=0.97)
    ax1=fig.add_subplot(gs[0,0]); ax2=fig.add_subplot(gs[0,1])
    ax3=fig.add_subplot(gs[1,0]); ax4=fig.add_subplot(gs[1,1])

    # ── Panel A: Bubble — slope vs Z ────────────────────────────────────
    for sk in scales_plot:
        sub=trend_df[(trend_df["Scale"]==sk) &
                     (trend_df["Method"]=="Modified MK")]
        ax1.scatter(sub["Slope_Q"], sub["Z"],
                    s=80, color=SCALE_META[sk]["color"],
                    alpha=0.80, edgecolors="white", linewidth=0.6,
                    label=SCALE_META[sk]["label"], zorder=4)
    ax1.axhline( Z_005,color="orange",lw=1.2,ls="--",alpha=0.7,label=f"±Z₀.₀₅")
    ax1.axhline(-Z_005,color="orange",lw=1.2,ls="--",alpha=0.7)
    ax1.axhline(0,color="grey",lw=0.8,ls=":",alpha=0.5)
    ax1.axvline(0,color="grey",lw=0.8,ls=":",alpha=0.5)
    ax1.set_xlabel("Sen's Slope β (mm yr⁻¹)",fontsize=12)
    ax1.set_ylabel("Modified MK Z-statistic",fontsize=12)
    ax1.set_title("(a)  Sen's Slope vs Z-Statistic\n"
                  "     Modified MK  |  All scales",
                  loc="left",fontsize=12,fontweight="bold",pad=5)
    ax1.legend(fontsize=10,frameon=True,edgecolor="#B0BEC5",loc="upper left")
    ax1.spines["top"].set_visible(False); ax1.spines["right"].set_visible(False)

    # ── Panel B: Stacked bar — trend counts ──────────────────────────────
    method_list = ["Standard MK","Modified MK"]
    cats  = ["Increasing","Decreasing","No trend"]
    cat_col={"Increasing":C["inc"],"Decreasing":C["dec"],"No trend":C["ns_col"]}
    bar_labs = []
    for sk in scales_plot:
        for meth in method_list:
            bar_labs.append(f"{SCALE_META[sk]['label'][:3]}\n{meth[:3]}")
    x2 = np.arange(len(bar_labs))

    for cat_i, cat in enumerate(cats):
        counts = []
        for sk in scales_plot:
            for meth in method_list:
                sub=trend_df[(trend_df["Scale"]==sk) &
                             (trend_df["Method"]==meth)]
                n_cat = sub["sig_05"].sum() if cat=="Increasing" else 0
                if cat=="Decreasing":
                    n_cat=int(((sub["sig_05"]==True) & (sub["Z"]<0)).sum())
                elif cat=="Increasing":
                    n_cat=int(((sub["sig_05"]==True) & (sub["Z"]>0)).sum())
                elif cat=="No trend":
                    n_cat=int((sub["sig_05"]==False).sum())
                counts.append(n_cat)
        if cat_i==0:
            bottom=np.zeros(len(bar_labs))
        ax2.bar(x2, counts, bottom=bottom, color=cat_col[cat],
                alpha=0.85, edgecolor="white", linewidth=0.5,
                label=cat, zorder=3)
        for xi,(c,b) in enumerate(zip(counts,bottom)):
            if c>0:
                ax2.text(xi,b+c/2,str(c),ha="center",va="center",
                         fontsize=9,fontweight="bold",color="white")
        bottom += np.array(counts)

    ax2.set_xticks(x2); ax2.set_xticklabels(bar_labs,fontsize=8,rotation=0)
    ax2.set_ylabel("Number of stations",fontsize=11)
    ax2.set_title("(b)  Trend Count by Scale and Method\n"
                  "     (Increasing / Decreasing / No trend at p<0.05)",
                  loc="left",fontsize=12,fontweight="bold",pad=5)
    ax2.legend(fontsize=10,frameon=True,edgecolor="#B0BEC5",loc="upper right")
    ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)
    ax2.set_ylim(bottom=0)

    # ── Panel C: ΔSlope (Wet − Dry) ─────────────────────────────────────
    wet_sl = {str(r["Station"]):r["Slope_Q"]
               for _,r in trend_df[(trend_df["Scale"]=="wet") &
                                    (trend_df["Method"]=="Modified MK")].iterrows()}
    dry_sl = {str(r["Station"]):r["Slope_Q"]
               for _,r in trend_df[(trend_df["Scale"]=="dry") &
                                    (trend_df["Method"]=="Modified MK")].iterrows()}
    delta  = [wet_sl.get(s,np.nan)-dry_sl.get(s,np.nan) for s in stns]
    col_d  = [C["wet"] if d>0 else C["dry"] for d in delta]
    ax3.bar(range(n_s), delta, width=0.65, color=col_d, alpha=0.82,
            edgecolor="white", linewidth=0.5, zorder=3)
    ax3.axhline(0,color="black",lw=0.9,ls="--",alpha=0.45)
    for xi,d in enumerate(delta):
        if np.isnan(d): continue
        ax3.text(xi,d+(0.5 if d>=0 else -1.0),f"{d:+.1f}",
                 ha="center",va="bottom" if d>=0 else "top",
                 fontsize=8.5,fontweight="bold")
    ax3.set_xticks(range(n_s)); ax3.set_xticklabels(codes,rotation=0,fontsize=11)
    ax3.set_ylabel("ΔSlope = β_Wet − β_Dry  (mm yr⁻¹)",fontsize=11)
    ax3.set_xlabel("Station",fontsize=11)
    ax3.set_title("(c)  Wet–Dry Slope Difference (ΔSlope)\n"
                  "     Blue > 0: stronger wet-season trend  |  "
                  "Orange < 0: stronger dry-season trend",
                  loc="left",fontsize=12,fontweight="bold",pad=5)
    ax3.spines["top"].set_visible(False); ax3.spines["right"].set_visible(False)
    ax3.yaxis.set_minor_locator(ticker.AutoMinorLocator())

    # ── Panel D: Slope ratio heatmap (method × scale, station mean) ──────
    meth_list2 = ["Standard MK","Modified MK"]
    mat = np.full((len(meth_list2)*3, n_s), np.nan)
    ylabels = []
    for ri,(meth,sk) in enumerate(
            [(m,sk2) for sk2 in scales_plot for m in meth_list2]):
        sub=trend_df[(trend_df["Scale"]==sk) & (trend_df["Method"]==meth)]
        sl_dict={str(r["Station"]):r["Slope_Q"] for _,r in sub.iterrows()}
        for si,stn in enumerate(stns):
            mat[ri,si]=sl_dict.get(stn,np.nan)
        ylabels.append(f"{SCALE_META[sk]['label'][:10]}\n({meth[:3]})")

    abs_m=np.nanmax(np.abs(mat)) if not np.all(np.isnan(mat)) else 10
    im=ax4.imshow(mat,cmap="RdYlGn",vmin=-abs_m,vmax=abs_m,
                  aspect="auto",interpolation="nearest")
    plt.colorbar(im,ax=ax4,orientation="horizontal",
                 pad=0.20,fraction=0.06,shrink=0.85,
                 label="Sen's Slope β (mm yr⁻¹)")
    for ri in range(mat.shape[0]):
        for si in range(n_s):
            v=mat[ri,si]
            if np.isnan(v): continue
            lp=v/abs_m
            tc="white" if abs(lp)>0.70 else "black"
            ax4.text(si,ri,f"{v:+.1f}",ha="center",va="center",
                     fontsize=8.5,fontweight="bold",color=tc)
    ax4.set_xticks(range(n_s)); ax4.set_xticklabels(codes,fontsize=11,rotation=0)
    ax4.set_yticks(range(len(ylabels))); ax4.set_yticklabels(ylabels,fontsize=9)
    ax4.set_xlabel("Station",fontsize=11)
    ax4.set_title("(d)  Sen's Slope Heatmap — All Methods × Scales\n"
                  "     Green=increasing, Red=decreasing",
                  loc="left",fontsize=12,fontweight="bold",pad=5)

    savefig(fig, str(out_dir/f"{prefix}_Fig8_SpatialTrend_Summary"))
