"""
rta.figures.taylor — Taylor diagram comparing station annual series to regional mean.

fig9_taylor_diagram(scales, stns, smap, period, out_dir, prefix)
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


# ── Internal helpers ──────────────────────────────────────────────────────────

def _taylor_coords(r: float, sigma_ratio: float):
    """Convert (r, sigma_ratio) to Cartesian Taylor coordinates."""
    theta = math.acos(max(-1.0, min(1.0, r)))
    x = sigma_ratio * math.cos(theta)
    y = sigma_ratio * math.sin(theta)
    return x, y


def _draw_rmsd_arcs(ax, rmsd_values, sigma_ref=1.0, color="#9E9E9E",
                    lw=0.9, ls="--"):
    """Draw RMSD contour arcs centred at (sigma_ref, 0)."""
    theta = np.linspace(0, np.pi, 360)
    for rmsd in rmsd_values:
        r_arc = rmsd / sigma_ref if sigma_ref > 0 else rmsd
        xs = sigma_ref + r_arc * np.cos(theta)
        ys = r_arc * np.sin(theta)
        # keep only the upper half and xs >= 0
        mask = ys >= 0
        ax.plot(xs[mask], ys[mask], color=color, lw=lw, ls=ls, zorder=1)
        # label at the arc's rightmost visible point
        label_idx = np.argmax(xs[mask]) if mask.sum() > 0 else 0
        lx = xs[mask][label_idx]
        ly = ys[mask][label_idx]
        ax.text(lx + 0.03, ly + 0.03, f"RMSD={rmsd:.1f}",
                fontsize=8, color=color, va="bottom", ha="left")


def _draw_correlation_gridlines(ax, r_values, r_max, color="#BDBDBD",
                                 lw=0.7, ls=":"):
    """Draw radial gridlines for given correlation values."""
    for r in r_values:
        theta = math.acos(max(-1.0, min(1.0, r)))
        ax.plot([0, r_max * math.cos(theta)],
                [0, r_max * math.sin(theta)],
                color=color, lw=lw, ls=ls, zorder=1)
        lx = (r_max + 0.07) * math.cos(theta)
        ly = (r_max + 0.07) * math.sin(theta)
        ax.text(lx, ly, f"r={r}", fontsize=8, color="#616161",
                ha="center", va="center")


# ── Public figure function ────────────────────────────────────────────────────

def fig9_taylor_diagram(scales: dict, stns: list, smap: dict,
                         period: str, out_dir: str, prefix: str) -> None:
    """
    Fig 9 — Taylor diagram comparing each station's annual rainfall series to
    the regional mean, one panel per temporal scale (Annual / Wet / Dry).

    Parameters
    ----------
    scales   : dict    Output of aggregate_all(); keys "annual", "wet", "dry".
    stns     : list    Station names (column names in scales DataFrames).
    smap     : dict    {station_name: short_code} for point labels.
    period   : str     Study period label (e.g. "1981–2014").
    out_dir  : str     Output directory (no trailing slash needed).
    prefix   : str     Filename prefix.
    """
    scale_keys = ["annual", "wet", "dry"]
    panel_labels = ["(a)", "(b)", "(c)"]

    fig, axes = plt.subplots(1, 3, figsize=(18, 7))

    cmap = cm.get_cmap("tab10", max(len(stns), 1))

    for col_idx, (scale_key, panel_lbl) in enumerate(
            zip(scale_keys, panel_labels)):

        ax = axes[col_idx]
        df_scale = scales[scale_key]   # DataFrame: rows=years, cols=stations

        # ── Regional reference (mean across all stations) ──────────────────
        valid_cols = [s for s in stns if s in df_scale.columns]
        if not valid_cols:
            ax.set_visible(False)
            continue

        ref_series = df_scale[valid_cols].mean(axis=1)
        ref_vals   = ref_series.dropna().values.astype(float)
        if len(ref_vals) < 4:
            ax.set_visible(False)
            continue

        sigma_ref = float(np.std(ref_vals, ddof=1))
        if sigma_ref == 0:
            ax.set_visible(False)
            continue

        # ── Compute per-station Taylor statistics ──────────────────────────
        station_points = []   # list of (x, y, label, color_idx)
        for s_idx, stn in enumerate(stns):
            if stn not in df_scale.columns:
                continue
            stn_series = df_scale[stn].dropna()
            # align on common index
            common_idx = ref_series.dropna().index.intersection(
                stn_series.index)
            if len(common_idx) < 4:
                continue

            stn_vals = stn_series.loc[common_idx].values.astype(float)
            ref_vals_aligned = ref_series.loc[common_idx].values.astype(float)

            r = float(np.corrcoef(stn_vals, ref_vals_aligned)[0, 1])
            if not np.isfinite(r):
                continue

            sigma_stn = float(np.std(stn_vals, ddof=1))
            sigma_ratio = sigma_stn / sigma_ref if sigma_ref > 0 else np.nan
            if not np.isfinite(sigma_ratio):
                continue

            x, y = _taylor_coords(r, sigma_ratio)
            label = smap.get(stn, stn)
            station_points.append((x, y, label, s_idx))

        if not station_points:
            ax.set_visible(False)
            continue

        # ── Axis limits ────────────────────────────────────────────────────
        all_x = [pt[0] for pt in station_points] + [0.0, 1.0]
        all_y = [pt[1] for pt in station_points] + [0.0]
        x_max = max(1.6, max(all_x) + 0.3)
        y_max = max(1.6, max(all_y) + 0.3)
        r_max = max(x_max, y_max)

        # ── Background decorations ─────────────────────────────────────────
        # Standard deviation arcs centred at origin
        std_arc_vals = np.arange(0.5, r_max, 0.5)
        for sv in std_arc_vals:
            theta_arc = np.linspace(0, np.pi / 2, 200)
            ax.plot(sv * np.cos(theta_arc), sv * np.sin(theta_arc),
                    color="#E0E0E0", lw=0.6, ls="-", zorder=0)

        # RMSD arcs centred at reference (1, 0)
        _draw_rmsd_arcs(ax, [0.5, 1.0, 1.5], sigma_ref=1.0)

        # Correlation gridlines
        _draw_correlation_gridlines(ax, [0.90, 0.95, 0.99], r_max=r_max)

        # ── Reference point ────────────────────────────────────────────────
        ax.scatter([1.0], [0.0], marker="*", s=220, color=C["gold"],
                   edgecolors="k", linewidths=0.8, zorder=5,
                   label="Regional mean")

        # ── Station points ─────────────────────────────────────────────────
        for x, y, label, s_idx in station_points:
            color = cmap(s_idx % 10)
            ax.scatter(x, y, s=80, color=color,
                       edgecolors="k", linewidths=0.5, zorder=4)
            ax.text(x + 0.04, y + 0.04, label,
                    fontsize=8.5, color=color,
                    va="bottom", ha="left", zorder=5)

        # ── Legend for station colours ─────────────────────────────────────
        legend_handles = [
            Line2D([0], [0], marker="*", color="w", markerfacecolor=C["gold"],
                   markeredgecolor="k", markersize=10, label="Regional mean")
        ]
        for x, y, label, s_idx in station_points:
            legend_handles.append(
                Line2D([0], [0], marker="o", color="w",
                       markerfacecolor=cmap(s_idx % 10),
                       markeredgecolor="k", markersize=7, label=label)
            )
        ax.legend(handles=legend_handles, fontsize=7.5,
                  loc="upper right", framealpha=0.8,
                  handletextpad=0.4, borderpad=0.5)

        # ── Axis formatting ────────────────────────────────────────────────
        ax.set_xlim(0.0, x_max)
        ax.set_ylim(0.0, y_max)
        ax.set_xlabel("Normalised Standard Deviation", fontsize=11)
        ax.set_ylabel("Normalised Standard Deviation", fontsize=11)

        meta = SCALE_META[scale_key]
        ax.set_title(
            f"{panel_lbl} Taylor Diagram — {meta['label']}\n{period}",
            fontsize=12, pad=8)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.35,
                color="#B0BEC5")

    fig.suptitle(
        f"Taylor Diagram — Station vs Regional Mean  |  {period}",
        fontsize=13, y=1.02)

    fig.tight_layout(rect=[0, 0, 1, 1])
    savefig(fig, f"{out_dir}/{prefix}_Fig9_TaylorDiagram")
