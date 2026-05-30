"""Comparison figures: Fig4 (Standard MK vs Modified MK)."""

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


def fig4_mk_vs_mmk(comp_df, stns, smap, period, out_dir, prefix):
    """
    Fig 4: Side-by-side comparison of Standard MK and Modified MK.
    (a) Z-statistic scatter: MK Z vs MMK Z (diagonal = no change).
    (b) p-value scatter: MK p vs MMK p with α=0.05 threshold lines.
    (c) ΔZ (MMK−MK) per station × scale bar chart.
    (d) Agreement table heatmap.
    """
    stns  = [str(s) for s in stns]
    codes = [smap.get(s, s) for s in stns]
    scales_plot = ["annual","wet","dry"]
    scale_labels= [SCALE_META[sk]["label"] for sk in scales_plot]

    fig = plt.figure(figsize=(20, 14))
    gs  = gridspec.GridSpec(2, 2, figure=fig, hspace=0.48, wspace=0.32,
                            top=0.91, bottom=0.08, left=0.07, right=0.97)
    ax1 = fig.add_subplot(gs[0, 0])   # Z scatter
    ax2 = fig.add_subplot(gs[0, 1])   # p scatter
    ax3 = fig.add_subplot(gs[1, 0])   # ΔZ bar
    ax4 = fig.add_subplot(gs[1, 1])   # Agreement heatmap

    # Colour per scale
    sc_col = {"annual":C["annual"], "wet":C["wet"], "dry":C["dry"]}

    for sk in scales_plot:
        sub = comp_df[comp_df["Scale"]==sk]
        if len(sub)==0: continue
        ax1.scatter(sub["MK_Z"], sub["MMK_Z"],
                    color=sc_col[sk], s=80, alpha=0.80, zorder=4,
                    edgecolors="white", linewidth=0.6,
                    label=SCALE_META[sk]["label"])
        ax2.scatter(sub["MK_p"], sub["MMK_p"],
                    color=sc_col[sk], s=80, alpha=0.80, zorder=4,
                    edgecolors="white", linewidth=0.6)

    # Panel A: Z scatter
    z_all = pd.concat([comp_df["MK_Z"], comp_df["MMK_Z"]]).dropna()
    zmax  = max(abs(z_all.min()), abs(z_all.max()), 0.5)
    ax1.plot([-zmax,zmax],[-zmax,zmax],"k--",lw=1.3,alpha=0.55,
             label="1:1 (no change)")
    ax1.axhline(0,color="grey",lw=0.7,ls=":",alpha=0.5)
    ax1.axvline(0,color="grey",lw=0.7,ls=":",alpha=0.5)
    ax1.axhline( Z_005,color="orange",lw=1.2,ls="--",alpha=0.7,label=f"±Z₀.₀₅={Z_005}")
    ax1.axhline(-Z_005,color="orange",lw=1.2,ls="--",alpha=0.7)
    ax1.set_xlim(-zmax,zmax); ax1.set_ylim(-zmax,zmax)
    ax1.set_xlabel("Standard MK Z-statistic", fontsize=12)
    ax1.set_ylabel("Modified MK Z-statistic", fontsize=12)
    ax1.set_title("(a)  Z-Statistic: Standard MK vs Modified MK\n"
                  "     Points above 1:1 → autocorr. inflated MK Z",
                  loc="left",fontsize=12,fontweight="bold",pad=5)
    ax1.legend(fontsize=9.5,frameon=True,edgecolor="#B0BEC5",loc="upper left")
    ax1.set_aspect("equal",adjustable="box")
    ax1.spines["top"].set_visible(False); ax1.spines["right"].set_visible(False)

    # Panel B: p scatter
    ax2.plot([0,1],[0,1],"k--",lw=1.3,alpha=0.55,label="1:1 (no change)")
    ax2.axhline(ALPHA_005,color="orange",lw=1.2,ls="--",alpha=0.7,
                label=f"α=0.05")
    ax2.axvline(ALPHA_005,color="orange",lw=1.2,ls="--",alpha=0.7)
    ax2.set_xlim(0,1); ax2.set_ylim(0,1)
    ax2.set_xlabel("Standard MK p-value", fontsize=12)
    ax2.set_ylabel("Modified MK p-value", fontsize=12)
    ax2.set_title("(b)  p-Value: Standard MK vs Modified MK\n"
                  "     Points above 1:1 → MMK more conservative",
                  loc="left",fontsize=12,fontweight="bold",pad=5)
    # annotate significant points
    for _, row in comp_df.iterrows():
        mk_p=float(row["MK_p"]); mmk_p=float(row["MMK_p"])
        if mk_p<0.15 or mmk_p<0.15:
            code=row.get("Code",row["Station"])
            ax2.annotate(f"{code}",xy=(mk_p,mmk_p),
                         fontsize=7.5,color="black",alpha=0.7)
    for sk in scales_plot:
        ax2.scatter([],[], color=sc_col[sk], s=60, label=SCALE_META[sk]["label"])
    ax2.legend(fontsize=9.5,frameon=True,edgecolor="#B0BEC5",loc="upper left")
    ax2.set_aspect("equal",adjustable="box")
    ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)

    # Panel C: ΔZ per station×scale
    n_s=len(stns); x=np.arange(n_s)
    bw = 0.25
    for di,(sk,off) in enumerate(zip(scales_plot,
                                     [bw*(-1), 0, bw*(1)])):
        sub   = comp_df[comp_df["Scale"]==sk]
        dz_s  = {str(r["Station"]): r["delta_Z"] for _,r in sub.iterrows()}
        dz_arr= [dz_s.get(s,np.nan) for s in stns]
        bars  = ax3.bar(x+off, dz_arr, width=bw*0.88,
                        color=sc_col[sk], alpha=0.82,
                        edgecolor="white", linewidth=0.4,
                        label=SCALE_META[sk]["label"], zorder=3)
    ax3.axhline(0,color="black",lw=0.9,ls="--",alpha=0.5)
    ax3.set_xticks(x); ax3.set_xticklabels(codes,rotation=0,fontsize=11)
    ax3.set_ylabel("ΔZ  =  Z_MMK − Z_MK", fontsize=11)
    ax3.set_xlabel("Station", fontsize=11)
    ax3.set_title("(c)  ΔZ (MMK − Standard MK) per Station\n"
                  "     ΔZ < 0 → autocorrelation reduced |Z|  "
                  "(positive autocorr. inflates standard MK)",
                  loc="left",fontsize=12,fontweight="bold",pad=5)
    ax3.legend(fontsize=10,frameon=True,edgecolor="#B0BEC5",loc="upper right")
    ax3.spines["top"].set_visible(False); ax3.spines["right"].set_visible(False)
    ax3.yaxis.set_minor_locator(ticker.AutoMinorLocator())

    # Panel D: Agreement heatmap (station × scale)
    agree_mat = np.zeros((len(scales_plot), n_s), dtype=float)
    for si, stn in enumerate(stns):
        for sci, sk in enumerate(scales_plot):
            sub = comp_df[(comp_df["Station"]==stn) &
                          (comp_df["Scale"]==sk)]
            if len(sub)==0: agree_mat[sci,si]=np.nan; continue
            agree_mat[sci,si]=1.0 if bool(sub["Agree"].values[0]) else 0.0

    im = ax4.imshow(agree_mat, cmap="RdYlGn", vmin=0, vmax=1,
                    aspect="auto", interpolation="nearest")
    plt.colorbar(im, ax=ax4, orientation="horizontal",
                 pad=0.22, fraction=0.06, shrink=0.8,
                 label="Agreement (1=Same Trend, 0=Different)")
    for si in range(n_s):
        for sci,sk in enumerate(scales_plot):
            v=agree_mat[sci,si]
            if np.isnan(v): continue
            sub=comp_df[(comp_df["Station"]==stns[si]) &
                        (comp_df["Scale"]==sk)]
            if len(sub)==0: continue
            dz=float(sub["delta_Z"].values[0])
            tc="white" if abs(v-0.5)<0.4 else "black"
            ax4.text(si,sci,f"ΔZ={dz:+.2f}",ha="center",va="center",
                     fontsize=8.5,fontweight="bold",color=tc)
    ax4.set_xticks(range(n_s)); ax4.set_xticklabels(codes,fontsize=11,rotation=0)
    ax4.set_yticks(range(len(scales_plot)))
    ax4.set_yticklabels(scale_labels, fontsize=11)
    ax4.set_xlabel("Station", fontsize=11); ax4.set_ylabel("Scale", fontsize=11)
    ax4.set_title("(d)  Agreement Heatmap: Standard MK vs Modified MK\n"
                  "     Cell: ΔZ value  |  Green=agree, Red=disagree",
                  loc="left",fontsize=12,fontweight="bold",pad=5)

    savefig(fig, str(out_dir/f"{prefix}_Fig4_MK_vs_MMK_Comparison"))
