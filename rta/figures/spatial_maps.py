"""
rta.figures.spatial_maps — Geographic/index scatter maps of Sen's slope trends.

fig14_spatial_maps(trend_df, stns, smap, coords, period, out_dir, prefix)
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


# ── Constants ─────────────────────────────────────────────────────────────────
_SCALE_ORDER = ["annual", "wet", "dry"]
_PANEL_LABELS = {
    "annual": "(a)",
    "wet":    "(b)",
    "dry":    "(c)",
}
_SCALE_LONG = {
    "annual": "Annual",
    "wet":    "Wet Season",
    "dry":    "Dry Season",
}

# Method key used for spatial map (Modified MK)
_MMK_KEY = "Modified MK (H&R98)"


def _bubble_size(slope_abs: float, max_slope: float,
                 s_min: float = 50.0, s_range: float = 200.0) -> float:
    """Scale bubble area proportional to |Sen's slope|."""
    if max_slope <= 0:
        return s_min
    return s_min + s_range * float(slope_abs) / float(max_slope)


def _trend_color(sig05: bool, z_val: float) -> str:
    """Return fill colour based on direction and significance."""
    if bool(sig05) and float(z_val) > 0:
        return C["inc"]
    if bool(sig05) and float(z_val) < 0:
        return C["dec"]
    return C["ns_col"]


