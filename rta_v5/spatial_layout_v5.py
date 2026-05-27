"""
rta_v5.spatial_layout_v5 — Figure layout constants, color palette, font
setup, and cartographic decoration helpers for Q1 spatial maps.

v5.1 refinements (in-place):
  • constrained_layout — automatic tight spacing, no manual margin params
  • Per-panel inset colorbars replace shared global colorbar axes
  • build_axes() returns 5 map axes only (no colorbar axes)
  • Geographic aspect-aware figure scaling
  • Colorblind-safe station marker palette (Wong 2011)
  • build_axes_compare() — 1×2 panel for side-by-side method comparisons
  • build_axes_single()  — 1-panel for standalone method figures

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


# ── Colors — Wong (2011) colorblind-safe palette ─────────────────────────────
C_INC = "#0072B2"   # significant increasing — blue   (safe for CVD)
C_DEC = "#D55E00"   # significant decreasing — vermilion (safe for CVD)
C_NS  = "#78909C"   # not significant        — grey   (neutral)

# ── Colormap bounds ───────────────────────────────────────────────────────────
Z_VABS = 2.6        # Z colormap saturation  (≈ Z_0.01 = 2.576)


# ── Layout specification ──────────────────────────────────────────────────────
#
# 5-panel figure: 11 × 12.5 inches  (constrained_layout)
# Maps:   3-row × 4-col GridSpec
#           Row 0: (a) cols 0:2,  (b) cols 2:4
#           Row 1: (c) cols 0:2,  (d) cols 2:4
#           Row 2: (empty) cols 0:2, (e) cols 2:4  ← lower-right
# Comparison figure: 10 × 8.5 inches, 1-row × 2-col GridSpec
# Single-method figure: 5.5 × 8.5 inches, 1-row × 1-col GridSpec
# Colorbars: per-panel inset axes (lower-right of each panel)
#
LAYOUT = {
    # 5-panel figure
    "fig_w":     11.0,      # inches
    "fig_h":     12.5,      # inches
    # Comparison figure (2 panels side-by-side)
    "cmp_fig_w": 10.0,
    "cmp_fig_h": 8.5,
    # Single-method figure (1 panel)
    "sgl_fig_w": 5.5,
    "sgl_fig_h": 8.5,
    "dpi":       600,
    # Station marker
    "stn_size":  60,
    # Province outline
    "poly_lw":   0.70,
    "poly_color":"#222222",
    # Inset colorbar geometry  (axes-fraction units for ax.inset_axes)
    "cbar_x0":   0.695,     # left edge
    "cbar_y0":   0.030,     # bottom edge
    "cbar_w":    0.275,     # width
    "cbar_h":    0.056,     # height
}


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Gridspec builder                                                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def build_axes(fig):
    """
    Build the 5-panel map axes using a constrained-layout GridSpec.

    The figure must be created with constrained_layout=True.
    Per-panel inset colorbars are added by the caller via ax.inset_axes().

    Returns
    -------
    ax_a, ax_b, ax_c, ax_d, ax_e : map axes (no colorbar axes)
    """
    from matplotlib.gridspec import GridSpec

    # No explicit left/right/top/bottom — constrained_layout handles spacing.
    # Row 2 is 5 % taller so panel (e) is slightly enlarged when centred.
    gs = GridSpec(3, 4, figure=fig, height_ratios=[1, 1, 1.05])
    ax_a = fig.add_subplot(gs[0, 0:2])
    ax_b = fig.add_subplot(gs[0, 2:4])
    ax_c = fig.add_subplot(gs[1, 0:2])
    ax_d = fig.add_subplot(gs[1, 2:4])
    ax_e = fig.add_subplot(gs[2, 2:4])   # lower-right: cols 2–3 of 4

    return ax_a, ax_b, ax_c, ax_d, ax_e


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
