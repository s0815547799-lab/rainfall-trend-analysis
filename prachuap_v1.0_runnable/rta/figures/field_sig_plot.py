"""
rta.figures.field_sig_plot — Field-significance summary figure.

fig13_field_significance(field_sig_df, period, out_dir, prefix)
"""

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
from ..config import (C, DPI, SAVE_PDF, SCALE_META, Z_005, Z_001,
                      ALPHA_005, savefig)


# ── Expected columns in field_sig_df ─────────────────────────────────────────
#
#   Scale            : "annual" | "wet" | "dry"
#   N_stations       : int   total stations analysed
#   N_sig_MK         : int   # significant under Standard MK
#   N_sig_MMK        : int   # significant under Modified MK
#   Frac_sig_MK      : float fraction significant (Standard MK)
#   Frac_sig_MMK     : float fraction significant (Modified MK)
#   Walker_p_MK      : float Walker (1914) binomial p-value (Standard MK)
#   Walker_sig_MK    : bool  Walker field significance (Standard MK)
#   LC_S_obs_MK      : float Livezey-Chen observed count (Standard MK)
#   LC_p_MK          : float Livezey-Chen p-value (Standard MK)
#   LC_sig_MK        : bool  Livezey-Chen field significance (Standard MK)
#   LC_null_mean_MK  : float LC null-distribution mean
#   LC_null_95th_MK  : float LC null-distribution 95th percentile

_SCALE_ORDER  = ["annual", "wet", "dry"]
_SCALE_LABELS = {
    "annual": "Annual",
    "wet":    "Wet Season",
    "dry":    "Dry Season",
}


