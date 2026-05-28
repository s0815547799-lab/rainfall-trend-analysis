"""
rta_v5.spatial_layout_v5 — Figure layout constants, color palette, font
setup, and cartographic decoration helpers for Q1 spatial maps.

v5.4 refinements (in-place):
  • 2×3 GridSpec — tighter wspace/hspace, reduced outer margins
  • Inset colorbar raised + reduced (clear of x-axis label zone)
  • Colorbar label placed above bar; tick fontsize reduced
  • Row-figure bottom margin reduced (footnotes removed)
  • North arrow reduced ~15%; linewidth reduced
  • Station triangle size factor + alpha exposed as LAYOUT constants
  • Raster rendering upgraded to bicubic (smoother appearance)

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


# ── Colors — hydrological/climatological convention ──────────────────────────
C_INC = "#1B7837"   # significant increasing — dark green  (hydro convention)
C_DEC = "#B2182B"   # significant decreasing — dark red    (hydro convention)
C_NS  = "#78909C"   # not significant        — grey        (neutral)

# ── Colormap bounds ───────────────────────────────────────────────────────────
Z_VABS = 2.6        # Z colormap saturation  (≈ Z_0.01 = 2.576)


# ── Layout specification ──────────────────────────────────────────────────────
#
# 5-panel figure: 8.8 × 10.8 inches (constrained_layout=False)
# Maps:   3-row × 4-col GridSpec — locked publication geometry
#           Row 0: (a) cols 0:2,  (b) cols 2:4
#           Row 1: (c) cols 0:2,  (d) cols 2:4
#           Row 2: (e) cols 1:3   ← centred
# GridSpec: left=0.045 right=0.985 top=0.955 bottom=0.055
#           wspace=0.08 hspace=0.16
# Row figures: 15.5 × 4.8 inches
#   left=0.03 right=0.992 top=0.90 bottom=0.09 wspace=0.06
#
LAYOUT = {
    # 5-panel publication figure — locked geometry
    "fig_w":     8.8,
    "fig_h":    10.8,
    # Comparison figure (2 panels side-by-side)
    "cmp_fig_w": 10.0,
    "cmp_fig_h":  8.5,
    # Single-method figure (1 panel)
    "sgl_fig_w":  4.5,
    "sgl_fig_h":  8.0,
    # Row figures — locked geometry (both 4-method and Sen rows)
    "row4_fig_w":    15.5,
    "row4_fig_h":     4.8,
    "row_sens_fig_w": 15.5,
    "row_sens_fig_h":  4.8,
    "dpi":       600,
    # Station markers
    "stn_size":   75,      # base size (scatter s= units)
    "tri_factor": 0.87,    # significant triangle  = stn_size × tri_factor
    "tri_alpha":  0.88,    # significant triangle alpha (softens vs raster)
    # NS circle uses stn_size × 0.50 (defined inline in _draw_panel)
    # Province outline
    "poly_lw":   0.70,
    "poly_color":"#222222",
    # Inset colorbar geometry (per-panel, axes-fraction coords)
    # cbar_y0 raised to clear x-axis label zone; cbar_h reduced ~19%
    "cbar_x0":   0.680,
    "cbar_y0":   0.065,    # raised from 0.022 → clear of x-axis labels
    "cbar_w":    0.295,
    "cbar_h":    0.050,    # reduced from 0.062 (~19%)
}


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Gridspec builder                                                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def build_axes(fig):
    """
    6-axes publication layout — 2×3 GridSpec (8.8 × 10.8 in).

    Grid layout:
        Row 0:  (a) col 0  |  (b) col 1  |  (c) col 2
        Row 1:  (d) col 0  |  (e) col 1  |  [legend] col 2

    GridSpec: left=0.030 right=0.995 top=0.940 bottom=0.030
              wspace=0.05  hspace=0.10

    Panel dimensions (approx.):
        width  ≈ 2.72 in  (figure fraction 0.3093)
        height ≈ 4.59 in  (figure fraction 0.4250)
        aspect ≈ 1.687  ≈ province H/W (1.698) → ~99% fill

    Returns
    -------
    ax_a, ax_b, ax_c, ax_d, ax_e, ax_leg
    """
    from matplotlib.gridspec import GridSpec

    gs = GridSpec(
        2, 3, figure=fig,
        height_ratios=[1, 1],
        hspace=0.10, wspace=0.05,
        left=0.030, right=0.995,
        top=0.940, bottom=0.030,
    )
    ax_a   = fig.add_subplot(gs[0, 0])   # (a) Standard MK
    ax_b   = fig.add_subplot(gs[0, 1])   # (b) Modified MK
    ax_c   = fig.add_subplot(gs[0, 2])   # (c) PW-MK
    ax_d   = fig.add_subplot(gs[1, 0])   # (d) TFPW-MK
    ax_e   = fig.add_subplot(gs[1, 1])   # (e) Sen's Slope
    ax_leg = fig.add_subplot(gs[1, 2])   # legend / metadata

    return ax_a, ax_b, ax_c, ax_d, ax_e, ax_leg


def build_axes_compare(fig):
    """
    1-row × 2-col layout for side-by-side method comparison figures.

    Returns
    -------
    ax_a, ax_b : left and right map axes
    """
    from matplotlib.gridspec import GridSpec
    gs = GridSpec(1, 2, figure=fig)
    return fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])


def build_axes_single(fig):
    """
    Single-panel layout for standalone method figures.

    Returns
    -------
    ax : the single map axes
    """
    from matplotlib.gridspec import GridSpec
    gs = GridSpec(1, 1, figure=fig)
    return fig.add_subplot(gs[0, 0])


def build_row_layout(fig, n_cols: int) -> list:
    """
    1×n_cols row of map axes — locked row-figure geometry (15.5 × 4.8 in).

    GridSpec: left=0.030 right=0.992 top=0.900 bottom=0.065 wspace=0.06

    bottom reduced from 0.090 → 0.065 now that footer metadata is removed.

    Parameters
    ----------
    fig    : figure created by the caller (constrained_layout=False)
    n_cols : number of map panels (columns)

    Returns
    -------
    list of n_cols map axes, left to right
    """
    from matplotlib.gridspec import GridSpec
    gs = GridSpec(
        1, n_cols, figure=fig,
        left=0.030, right=0.992,
        top=0.900, bottom=0.065,
        wspace=0.06,
    )
    return [fig.add_subplot(gs[0, i]) for i in range(n_cols)]


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Cartographic decorations                                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def north_arrow(ax, x: float = 0.91, y: float = 0.86,
                length: float = 0.077, fontsize: float = 6.5) -> None:
    """Simple north arrow at axes-fraction coordinates (x, y)."""
    ax.annotate(
        "", xy=(x, y + length), xytext=(x, y),
        xycoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color="#111111",
                        lw=0.75, mutation_scale=8),
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
    """Apply consistent tick formatting and geographic aspect to a map axes."""
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
    # Province-shape-aware aspect: 1 km east = 1 km north
    lat_c = (ymin + ymax) / 2.0
    ax.set_aspect(1.0 / np.cos(np.radians(lat_c)))
