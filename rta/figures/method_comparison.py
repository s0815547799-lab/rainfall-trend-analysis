"""
rta.figures.method_comparison — Z-statistic comparison across MK variants.

fig10_z_comparison_matrix(trend_df, stns, smap, period, out_dir, prefix)
fig11_method_comparison_scatter(trend_df, stns, smap, period, out_dir, prefix)
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


# ── Column-name conventions expected in trend_df ─────────────────────────────
#
#   trend_df is a long-form DataFrame with at least the columns:
#       Station, Scale, Method, Z, sig_05, sig_01
#
#   Method values expected: "Standard MK", "Modified MK (H&R98)",
#                           "PW-MK", "TFPW-MK"
#
# If the exact column names differ in the caller's DataFrame, only the
# columns listed above are required; everything else is ignored.

_METHOD_KEYS  = ["Standard MK", "Modified MK (H&R98)", "PW-MK", "TFPW-MK"]
_METHOD_SHORT = {
    "Standard MK":         "MK",
    "Modified MK (H&R98)": "MMK",
    "PW-MK":               "PW-MK",
    "TFPW-MK":             "TFPW-MK",
}
_PANEL_LABELS = ["(a)", "(b)", "(c)", "(d)"]
_SCALE_ORDER  = ["annual", "wet", "dry"]
_SCALE_LABELS = {
    "annual": "Annual",
    "wet":    "Wet",
    "dry":    "Dry",
}


def _sig_marker(row) -> str:
    """Return **, * or '' depending on significance columns."""
    try:
        if bool(row.get("sig_01", False)):
            return "**"
        if bool(row.get("sig_05", False)):
            return "*"
    except Exception:
        pass
    return ""


# ─────────────────────────────────────────────────────────────────────────────
#   Fig 10 — 2×2 Z-statistic heatmap matrix
# ─────────────────────────────────────────────────────────────────────────────

def fig10_z_comparison_matrix(trend_df: pd.DataFrame, stns: list,
                               smap: dict, period: str,
                               out_dir: str, prefix: str) -> None:
    """
    Fig 10 — Four-panel heatmap (one panel per MK method) showing Z-statistics.

    Each panel: rows = temporal scale (Annual / Wet / Dry),
                columns = stations,
                cell colour = Z value (RdBu_r, symmetric about 0).

    Parameters
    ----------
    trend_df : pd.DataFrame  Long-form results with columns:
                             Station, Scale, Method, Z, sig_05, sig_01
    stns     : list          Ordered station names.
    smap     : dict          {station_name: short_code}.
    period   : str           Study period label.
    out_dir  : str           Output directory.
    prefix   : str           Filename prefix.
    """
    fig = plt.figure(figsize=(20, 13))
    gs  = gridspec.GridSpec(2, 2, figure=fig,
                             hspace=0.42, wspace=0.30)

    # ── Build a 3-D pivot: method → scale × station ─────────────────────────
    # Normalise the Scale column to lowercase keys
    df = trend_df.copy()
    if "Scale" in df.columns:
        df["Scale"] = df["Scale"].str.lower().str.strip()
    if "Method" in df.columns:
        df["Method"] = df["Method"].str.strip()

    # Collect all Z values for a symmetric colorbar range
    all_z = df["Z"].dropna().values
    vmax  = float(np.nanpercentile(np.abs(all_z), 98)) if len(all_z) else 3.0
    vmax  = max(vmax, Z_005 + 0.5)
    vmin  = -vmax

    cmap_hm = plt.cm.RdBu_r

    # Short station labels for x-axis
    x_labels = [smap.get(s, s) for s in stns]

    axes_list = []
    for m_idx, method_key in enumerate(_METHOD_KEYS):
        row, col = divmod(m_idx, 2)
        ax = fig.add_subplot(gs[row, col])
        axes_list.append(ax)

        # Slice for this method
        sub = df[df["Method"] == method_key]

        # Build matrix: rows = scales, cols = stations
        z_matrix  = np.full((len(_SCALE_ORDER), len(stns)), np.nan)
        sig05_mat = np.zeros((len(_SCALE_ORDER), len(stns)), dtype=bool)
        sig01_mat = np.zeros((len(_SCALE_ORDER), len(stns)), dtype=bool)

        for r_idx, scale_key in enumerate(_SCALE_ORDER):
            scale_sub = sub[sub["Scale"] == scale_key]
            for c_idx, stn in enumerate(stns):
                stn_row = scale_sub[scale_sub["Station"] == stn]
                if len(stn_row) == 0:
                    continue
                stn_row = stn_row.iloc[0]
                z_val = stn_row.get("Z", np.nan)
                if pd.notna(z_val):
                    z_matrix[r_idx, c_idx] = float(z_val)
                sig05_mat[r_idx, c_idx] = bool(stn_row.get("sig_05", False))
                sig01_mat[r_idx, c_idx] = bool(stn_row.get("sig_01", False))

        im = ax.imshow(z_matrix, aspect="auto", cmap=cmap_hm,
                        vmin=vmin, vmax=vmax, interpolation="nearest")

        # Cell annotations
        for r_idx in range(len(_SCALE_ORDER)):
            for c_idx in range(len(stns)):
                z_val = z_matrix[r_idx, c_idx]
                if np.isnan(z_val):
                    cell_txt = "—"
                else:
                    marker = "**" if sig01_mat[r_idx, c_idx] \
                             else "*" if sig05_mat[r_idx, c_idx] else ""
                    cell_txt = f"{z_val:.2f}{marker}"
                # Choose text colour for legibility
                bg_norm  = (z_val - vmin) / (vmax - vmin) \
                           if not np.isnan(z_val) else 0.5
                txt_col  = "white" if (bg_norm < 0.2 or bg_norm > 0.8) \
                           else "black"
                ax.text(c_idx, r_idx, cell_txt,
                        ha="center", va="center",
                        fontsize=7.5, color=txt_col)

        ax.set_xticks(range(len(stns)))
        ax.set_xticklabels(x_labels, rotation=45, ha="right", fontsize=9)
        ax.set_yticks(range(len(_SCALE_ORDER)))
        ax.set_yticklabels([_SCALE_LABELS[s] for s in _SCALE_ORDER],
                           fontsize=10)

        short = _METHOD_SHORT.get(method_key, method_key)
        panel = _PANEL_LABELS[m_idx]
        ax.set_title(f"{panel} {short}  |  Z-statistic",
                     fontsize=11, pad=7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Colour bar per panel
        cbar = fig.colorbar(im, ax=ax, orientation="vertical",
                             fraction=0.046, pad=0.04)
        cbar.set_label("Z-statistic", fontsize=9)
        cbar.ax.tick_params(labelsize=8)
        # Threshold lines on colorbar
        for zline in [-Z_005, Z_005]:
            norm_val = (zline - vmin) / (vmax - vmin)
            cbar.ax.axhline(norm_val, color="#FF8F00", lw=1.0, ls="--")

    # Significance note
    fig.text(0.5, 0.01,
             "* p < 0.05   ** p < 0.01   Orange dashed lines = ±1.96 threshold",
             ha="center", fontsize=9.5, style="italic", color="#424242")

    fig.suptitle(
        f"Z-Statistic Comparison Matrix — All Methods  |  {period}",
        fontsize=13, y=1.01)

    savefig(fig, f"{out_dir}/{prefix}_Fig10_ZComparisonMatrix")


# ─────────────────────────────────────────────────────────────────────────────
#   Fig 11 — Scatter: alternative method Z vs Standard MK Z
# ─────────────────────────────────────────────────────────────────────────────

def fig11_method_comparison_scatter(trend_df: pd.DataFrame, stns: list,
                                     smap: dict, period: str,
                                     out_dir: str, prefix: str) -> None:
    """
    Fig 11 — Three-panel scatter comparing alternative MK variant Z-statistics
    against Standard MK Z (one panel per comparison).

    Panels: (a) MMK vs MK, (b) PW-MK vs MK, (c) TFPW-MK vs MK.
    Points = (station × temporal scale) combinations.
    Colour by scale; shape by station if ≤ 8 stations.

    Parameters
    ----------
    trend_df : pd.DataFrame  Long-form results (Station, Scale, Method, Z,
                             sig_05, sig_01).
    stns     : list          Ordered station names.
    smap     : dict          {station_name: short_code}.
    period   : str           Study period label.
    out_dir  : str           Output directory.
    prefix   : str           Filename prefix.
    """
    df = trend_df.copy()
    if "Scale" in df.columns:
        df["Scale"] = df["Scale"].str.lower().str.strip()
    if "Method" in df.columns:
        df["Method"] = df["Method"].str.strip()

    # Scale colours
    scale_colors = {
        "annual": C["annual"],
        "wet":    C["wet"],
        "dry":    C["dry"],
    }

    # Marker shapes for stations (up to 8)
    marker_list = ["o", "s", "^", "D", "v", "P", "X", "h"]
    use_shapes  = len(stns) <= 8

    # Comparison pairs: (y_method_key, y_label)
    comparisons = [
        ("Modified MK (H&R98)", "MMK Z"),
        ("PW-MK",               "PW-MK Z"),
        ("TFPW-MK",             "TFPW-MK Z"),
    ]
    panel_labels = ["(a)", "(b)", "(c)"]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Precompute Standard MK pivot: (station, scale) → Z
    mk_sub = df[df["Method"] == "Standard MK"].copy()
    mk_pivot = {}
    for _, row in mk_sub.iterrows():
        stn   = row.get("Station", None)
        scale = row.get("Scale",   None)
        z_val = row.get("Z",       np.nan)
        if stn is not None and scale is not None:
            mk_pivot[(stn, scale)] = float(z_val) if pd.notna(z_val) else np.nan

    for ax_idx, ((method_key, y_label), panel_lbl) in enumerate(
            zip(comparisons, panel_labels)):

        ax = axes[ax_idx]
        alt_sub = df[df["Method"] == method_key].copy()

        all_xs, all_ys = [], []

        for _, row in alt_sub.iterrows():
            stn   = row.get("Station", None)
            scale = row.get("Scale",   None)
            z_alt = row.get("Z",       np.nan)
            z_mk  = mk_pivot.get((stn, scale), np.nan)

            if not (pd.notna(z_alt) and pd.notna(z_mk)):
                continue

            z_alt_f = float(z_alt)
            z_mk_f  = float(z_mk)

            color  = scale_colors.get(scale, C["grey"])
            if use_shapes:
                s_idx  = stns.index(stn) if stn in stns else 0
                marker = marker_list[s_idx % len(marker_list)]
            else:
                marker = "o"

            ax.scatter(z_mk_f, z_alt_f,
                       s=60, color=color, marker=marker,
                       edgecolors="k", linewidths=0.4, alpha=0.85,
                       zorder=3)
            all_xs.append(z_mk_f)
            all_ys.append(z_alt_f)

        if all_xs:
            # Axis limits
            lim_lo = min(min(all_xs), min(all_ys)) - 0.5
            lim_hi = max(max(all_xs), max(all_ys)) + 0.5
        else:
            lim_lo, lim_hi = -4.0, 4.0

        # Identity line y = x
        lim_range = [lim_lo, lim_hi]
        ax.plot(lim_range, lim_range, color="black", lw=1.2,
                ls="--", zorder=2, label="y = x")

        # Significance threshold lines
        for z_thr in [-Z_005, Z_005]:
            ax.axvline(z_thr, color="#FF8F00", lw=0.9, ls="--", alpha=0.7,
                       zorder=1)
            ax.axhline(z_thr, color="#FF8F00", lw=0.9, ls="--", alpha=0.7,
                       zorder=1)

        ax.set_xlim(lim_lo, lim_hi)
        ax.set_ylim(lim_lo, lim_hi)
        ax.set_xlabel("Standard MK  Z", fontsize=11)
        ax.set_ylabel(y_label, fontsize=11)
        ax.set_title(f"{panel_lbl} {y_label} vs Standard MK Z",
                     fontsize=12, pad=7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # ── Legend ─────────────────────────────────────────────────────────
        legend_handles = []

        # Scale colour patches
        for sk, sc in scale_colors.items():
            lbl = _SCALE_LABELS.get(sk, sk.capitalize())
            legend_handles.append(
                mpatches.Patch(color=sc, label=lbl))

        # Station markers (only if using shapes)
        if use_shapes:
            for s_idx, stn in enumerate(stns):
                mk = marker_list[s_idx % len(marker_list)]
                legend_handles.append(
                    Line2D([0], [0], marker=mk, color="w",
                           markerfacecolor=C["grey"],
                           markeredgecolor="k", markersize=7,
                           label=smap.get(stn, stn)))

        # Identity and threshold line entries
        legend_handles.append(
            Line2D([0], [0], color="black", lw=1.2, ls="--",
                   label="y = x"))
        legend_handles.append(
            Line2D([0], [0], color="#FF8F00", lw=0.9, ls="--",
                   label=f"±{Z_005:.2f} (α=0.05)"))

        ax.legend(handles=legend_handles, fontsize=7.5,
                  loc="upper left", framealpha=0.8,
                  handletextpad=0.4, borderpad=0.5, ncol=1)

    fig.suptitle(
        f"Method Comparison — Z-Statistic Scatter  |  {period}",
        fontsize=13, y=1.02)

    fig.tight_layout(rect=[0, 0, 1, 1])
    savefig(fig, f"{out_dir}/{prefix}_Fig11_MethodComparison")