def fig13_field_significance(field_sig_df: pd.DataFrame,
                              period: str,
                              out_dir: str,
                              prefix: str) -> None:
    """
    Fig 13 — Field significance summary.

    Panel (a): grouped bar chart — fraction of significant stations per
               temporal scale for Standard MK and Modified MK.
    Panel (b): embedded text table summarising Walker and Livezey-Chen results.

    Parameters
    ----------
    field_sig_df : pd.DataFrame
        One row per temporal scale with the columns described in the module
        docstring.
    period  : str   Study period label (e.g. "1981–2014").
    out_dir : str   Output directory.
    prefix  : str   Filename prefix.
    """
    df = field_sig_df.copy()
    if "Scale" in df.columns:
        df["Scale"] = df["Scale"].str.lower().str.strip()

    # Reorder rows to standard scale order
    order_map = {s: i for i, s in enumerate(_SCALE_ORDER)}
    df["_order"] = df["Scale"].map(order_map)
    df = df.sort_values("_order").reset_index(drop=True)

    # ── Figure layout ─────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(14, 8))
    gs  = gridspec.GridSpec(1, 2, figure=fig,
                             width_ratios=[1.0, 1.3],
                             wspace=0.35)
    ax_bar = fig.add_subplot(gs[0, 0])
    ax_tbl = fig.add_subplot(gs[0, 1])

    # ══════════════════════════════════════════════════════════════════════════
    #  Panel (a) — Bar chart
    # ══════════════════════════════════════════════════════════════════════════
    n_scales  = len(df)
    bar_w     = 0.32
    x_base    = np.arange(n_scales)

    # Fraction values (guard against missing columns)
    frac_mk  = df.get("Frac_sig_MK",  pd.Series(np.nan, index=df.index)).values
    frac_mmk = df.get("Frac_sig_MMK", pd.Series(np.nan, index=df.index)).values

    # Replace NaN with 0 for plotting
    frac_mk_plot  = np.where(np.isnan(frac_mk.astype(float)),  0.0, frac_mk.astype(float))
    frac_mmk_plot = np.where(np.isnan(frac_mmk.astype(float)), 0.0, frac_mmk.astype(float))

    bars_mk = ax_bar.bar(
        x_base - bar_w / 2, frac_mk_plot, bar_w,
        color=C["mk_std"], edgecolor="k", linewidth=0.7,
        label="Standard MK", zorder=3)
    bars_mmk = ax_bar.bar(
        x_base + bar_w / 2, frac_mmk_plot, bar_w,
        color=C["mk_mod"], edgecolor="k", linewidth=0.7,
        label="Modified MK", zorder=3)

    # Horizontal threshold line (Walker: expected fraction under H0 = ALPHA_005)
    ax_bar.axhline(ALPHA_005, color=C["gold"], lw=1.4, ls="--", zorder=2,
                   label=f"α = {ALPHA_005} (Walker H₀ threshold)")

    # Star markers for Walker-significant bars (Standard MK only)
    walker_sig_col = "Walker_sig_MK"
    if walker_sig_col in df.columns:
        for i, (bar, sig) in enumerate(zip(bars_mk, df[walker_sig_col])):
            if bool(sig):
                bh = bar.get_height()
                ax_bar.text(bar.get_x() + bar.get_width() / 2.0,
                            bh + 0.01, "*",
                            ha="center", va="bottom",
                            fontsize=14, color=C["gold"], fontweight="bold")

    # x-axis
    scale_tick_labels = [
        _SCALE_LABELS.get(df["Scale"].iloc[i], df["Scale"].iloc[i])
        for i in range(n_scales)
    ]
    ax_bar.set_xticks(x_base)
    ax_bar.set_xticklabels(scale_tick_labels, fontsize=11)

    # y-axis
    ax_bar.set_ylim(0, min(1.05, max(float(np.nanmax(
        np.concatenate([frac_mk_plot, frac_mmk_plot])
    )) + 0.18, ALPHA_005 + 0.15)))
    ax_bar.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1.0, decimals=0))
    ax_bar.set_ylabel("Fraction of Significant Stations", fontsize=11)
    ax_bar.set_title("(a) Field Significance — Fraction Significant", fontsize=11, pad=8)

    ax_bar.spines["top"].set_visible(False)
    ax_bar.spines["right"].set_visible(False)
    ax_bar.legend(fontsize=9.5, loc="upper right",
                  framealpha=0.85, handlelength=1.4)
    ax_bar.grid(True, axis="y", linestyle="--", linewidth=0.4, alpha=0.4,
                color="#B0BEC5")

    # ══════════════════════════════════════════════════════════════════════════
    #  Panel (b) — Summary table
    # ══════════════════════════════════════════════════════════════════════════
    ax_tbl.set_axis_off()
    ax_tbl.set_title("(b) Field Significance Summary Table", fontsize=11, pad=8)

    # ── Build table data ──────────────────────────────────────────────────────
    col_headers = [
        "Scale",
        "Method",
        "N sig / N total",
        "Fraction",
        "Walker p",
        "Field Sig\n(Walker)",
        "LC p",
        "Field Sig\n(LC)",
    ]

    table_rows = []
    row_colors_list = []

    for _, row in df.iterrows():
        scale_lbl = _SCALE_LABELS.get(row["Scale"], row["Scale"].capitalize())
        n_total   = int(row.get("N_stations", 0))

        for method_label, n_sig_col, frac_col, \
            walker_p_col, walker_sig_col_r, \
            lc_p_col, lc_sig_col in [
                ("Standard MK",
                 "N_sig_MK",       "Frac_sig_MK",
                 "Walker_p_MK",    "Walker_sig_MK",
                 "LC_p_MK",        "LC_sig_MK"),
                ("Modified MK",
                 "N_sig_MMK",      "Frac_sig_MMK",
                 # Modified MK may not have dedicated Walker/LC columns;
                 # fall back gracefully
                 "Walker_p_MMK",   "Walker_sig_MMK",
                 "LC_p_MMK",       "LC_sig_MMK"),
        ]:
            n_sig = row.get(n_sig_col, np.nan)
            frac  = row.get(frac_col,  np.nan)
            w_p   = row.get(walker_p_col,   np.nan)
            w_sig = row.get(walker_sig_col_r, False)
            lc_p  = row.get(lc_p_col,  np.nan)
            lc_sig = row.get(lc_sig_col, False)

            # Format values
            n_sig_str = f"{int(n_sig)}" if pd.notna(n_sig) else "—"
            frac_str  = f"{float(frac):.1%}" if pd.notna(frac) else "—"
            w_p_str   = f"{float(w_p):.3f}"  if pd.notna(w_p)  else "—"
            w_sig_str = "Yes *" if bool(w_sig) else "No"
            lc_p_str  = f"{float(lc_p):.3f}" if pd.notna(lc_p) else "—"
            lc_sig_str = "Yes *" if bool(lc_sig) else "No"

            table_rows.append([
                scale_lbl,
                method_label,
                f"{n_sig_str} / {n_total}",
                frac_str,
                w_p_str,
                w_sig_str,
                lc_p_str,
                lc_sig_str,
            ])

            # Row colour: green if either Walker or LC is field-significant
            if bool(w_sig) or bool(lc_sig):
                row_colors_list.append(["#C8E6C9"] * len(col_headers))
            else:
                row_colors_list.append(["#F5F5F5"] * len(col_headers))

    # ── Render table ──────────────────────────────────────────────────────────
    if table_rows:
        # Use the full axes bounding box
        tbl = ax_tbl.table(
            cellText=table_rows,
            colLabels=col_headers,
            cellLoc="center",
            loc="center",
            cellColours=row_colors_list,
        )

        tbl.auto_set_font_size(False)
        tbl.set_fontsize(8.5)
        tbl.auto_set_column_width(list(range(len(col_headers))))

        # Style header row
        for c_idx in range(len(col_headers)):
            cell = tbl[(0, c_idx)]
            cell.set_facecolor(C["mk_std"])
            cell.set_text_props(color="white", fontweight="bold")

        # Scale cells: italic for scale name column
        for r_idx in range(1, len(table_rows) + 1):
            tbl[(r_idx, 0)].set_text_props(style="italic")

        tbl.scale(1.0, 1.65)
    else:
        ax_tbl.text(0.5, 0.5, "No field-significance data available.",
                    ha="center", va="center", fontsize=11,
                    transform=ax_tbl.transAxes)

    # ── Note below table ──────────────────────────────────────────────────────
    ax_tbl.text(0.0, -0.04,
                "* Field-significant at α = 0.05   "
                "Green rows = field significant (Walker or LC)",
                transform=ax_tbl.transAxes,
                fontsize=8, style="italic", color="#424242",
                va="top")

    fig.suptitle(
        f"Field Significance Analysis  |  {period}",
        fontsize=13, y=1.02)

    fig.tight_layout(rect=[0, 0, 1, 1])
    savefig(fig, f"{out_dir}/{prefix}_Fig13_FieldSignificance")