def fig14_spatial_maps(trend_df: pd.DataFrame,
                        stns: list,
                        smap: dict,
                        coords: dict | None,
                        period: str,
                        out_dir: str,
                        prefix: str) -> None:
    """
    Fig 14 — Spatial (or index-axis) bubble maps of Modified MK Sen's slope.

    One panel per temporal scale (Annual / Wet Season / Dry Season).
    Bubble size is proportional to |Sen's slope|; colour indicates direction
    and significance.

    Parameters
    ----------
    trend_df : pd.DataFrame
        Long-form results with columns:
        Station, Scale, Method, Z, sig_05, sig_01, slope_Q
    stns     : list
        Ordered station names.
    smap     : dict
        {station_name: short_code} for point labels.
    coords   : dict | None
        {station_name: (lat, lon)}.  If None, station index is used as x-axis.
    period   : str
        Study period label (e.g. "1981–2014").
    out_dir  : str
        Output directory.
    prefix   : str
        Filename prefix.
    """
    df = trend_df.copy()
    if "Scale" in df.columns:
        df["Scale"] = df["Scale"].str.lower().str.strip()
    if "Method" in df.columns:
        df["Method"] = df["Method"].str.strip()

    use_coords = coords is not None and len(coords) > 0

    # Filter to Modified MK only
    mmk_df = df[df["Method"] == _MMK_KEY].copy()

    # ── Pre-compute global max |slope| for consistent bubble scaling ─────────
    slope_vals = pd.to_numeric(mmk_df.get("slope_Q", pd.Series(dtype=float)),
                               errors="coerce").dropna().abs()
    global_max_slope = float(slope_vals.max()) if len(slope_vals) > 0 else 1.0
    if global_max_slope == 0:
        global_max_slope = 1.0

    # ── Figure ────────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(18, 7))

    for col_idx, scale_key in enumerate(_SCALE_ORDER):
        ax = axes[col_idx]
        panel_lbl  = _PANEL_LABELS[scale_key]
        scale_long = _SCALE_LONG[scale_key]
        meta       = SCALE_META[scale_key]

        # Slice this scale
        scale_sub = mmk_df[mmk_df["Scale"] == scale_key]

        xs, ys, sizes, colors, labels_plot = [], [], [], [], []

        for s_idx, stn in enumerate(stns):
            stn_row = scale_sub[scale_sub["Station"] == stn]
            if len(stn_row) == 0:
                continue
            stn_row = stn_row.iloc[0]

            slope_q = pd.to_numeric(stn_row.get("slope_Q", np.nan),
                                    errors="coerce")
            z_val   = pd.to_numeric(stn_row.get("Z",       np.nan),
                                    errors="coerce")
            sig05   = bool(stn_row.get("sig_05", False))

            slope_abs = float(abs(slope_q)) if pd.notna(slope_q) else 0.0
            z_f       = float(z_val)        if pd.notna(z_val)   else 0.0

            if use_coords and stn in coords:
                lat, lon = coords[stn]
                x_val, y_val = float(lon), float(lat)
            else:
                x_val = float(s_idx)
                y_val = 0.0

            size  = _bubble_size(slope_abs, global_max_slope)
            color = _trend_color(sig05, z_f)
            label = smap.get(stn, stn)

            xs.append(x_val)
            ys.append(y_val)
            sizes.append(size)
            colors.append(color)
            labels_plot.append(label)

        if xs:
            sc = ax.scatter(
                xs, ys, s=sizes, c=colors,
                edgecolors="black", linewidths=0.7,
                zorder=4, alpha=0.88)

            # Station labels
            for xi, yi, lbl in zip(xs, ys, labels_plot):
                ax.annotate(
                    lbl,
                    xy=(xi, yi),
                    xytext=(4, 5),
                    textcoords="offset points",
                    fontsize=8.5,
                    color="#212121",
                    zorder=5,
                )

        # ── Axes labels & cosmetics ───────────────────────────────────────
        if use_coords:
            ax.set_xlabel("Longitude (°E)", fontsize=11)
            ax.set_ylabel("Latitude (°N)",  fontsize=11)

            # Compass annotation "N↑" in upper right
            ax.annotate(
                "N↑",
                xy=(0.95, 0.93), xycoords="axes fraction",
                fontsize=12, ha="right", va="top",
                fontweight="bold", color="#212121",
                bbox=dict(boxstyle="round,pad=0.2", fc="white",
                          ec="#BDBDBD", lw=0.7))

            # Add a bit of padding around the data extent
            if xs:
                x_pad = max((max(xs) - min(xs)) * 0.08, 0.05)
                y_pad = max((max(ys) - min(ys)) * 0.08, 0.05)
                ax.set_xlim(min(xs) - x_pad, max(xs) + x_pad)
                ax.set_ylim(min(ys) - y_pad, max(ys) + y_pad)
        else:
            ax.set_xlabel("Station Index", fontsize=11)
            ax.set_ylabel("",              fontsize=11)
            if xs:
                ax.set_xlim(-0.8, len(stns) - 0.2)
                ax.set_ylim(-1.0, 1.0)
                ax.set_yticks([])
            # Label x-axis ticks with short station names
            tick_xs   = list(range(len(stns)))
            tick_lbls = [smap.get(s, s) for s in stns]
            ax.set_xticks(tick_xs)
            ax.set_xticklabels(tick_lbls, rotation=45, ha="right", fontsize=9)

        ax.set_title(
            f"{panel_lbl} {scale_long} — Sen's Slope (MMK)\n{period}",
            fontsize=11, pad=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.35,
                color="#B0BEC5")

        # ── Trend-direction legend ────────────────────────────────────────
        legend_handles = [
            mpatches.Patch(facecolor=C["inc"],    edgecolor="k",
                           linewidth=0.7, label="Increasing (sig.)"),
            mpatches.Patch(facecolor=C["dec"],    edgecolor="k",
                           linewidth=0.7, label="Decreasing (sig.)"),
            mpatches.Patch(facecolor=C["ns_col"], edgecolor="k",
                           linewidth=0.7, label="Not significant"),
        ]

        # ── Reference size legend ─────────────────────────────────────────
        # Show three reference bubble sizes: 25 %, 50 %, 100 % of max slope
        ref_fracs  = [0.25, 0.50, 1.00]
        ref_slopes = [f * global_max_slope for f in ref_fracs]
        for rf, rs in zip(ref_fracs, ref_slopes):
            size_pt = _bubble_size(rs, global_max_slope)
            legend_handles.append(
                Line2D([0], [0], marker="o", color="w",
                       markerfacecolor=C["grey"],
                       markeredgecolor="k",
                       markersize=math.sqrt(size_pt / math.pi),
                       label=f"|slope| = {rs:.1f} {meta['unit']}"))

        ax.legend(handles=legend_handles,
                  fontsize=7.5, loc="lower right",
                  framealpha=0.85, handletextpad=0.4,
                  borderpad=0.5)

    fig.suptitle(
        f"Spatial Distribution of Rainfall Trends (Modified MK)  |  {period}",
        fontsize=13, y=1.02)

    fig.tight_layout(rect=[0, 0, 1, 1])
    savefig(fig, f"{out_dir}/{prefix}_Fig14_SpatialMaps")
