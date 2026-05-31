"""
figures.base — publication figure utilities (Q1 journal standard).

Requirement 1: every figure is rendered in BOTH single-column and double-column
widths (and in all configured formats: PNG/TIFF/PDF, 600 dpi). No main title,
no footnote; panels use (a)(b)(c).

Requirement 2: GIS maps use auto-scaling colour range (robust 2–98 percentile,
zero-centred for change maps) and auto-label placement (free-corner search) so
nothing overlaps when the study area changes.

Typography: serif font (Times New Roman or Liberation Serif) per most Q1
hydrology journals (J. Hydrol., Water Resour. Res., HESS, etc.).
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

log = logging.getLogger(__name__)

# ── Typography — prefer serif fonts used by Q1 hydrology journals ─────────────
_SERIF_PREFS = (
    "Times New Roman", "Liberation Serif", "DejaVu Serif",
    "Georgia", "FreeSerif",
)
_available = {f.name for f in font_manager.fontManager.ttflist}
_chosen = next((f for f in _SERIF_PREFS if f in _available), "DejaVu Serif")

plt.rcParams.update({
    # Font
    "font.family":        "serif",
    "font.serif":         [_chosen],
    "font.size":          9,
    "axes.titlesize":     9,
    "axes.labelsize":     9,
    "xtick.labelsize":    8,
    "ytick.labelsize":    8,
    "legend.fontsize":    8,
    "legend.framealpha":  0.85,
    # Axes
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.linewidth":     0.8,
    "axes.grid":          True,
    "grid.linestyle":     "--",
    "grid.linewidth":     0.4,
    "grid.alpha":         0.45,
    # Lines / markers
    "lines.linewidth":    1.2,
    "lines.markersize":   4,
    # Output
    "savefig.dpi":        600,
    "savefig.bbox":       "tight",
    "savefig.pad_inches": 0.05,
    "pdf.fonttype":       42,   # embed fonts in PDF (required by many journals)
    "ps.fonttype":        42,
})

log.debug("Publication font selected: %s", _chosen)


# ── Panel labels ─────────────────────────────────────────────────────────────

def panel_tag(ax, tag: str, loc: tuple[float, float] = (0.02, 0.96)):
    """Lightweight panel label used in simple subplots."""
    ax.text(*loc, f"({tag})", transform=ax.transAxes, fontweight="bold",
            va="top", ha="left", fontsize=10,
            bbox=dict(boxstyle="round,pad=0.20", fc="white", ec="none", alpha=0.85))


PANEL_LABEL = {"x": 0.03, "y": 0.97, "fontsize": 10, "fontweight": "bold"}


def add_panel_label(ax, tag: str, subtitle: str | None = None):
    """Project-wide standard: (a) [subtitle] — identical offset/size everywhere."""
    txt = f"({tag})" + (f" {subtitle}" if subtitle else "")
    ax.text(PANEL_LABEL["x"], PANEL_LABEL["y"], txt,
            transform=ax.transAxes,
            ha="left", va="top",
            fontsize=PANEL_LABEL["fontsize"],
            fontweight=PANEL_LABEL["fontweight"],
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.85))


# ── Save helper ───────────────────────────────────────────────────────────────

def save_dual(fig_builder, fid: str, cfg: dict) -> list[Path]:
    """Build + save a figure at BOTH single and double column widths × all formats.

    fig_builder(width_in) -> matplotlib Figure (caller sets content; no suptitle).
    Returns a list of Path objects for every file written.
    """
    out = Path(cfg["paths"]["outputs"]) / "figures"
    out.mkdir(parents=True, exist_ok=True)
    widths = {
        "single": cfg["figures"]["single_col_in"],
        "double": cfg["figures"]["double_col_in"],
    }
    dpi  = cfg["figures"]["dpi"]
    fmts = cfg["figures"]["formats"]
    saved: list[Path] = []
    for col, w in widths.items():
        fig = fig_builder(w)
        for fmt in fmts:
            p = out / f"{fid}_{col}.{fmt}"
            fig.savefig(p, dpi=dpi, bbox_inches="tight", pad_inches=0.05)
            saved.append(p)
        plt.close(fig)
    log.info("saved %s: %d files (single+double × %d formats)",
             fid, len(saved), len(fmts))
    return saved


# ── Auto colour range ─────────────────────────────────────────────────────────

def auto_color_range(values, diverging: bool = False) -> tuple[float, float]:
    """Robust colour limits (2–98 pct).  Zero-centred when diverging=True."""
    v = np.asarray(values, float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return (-1.0, 1.0) if diverging else (0.0, 1.0)
    lo, hi = np.percentile(v, [2, 98])
    if diverging:
        m = max(abs(lo), abs(hi)) or 1.0
        return (-m, m)
    return (float(lo), float(hi))


# ── Free-corner placement (geographic convention) ─────────────────────────────

def free_corner(mask: np.ndarray, bounds: tuple[float, float, float, float],
                margin: float = 0.12) -> tuple[tuple, tuple, str]:
    """Return (north_xy, scale_xy, scale_corner) in the least-dense map corners.

    mask is a 2-D boolean array in **image** coordinates (row 0 = geographic
    NORTH, row -1 = geographic SOUTH), as produced by gis.interp.surface().

    Quadrant mapping (image → geographic):
        image rows   0..hy  → geographic NORTH half  → label "u" (upper)
        image rows  hy..-1  → geographic SOUTH half  → label "l" (lower)
        image cols   0..hx  → geographic WEST  half  → label "l" (left)
        image cols  hx..-1  → geographic EAST  half  → label "r" (right)
    """
    ny, nx = mask.shape
    hy, hx = ny // 2, nx // 2

    # Density = fraction of grid cells inside the study-area boundary
    # Lower density → emptier corner → better placement
    dens = {
        "ul": mask[:hy, :hx].mean(),   # image upper-left  = geographic NW
        "ur": mask[:hy, hx:].mean(),   # image upper-right = geographic NE
        "ll": mask[hy:, :hx].mean(),   # image lower-left  = geographic SW
        "lr": mask[hy:, hx:].mean(),   # image lower-right = geographic SE
    }

    # North arrow → prefer NW or NE corner (upper in geographic space)
    north_c = "ul" if dens["ul"] <= dens["ur"] else "ur"
    # Scale bar → prefer SW or SE corner (lower in geographic space)
    scale_c = "ll" if dens["ll"] <= dens["lr"] else "lr"

    x0, y0, x1, y1 = bounds
    w, h = x1 - x0, y1 - y0

    def _pos(cc: str) -> tuple[float, float]:
        # cc[0]: 'u'=north/top → high y;  'l'=south/bottom → low y
        # cc[1]: 'l'=west/left → low x;   'r'=east/right   → high x
        cx = x0 + (margin if cc[1] == "l" else (1 - margin)) * w
        cy = y0 + ((1 - margin) if cc[0] == "u" else margin) * h
        return (cx, cy)

    return _pos(north_c), _pos(scale_c), scale_c
