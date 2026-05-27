"""
rta_v5.spatial_layout_v5 — Figure layout constants, color palette, font
setup, and cartographic decoration helpers for Q1 spatial maps.

All layout parameters live here so any figure change requires editing
only this file.
"""

from __future__ import annotations

import numpy as np
import matplotlib
import matplotlib.font_manager as fm

# ── Font ──────────────────────────────────────────────────────────────────────
_tnr_avail = any("Times New Roman" in f.name for f in fm.fontManager.ttflist)
FONT_SERIF  = "Times New Roman" if _tnr_avail else "DejaVu Serif"

def setup_fonts() -> None:
    """Apply consistent font settings to rcParams."""
    matplotlib.rcParams.update({
        "font.family":        "serif",
        "font.serif":         [FONT_SERIF, "DejaVu Serif"],
        "axes.titlesize":     8,
        "axes.labelsize":     6.5,
        "xtick.labelsize":    5.5,
        "ytick.labelsize":    5.5,
        "font.size":          7,
    })


# ── Colors ────────────────────────────────────────────────────────────────────
C_INC = "#1B5E20"   # significant increasing — dark green
C_DEC = "#B71C1C"   # significant decreasing — dark red
C_NS  = "#78909C"   # not significant        — grey

# ── Colormap bounds ───────────────────────────────────────────────────────────
Z_VABS = 2.6        # Z colormap saturation  (≈ Z_0.01 = 2.576)


# ── Layout specification ──────────────────────────────────────────────────────
#
# Figure: 11 × 13 inches
# Maps:   3-row × 4-col gridspec
#           Row 0: (a) cols 0:2,  (b) cols 2:4
#           Row 1: (c) cols 0:2,  (d) cols 2:4
#           Row 2: (e) cols 1:3   ← exactly centred
# Cbars:  1-row × 2-col gridspec below maps
#           Left:  Z colorbar  (equal width = half figure)
#           Right: Slope cbar  (equal width = half figure)
#
LAYOUT = {
    "fig_w":     11.0,      # inches
    "fig_h":     13.0,      # inches
    "dpi":       600,
    # Map gridspec
    "map_left":  0.062,
    "map_right": 0.972,
    "map_top":   0.960,
    "map_bottom":0.130,
    "hspace":    0.155,
    "wspace":    0.090,
    # Colorbar gridspec
    "cb_left":   0.075,
    "cb_right":  0.955,
    "cb_top":    0.100,
    "cb_bottom": 0.038,
    "cb_wspace": 0.24,
    # Station marker
    "stn_size":  60,
    # Province outline
    "poly_lw":   0.70,
    "poly_color":"#222222",
}

# Canvas efficiency (informational, enforced by layout values above):
# Maps:  (map_top - map_bottom) × fig_h = 10.8 in = 83 % of 13 in
# After removing hspace gaps ≈ 86 % effective


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Gridspec builder                                                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def build_axes(fig):
    """
    Build the 5-panel map axes + 2 colorbar axes using two GridSpecs.

    Returns
    -------
    ax_a, ax_b, ax_c, ax_d, ax_e : map axes
    ax_cz, ax_cs                  : colorbar axes (Z, slope)
    """
    from matplotlib.gridspec import GridSpec

    L = LAYOUT

    # 3-row × 4-col map grid
    gs_m = GridSpec(
        3, 4,
        left=L["map_left"], right=L["map_right"],
        top=L["map_top"],   bottom=L["map_bottom"],
        hspace=L["hspace"], wspace=L["wspace"],
        figure=fig,
    )
    ax_a = fig.add_subplot(gs_m[0, 0:2])
    ax_b = fig.add_subplot(gs_m[0, 2:4])
    ax_c = fig.add_subplot(gs_m[1, 0:2])
    ax_d = fig.add_subplot(gs_m[1, 2:4])
    ax_e = fig.add_subplot(gs_m[2, 1:3])   # centred: cols 1–2 of 4

    # 1-row × 2-col colorbar grid
    gs_c = GridSpec(
        1, 2,
        left=L["cb_left"], right=L["cb_right"],
        top=L["cb_top"],   bottom=L["cb_bottom"],
        wspace=L["cb_wspace"],
        figure=fig,
    )
    ax_cz = fig.add_subplot(gs_c[0, 0])   # Z colorbar (left = equal width)
    ax_cs = fig.add_subplot(gs_c[0, 1])   # slope colorbar (right = equal width)

    return ax_a, ax_b, ax_c, ax_d, ax_e, ax_cz, ax_cs


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Cartographic decorations                                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def north_arrow(ax, x: float = 0.91, y: float = 0.86,
                length: float = 0.09, fontsize: float = 6.5) -> None:
    """Simple north arrow at axes-fraction coordinates (x, y)."""
    ax.annotate(
        "", xy=(x, y + length), xytext=(x, y),
        xycoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color="#111111",
                        lw=0.9, mutation_scale=8),
    )
    ax.text(x, y + length + 0.028, "N",
            transform=ax.transAxes, ha="center", va="bottom",
            fontsize=fontsize, fontweight="bold", color="#111111",
            fontfamily=FONT_SERIF, zorder=10)


def scale_bar(ax, xmin: float, xmax: float,
              ymin: float, ymax: float, km: int = 25) -> None:
    """Horizontal scale bar in lower-left map corner (geographic coords)."""
    lat_c       = (ymin + ymax) / 2.0
    dlon_per_km = 1.0 / (111.32 * np.cos(np.radians(lat_c)))
    bar_lon     = km * dlon_per_km
    x0 = xmin + 0.062 * (xmax - xmin)
    y0 = ymin + 0.042 * (ymax - ymin)
    x1 = x0 + bar_lon
    dy = 0.009 * (ymax - ymin)
    kw = dict(color="#111111", zorder=9)
    ax.plot([x0, x1], [y0, y0], lw=2.0, solid_capstyle="butt", **kw)
    for xx in (x0, x1):
        ax.plot([xx, xx], [y0 - dy, y0 + dy], lw=1.2, **kw)
    ax.text((x0 + x1) / 2, y0 + 1.9 * dy,
            f"{km} km", ha="center", va="bottom",
            fontsize=5.5, color="#111111", zorder=9)


def panel_letter(ax, letter: str, fontsize: float = 10.0) -> None:
    """Bold panel letter in top-left corner with white backing."""
    ax.text(0.022, 0.978, letter,
            transform=ax.transAxes, ha="left", va="top",
            fontsize=fontsize, fontweight="bold", color="#111111",
            fontfamily=FONT_SERIF, zorder=11,
            bbox=dict(boxstyle="round,pad=0.14", fc="white",
                      ec="none", alpha=0.82))


def format_map_axes(ax, xmin: float, xmax: float,
                    ymin: float, ymax: float) -> None:
    """Apply consistent tick formatting to a map axes."""
    lon_ticks = np.arange(np.ceil(xmin  / 0.5) * 0.5, xmax + 0.001, 0.5)
    lat_ticks = np.arange(np.ceil(ymin  / 0.5) * 0.5, ymax + 0.001, 0.5)
    ax.set_xticks(lon_ticks)
    ax.set_yticks(lat_ticks)
    ax.set_xticklabels([f"{v:.1f}°E" for v in lon_ticks])
    ax.set_yticklabels([f"{v:.1f}°N" for v in lat_ticks])
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.tick_params(width=0.5, length=2, pad=1.5)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_linewidth(0.5)
    ax.set_facecolor("white")
