"""figures.base — Publication figure utilities (Q1 journal standard).

Typography:
  Serif font (Times New Roman → Liberation Serif → DejaVu Serif) for
  compliance with most Q1 hydrology journals (J. Hydrol., WRR, HESS, etc.).

Requirement 1 (save_dual):
  Every figure is rendered at BOTH single-column (3.5″) and double-column
  (7.2″) widths, saved in all configured formats (PNG/TIFF/PDF at 600 DPI).
  No figure title, no footnote; panels use (a)(b)(c) labels.

Requirement 2 (auto_color_range):
  Colour limits use the robust 2–98 percentile of the data, with zero-centred
  symmetric limits for diverging (change) maps.

Requirement 3 (free_corner):
  Compass rose and scale bar are placed in the emptiest map corner to avoid
  overlap with land features. Correct geographic/image-array convention:
  image row 0 = geographic NORTH.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

log = logging.getLogger(__name__)

# ── Typography ────────────────────────────────────────────────────────────────
_SERIF_PREFS = (
    "Times New Roman", "Liberation Serif", "DejaVu Serif",
    "Georgia", "FreeSerif",
)
_available = {f.name for f in font_manager.fontManager.ttflist}
_chosen    = next((f for f in _SERIF_PREFS if f in _available), "DejaVu Serif")

plt.rcParams.update({
    # Font
    "font.family":         "serif",
    "font.serif":          [_chosen],
    "font.size":           9,
    "axes.titlesize":      9,
    "axes.labelsize":      9,
    "xtick.labelsize":     8,
    "ytick.labelsize":     8,
    "legend.fontsize":     8,
    "legend.framealpha":   0.88,
    "legend.edgecolor":    "0.70",
    # Axes
    "axes.spines.top":     False,
    "axes.spines.right":   False,
    "axes.linewidth":      0.8,
    "axes.grid":           True,
    "grid.linestyle":      "--",
    "grid.linewidth":      0.40,
    "grid.alpha":          0.45,
    # Lines
    "lines.linewidth":     1.2,
    "lines.markersize":    4,
    # Output — embed fonts (required by many journals for PDF/EPS)
    "savefig.dpi":         600,
    "savefig.bbox":        "tight",
    "savefig.pad_inches":  0.05,
    "pdf.fonttype":        42,
    "ps.fonttype":         42,
    "hatch.linewidth":     0.4,
})

log.debug("Publication font: %s", _chosen)


# ── Panel labels ──────────────────────────────────────────────────────────────

def panel_tag(ax, tag: str, loc: tuple[float, float] = (0.02, 0.96)):
    """Compact panel label for simple subplots."""
    ax.text(*loc, f"({tag})", transform=ax.transAxes, fontweight="bold",
            va="top", ha="left", fontsize=10,
            bbox=dict(boxstyle="round,pad=0.20", fc="white", ec="none", alpha=0.85))


PANEL_LABEL = {"x": 0.03, "y": 0.97, "fontsize": 10, "fontweight": "bold"}


def add_panel_label(ax, tag: str, subtitle: str | None = None):
    """Standard (a)/( b)(c) label — identical position and size across all figures."""
    txt = f"({tag})" + (f" {subtitle}" if subtitle else "")
    ax.text(PANEL_LABEL["x"], PANEL_LABEL["y"], txt,
            transform=ax.transAxes,
            ha="left", va="top",
            fontsize=PANEL_LABEL["fontsize"],
            fontweight=PANEL_LABEL["fontweight"],
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.85))


# ── Save helper ───────────────────────────────────────────────────────────────

def save_dual(fig_builder, fid: str, cfg: dict) -> list[Path]:
    """Build and save a figure at single and double column widths × all formats.

    fig_builder(width_in) → matplotlib Figure.
    Returns list of Path objects for every file written.
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
            save_kw = dict(dpi=dpi, bbox_inches="tight", pad_inches=0.05)
            if fmt.lower() in ("tif", "tiff"):
                # LZW-compressed TIFF: lossless, journal-standard, ~10× smaller
                save_kw["pil_kwargs"] = {"compression": "tiff_lzw"}
            fig.savefig(p, **save_kw)
            saved.append(p)
        plt.close(fig)

    log.info("saved %s: %d files (×%d formats × single/double)", fid, len(saved), len(fmts))
    return saved


# ── Auto colour range ─────────────────────────────────────────────────────────

def auto_color_range(values, diverging: bool = False) -> tuple[float, float]:
    """Robust colour limits (2–98 percentile). Zero-centred when diverging=True."""
    v = np.asarray(values, float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return (-1.0, 1.0) if diverging else (0.0, 1.0)
    lo, hi = np.percentile(v, [2, 98])
    if diverging:
        m = max(abs(lo), abs(hi)) or 1.0
        return (-m, m)
    return (float(lo), float(hi))


# ── Free-corner label placement ───────────────────────────────────────────────

def free_corner(mask: np.ndarray,
                bounds: tuple[float, float, float, float],
                margin: float = 0.12) -> tuple[tuple, tuple, str]:
    """Return (north_xy, scale_xy, scale_corner) in the emptiest map corners.

    mask is a 2-D boolean array in **image** coordinates
    (row 0 = geographic NORTH, row -1 = geographic SOUTH).

    Quadrant key:
        ul = image top-left    = geographic NW  (north half, west half)
        ur = image top-right   = geographic NE
        ll = image bottom-left = geographic SW  (south half, west half)
        lr = image bottom-right= geographic SE
    """
    ny, nx = mask.shape
    hy, hx = ny // 2, nx // 2

    dens = {
        "ul": mask[:hy, :hx].mean(),   # geo NW
        "ur": mask[:hy, hx:].mean(),   # geo NE
        "ll": mask[hy:, :hx].mean(),   # geo SW
        "lr": mask[hy:, hx:].mean(),   # geo SE
    }

    # North arrow → prefer NW/NE (north = small row indices in image)
    north_c = "ul" if dens["ul"] <= dens["ur"] else "ur"
    # Scale bar → prefer SW/SE (south = large row indices in image)
    scale_c = "ll" if dens["ll"] <= dens["lr"] else "lr"

    x0, y0, x1, y1 = bounds
    w, h = x1 - x0, y1 - y0

    def _pos(cc: str) -> tuple[float, float]:
        # cc[1]: 'l'=west→low x, 'r'=east→high x
        # cc[0]: 'u'=north→high y, 'l'=south→low y
        cx = x0 + (margin if cc[1] == "l" else (1 - margin)) * w
        cy = y0 + ((1 - margin) if cc[0] == "u" else margin) * h
        return (cx, cy)

    return _pos(north_c), _pos(scale_c), scale_c
