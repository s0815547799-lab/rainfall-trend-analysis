"""Climatology figures: Fig7 (monthly climatology)."""

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


def fig7_monthly_climatology(scales, stns, smap, period, out_dir, prefix):
    """
    Fig 7: Mean monthly rainfall per station (line) + regional mean (bars).
    Clearly shows wet/dry season partitioning.
    """
    stns = [str(s) for s in stns]
    df_m = scales["monthly_all"]
    n_s  = len(stns)

    fig, axes = plt.subplots(math.ceil(n_s/4)+1, min(4,n_s),
                              figsize=(18, 4*(math.ceil(n_s/4)+1)),
                              squeeze=False)
    fig.subplots_adjust(hspace=0.55, wspace=0.30,
                        top=0.93, bottom=0.06, left=0.06, right=0.97)

    # Regional mean monthly
    cols    = [s for s in stns if s in df_m.columns]
    reg_m   = df_m[cols].copy()
    reg_m["month"] = reg_m.index.month
    clim_reg= reg_m.groupby("month")[cols].mean().mean(axis=1)

    # Ax0: Regional mean
    ax0 = axes[0][0]
    months = np.arange(1,13)
    bar_col = [C["wet_lt"] if m in WET_MONTHS else C["dry_lt"] for m in months]
    ax0.bar(months, clim_reg.values, color=bar_col, edgecolor="grey",
            linewidth=0.6, alpha=0.85, zorder=3)
    ax0.set_xticks(months)
    ax0.set_xticklabels(MONTH_ABBR, rotation=0, fontsize=9)
    ax0.set_ylabel("Mean Monthly\nRainfall (mm)", fontsize=10)
    ax0.set_title("(a)  Regional Mean Monthly Climatology\n"
                  "     Blue=Wet (May–Oct)  |  Orange=Dry (Nov–Apr)",
                  loc="left", fontsize=10.5, fontweight="bold", pad=4)
    ax0.set_ylim(bottom=0)
    ax0.spines["top"].set_visible(False); ax0.spines["right"].set_visible(False)

    # Axhline to mark wet/dry boundary
    for ax_ref in [ax0]:
        for m in [4.5, 10.5]:
            ax_ref.axvline(m, color="black", lw=1.0, ls="--", alpha=0.5)

    # Per-station panels
    for si, stn in enumerate(stns):
        row = (si + 1) // 4;  col_i = (si + 1) % 4
        ax  = axes[row][col_i] if row < axes.shape[0] else None
        if ax is None: continue
        if stn not in df_m.columns: ax.set_visible(False); continue

        stn_m = df_m[[stn]].copy()
        stn_m["month"] = stn_m.index.month
        clim_s = stn_m.groupby("month")[stn].mean()
        bar_c2 = [C["wet"] if m in WET_MONTHS else C["dry"] for m in months]
        ax.bar(months, clim_s.values, color=bar_c2, edgecolor="white",
               linewidth=0.4, alpha=0.78, zorder=3)
        ax.set_xticks(months)
        ax.set_xticklabels(MONTH_ABBR, rotation=45, fontsize=7.5)
        ax.set_ylabel("mm", fontsize=9, labelpad=2)
        ax.set_title(f"({chr(97+si+1)})  {smap.get(stn,stn)} [{stn}]",
                     loc="left", fontsize=9.5, fontweight="bold", pad=3)
        ax.set_ylim(bottom=0)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

    for idx in range(len(stns)+1, axes.size):
        axes.flat[idx].set_visible(False)

    # wet/dry legend
    hand = [mpatches.Patch(color=C["wet_lt"],label="Wet Season (May–Oct)"),
            mpatches.Patch(color=C["dry_lt"],label="Dry Season (Nov–Apr)")]
    fig.legend(handles=hand, loc="lower center", ncol=5, fontsize=15,
               markerscale=1.5, frameon=True, edgecolor="#B0BEC5", bbox_to_anchor=(0.5,-0.02))
    savefig(fig, str(out_dir/f"{prefix}_Fig7_MonthlyClimatology"))
