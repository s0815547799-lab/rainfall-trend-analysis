"""Bar chart figures: Fig3 (Sen's slope all scales)."""

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


def fig3_sens_all(trend_df, stns, smap, period, out_dir, prefix):
    """Fig 3: Sen's slope bar chart for Annual/Wet/Dry — 3 rows × MMK results."""
    stns  = [str(s) for s in stns]
    codes = [smap.get(s, s) for s in stns]
    n_s   = len(stns)
    x     = np.arange(n_s)
    fig, axes = plt.subplots(3, 1, figsize=(max(14,n_s*1.1+4), 14),
                              sharex=True)
    fig.subplots_adjust(hspace=0.42, top=0.93, bottom=0.09,
                        left=0.07, right=0.97)

    for pi, (sk, col_l) in enumerate(
            [("annual",C["annual"]),("wet",C["wet"]),("dry",C["dry"])]):
        ax = axes[pi]
        meta = SCALE_META[sk]
        slopes_v=[]; lo_e=[]; hi_e=[]; bar_cols=[]
        for stn in stns:
            sub = trend_df[(trend_df["Station"]==stn) &
                           (trend_df["Scale"]==sk) &
                           (trend_df["Method"]=="Modified MK")]
            if len(sub)==0:
                slopes_v.append(np.nan); lo_e.append(0); hi_e.append(0)
                bar_cols.append(C["ns_col"]); continue
            sl=float(sub["Slope_Q"].values[0])
            lo=float(sub["Slope_lo"].values[0])
            hi=float(sub["Slope_hi"].values[0])
            s05=bool(sub["sig_05"].values[0])
            Z=float(sub["Z"].values[0])
            slopes_v.append(sl)
            lo_e.append(abs(sl-lo) if not np.isnan(lo) else 0)
            hi_e.append(abs(hi-sl) if not np.isnan(hi) else 0)
            bar_cols.append(_col_trend(s05, Z))

        for xi,(sl,le,he,bc) in enumerate(zip(slopes_v,lo_e,hi_e,bar_cols)):
            if np.isnan(sl): continue
            ax.bar(xi,sl,width=0.65,color=bc,alpha=0.82,
                   edgecolor="white",linewidth=0.5,zorder=3)
            ax.errorbar(xi,sl,yerr=[[le],[he]],fmt="none",color="black",
                        capsize=5,capthick=1.5,lw=1.5,zorder=5)
            yoff=0.8 if sl>=0 else -1.5
            ax.text(xi,sl+yoff,f"{sl:+.1f}",ha="center",
                    va="bottom" if sl>=0 else "top",fontsize=8.5,fontweight="bold")

        # significance stars
        for xi,stn in enumerate(stns):
            sub=trend_df[(trend_df["Station"]==stn) &
                         (trend_df["Scale"]==sk) &
                         (trend_df["Method"]=="Modified MK")]
            if len(sub)==0: continue
            s01=bool(sub["sig_01"].values[0]); s05=bool(sub["sig_05"].values[0])
            sl=float(sub["Slope_Q"].values[0])
            if np.isnan(sl): continue
            sig_s="**" if s01 else ("*" if s05 else "")
            if sig_s:
                ax.text(xi,sl+(1.5 if sl>=0 else -2.5),sig_s,
                        ha="center",fontsize=11,fontweight="bold",color="black")

        ax.axhline(0, color="black", lw=0.9, ls="--", alpha=0.45)
        ax.set_ylabel(f"β (mm yr⁻¹)\n{meta['label']}",fontsize=11)
        ax.set_title(f"({chr(97+pi)})  {meta['label']} — Sen's Slope (Modified MK)",
                     loc="left",fontsize=12,fontweight="bold",pad=4)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(codes,rotation=0,ha="center",fontsize=11)
    axes[-1].set_xlabel("Station",fontsize=12,labelpad=5)
    hand=[mpatches.Patch(color=C["inc"],label="Increasing (sig.)"),
          mpatches.Patch(color=C["dec"],label="Decreasing (sig.)"),
          mpatches.Patch(color=C["ns_col"],label="Not significant"),
          Line2D([0],[0],color="black",lw=1.8,marker="|",ms=8,label="95% CI")]
    fig.legend(handles=hand, loc="lower center", ncol=5, fontsize=15,
               markerscale=1.5, frameon=True, edgecolor="#B0BEC5", bbox_to_anchor=(0.5,-0.02))
    savefig(fig, str(out_dir/f"{prefix}_Fig3_SenSlope_AllScales"))
