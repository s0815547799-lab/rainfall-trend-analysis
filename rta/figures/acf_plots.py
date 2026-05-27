"""Autocorrelation figures: Fig6 (autocorrelation diagnostics)."""

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


def fig6_autocorrelation(scales, stns, smap, period, out_dir, prefix):
    """Fig 6: Lag-1 r₁ per station (3 scales) + ACF for regional mean."""
    stns  = [str(s) for s in stns]
    codes = [smap.get(s, s) for s in stns]
    n_s   = len(stns)
    sc_list = ["annual","wet","dry"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
    fig.subplots_adjust(left=0.07,right=0.97,top=0.88,bottom=0.12,wspace=0.30)

    # ── Panel A: Lag-1 r₁ grouped bars ───────────────────────────────────
    x = np.arange(n_s); bw = 0.25
    offsets = [bw*(-1), 0, bw*(1)]
    for di,(sk,off) in enumerate(zip(sc_list, offsets)):
        df_s = scales[sk]
        r1_v = [lag_k_autocorr(df_s[s].dropna().values.astype(float))
                if s in df_s.columns else np.nan for s in stns]
        col  = SCALE_META[sk]["color"]
        bars = ax1.bar(x+off, [r if not np.isnan(r) else 0 for r in r1_v],
                       width=bw*0.88, color=col, alpha=0.82,
                       edgecolor="white", linewidth=0.4,
                       label=SCALE_META[sk]["label"], zorder=3)
        for xi,(r,s) in enumerate(zip(r1_v,stns)):
            if np.isnan(r): continue
            sig=is_sig_autocorr(r, int(df_s[s].dropna().__len__()))
            if sig:
                ax1.text(x[xi]+off, r+(0.02 if r>=0 else -0.04),
                         "*",ha="center",fontsize=11,fontweight="bold",
                         color=col)

    # 95% band (Bartlett, approximate n=34)
    n_approx = int(np.mean([len(scales["annual"][s].dropna())
                             for s in stns if s in scales["annual"].columns]))
    ci95 = scipy_norm.ppf(0.975) / math.sqrt(n_approx)
    ax1.axhline( ci95,color="red",lw=1.5,ls="--",label=f"95% band (±{ci95:.3f})")
    ax1.axhline(-ci95,color="red",lw=1.5,ls="--")
    ax1.axhline(0,color="black",lw=0.8,ls="-",alpha=0.4)
    ax1.set_xticks(x); ax1.set_xticklabels(codes,rotation=0,fontsize=11)
    ax1.set_ylabel("Lag-1 Autocorrelation (r₁)",fontsize=12)
    ax1.set_xlabel("Station",fontsize=12)
    ax1.set_ylim(-1,1)
    ax1.set_title("(a)  Lag-1 Autocorrelation — Annual, Wet, Dry\n"
                  "     * = significant (α=0.05)  |  Dashed: 95% threshold",
                  loc="left",fontsize=12,fontweight="bold",pad=5)
    ax1.legend(fontsize=10,frameon=True,edgecolor="#B0BEC5",loc="upper right")
    ax1.spines["top"].set_visible(False); ax1.spines["right"].set_visible(False)

    # ── Panel B: ACF of regional mean annual ─────────────────────────────
    cols    = [s for s in stns if s in scales["annual"].columns]
    reg_ann = scales["annual"][cols].mean(axis=1).dropna().values.astype(float)
    n_reg   = len(reg_ann)
    max_lag = min(10, n_reg // 3)
    rho_all = all_lag_autocorr(reg_ann, max_lag=max_lag)
    lags    = np.arange(1, len(rho_all)+1)
    ci_acf  = scipy_norm.ppf(0.975) / math.sqrt(n_reg)

    ax2.bar(lags, rho_all, width=0.65, color=C["annual"],
            alpha=0.75, edgecolor="white", linewidth=0.5, zorder=3)
    ax2.axhline( ci_acf,color="red",lw=1.5,ls="--",label=f"95% CI (±{ci_acf:.3f})")
    ax2.axhline(-ci_acf,color="red",lw=1.5,ls="--")
    ax2.axhline(0,color="black",lw=0.8,ls="-",alpha=0.4)
    for lg,rho_v in zip(lags,rho_all):
        if abs(rho_v)>ci_acf:
            ax2.text(lg,rho_v+(0.03 if rho_v>=0 else -0.05),
                     f"{rho_v:.2f}*",ha="center",va="bottom" if rho_v>=0 else "top",
                     fontsize=9,fontweight="bold",color=C["dec"])
    ax2.set_xticks(lags)
    ax2.set_xlabel("Lag (years)",fontsize=12)
    ax2.set_ylabel("Autocorrelation Coefficient (rₖ)",fontsize=12)
    ax2.set_ylim(-1,1)
    ax2.set_title(f"(b)  ACF — Regional Mean Annual Rainfall (Lag 1–{max_lag})\n"
                  "     Significant rₖ → Modified MK essential",
                  loc="left",fontsize=12,fontweight="bold",pad=5)
    ax2.legend(fontsize=10,frameon=True,edgecolor="#B0BEC5")
    ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)

    savefig(fig, str(out_dir/f"{prefix}_Fig6_Autocorrelation"))
