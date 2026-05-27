"""Heatmap figures: Fig5 (significance heatmap)."""

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


def fig5_significance_heatmap(trend_df, stns, smap, period, out_dir, prefix):
    """Fig 5: Z-stat heatmap (station × scale) for Standard MK and Modified MK."""
    stns   = [str(s) for s in stns]
    codes  = [smap.get(s, s) for s in stns]
    scales = ["annual","wet","dry"]
    n_s    = len(stns)

    fig, axes = plt.subplots(2, 1, figsize=(max(14,n_s+6), 13))
    fig.subplots_adjust(hspace=0.55, top=0.91, bottom=0.10,
                        left=0.12, right=0.97)

    for ai, (method, ax) in enumerate([("Standard MK",axes[0]),
                                        ("Modified MK",axes[1])]):
        Z_mat = np.full((len(scales), n_s), np.nan)
        p_mat = np.full((len(scales), n_s), np.nan)
        sl_mat= np.full((len(scales), n_s), np.nan)
        sg_mat= np.zeros((len(scales), n_s), dtype=int)

        for si, stn in enumerate(stns):
            for sci, sk in enumerate(scales):
                sub = trend_df[(trend_df["Station"]==stn) &
                               (trend_df["Scale"]==sk) &
                               (trend_df["Method"]==method)]
                if len(sub)==0: continue
                Z_mat[sci,si]  = float(sub["Z"].values[0])
                p_mat[sci,si]  = float(sub["p_value"].values[0])
                sl_mat[sci,si] = float(sub["Slope_Q"].values[0])
                if bool(sub["sig_01"].values[0]): sg_mat[sci,si]=2
                elif bool(sub["sig_05"].values[0]): sg_mat[sci,si]=1

        abs_max=max(np.nanmax(np.abs(Z_mat)) if not np.all(np.isnan(Z_mat)) else 3, Z_001+0.5)
        im=ax.imshow(Z_mat,cmap="RdBu_r",vmin=-abs_max,vmax=abs_max,
                     aspect="auto",interpolation="nearest")
        cbar=plt.colorbar(im,ax=ax,orientation="vertical",
                          pad=0.02,fraction=0.03,shrink=0.95)
        cbar.set_label("Z-statistic",fontsize=10)
        cbar.ax.axhline( Z_005,color="orange",lw=1.4,ls="--")
        cbar.ax.axhline(-Z_005,color="orange",lw=1.4,ls="--")
        cbar.ax.axhline( Z_001,color="red",   lw=1.4,ls="-")
        cbar.ax.axhline(-Z_001,color="red",   lw=1.4,ls="-")

        for sci in range(len(scales)):
            for si in range(n_s):
                Z_v=Z_mat[sci,si]; p_v=p_mat[sci,si]; sl_v=sl_mat[sci,si]
                if np.isnan(Z_v): continue
                lp=abs(Z_v)/abs_max
                tc="white" if lp>0.70 else "black"
                sig_s=("**" if sg_mat[sci,si]==2 else
                        "*"  if sg_mat[sci,si]==1 else "ns")
                ax.text(si,sci,
                        f"Z={Z_v:.2f}\nβ={sl_v:+.1f}\np={p_v:.3f} {sig_s}",
                        ha="center",va="center",fontsize=7.5,
                        fontweight="bold" if sg_mat[sci,si]>0 else "normal",
                        color=tc,linespacing=1.35)

        ax.set_xticks(range(n_s)); ax.set_xticklabels(codes,fontsize=11,rotation=0)
        ax.set_yticks(range(len(scales)))
        ax.set_yticklabels([SCALE_META[sk]["label"] for sk in scales],fontsize=11)
        ax.set_xlabel("Station",fontsize=11,labelpad=4)
        ax.set_title(f"({chr(97+ai)})  {method} — Z-Statistic Heatmap\n"
                     "     Cell: Z | β (mm/yr) | p | significance",
                     loc="left",fontsize=12,fontweight="bold",pad=5)

    savefig(fig, str(out_dir/f"{prefix}_Fig5_Significance_Heatmap"))
