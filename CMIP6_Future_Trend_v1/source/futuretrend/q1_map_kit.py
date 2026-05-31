"""
q1_map_kit — Standard Q1 Publication Map Engine (reusable across all projects)
=============================================================================

A standalone, config-driven map engine for publication-quality (Q1) spatial
figures. Designed to be dropped into any hydroclimate/GIS project unchanged;
all behaviour is controlled by ``MapStyle`` (a dataclass) so adjustments —
adding a station-id label, nudging the scale bar off the edge, tuning spacing,
swapping palettes — are done by editing config, NOT logic.

Design goals
------------
1. Continuous surface (IDW) → boundary clip → station overlay → boundary on top.
2. Fully dynamic layout from the boundary bounding box (no hard-coded positions).
3. Collision-aware placement: north arrow / scale bar / labels go to the emptiest
   free corner and keep a configurable margin off the map edge.
4. One central style object → consistent typography, colours, element sizes.
5. Reusable: change boundary.shp + station_coordinates.csv only.

Public API
----------
    MapStyle                      — all tunable parameters (edit this to customise)
    load_gis(dir)                 — read boundary + stations
    surface_panel(ax, ...)        — render one IDW surface panel with full cartography
    new_figure(n_panels, style)   — create a tight, balanced figure + axes
    finalize(fig, ...)            — shared colorbar + suptitle + export PNG (600 dpi)
    station_labels(ax, ...)       — optional station-id labels (collision-nudged)

This module performs NO scientific computation; it only visualises values that
the caller supplies per station.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from shapely.geometry import Point
from shapely.prepared import prep

log = logging.getLogger(__name__)

__all__ = ["MapStyle", "GisData", "load_gis", "new_figure", "surface_panel",
           "station_labels", "finalize"]


# ─────────────────────────────────────────────────────────────────────────────────
# CONFIG — edit here to customise every map (no logic changes needed)
# ─────────────────────────────────────────────────────────────────────────────────
@dataclass
class MapStyle:
    # typography (pt)
    title_size: int = 18
    panel_title_size: int = 13
    axis_size: int = 11
    legend_size: int = 11
    colorbar_size: int = 11
    font_candidates: tuple = ("Liberation Sans", "Arial", "Helvetica", "DejaVu Sans")

    # colour semantics (consistent everywhere)
    cmap_diverging: str = "RdBu_r"     # +increase red / −decrease blue
    cmap_sequential: str = "YlOrRd"    # uncertainty / agreement (light→dark)

    # layout / spacing
    bbox_pad: float = 0.02             # padding around boundary (fraction of span)
    panel_w_in: float = 4.4            # width per panel (inches)
    panel_h_in: float = 6.2            # panel height (inches)
    edge_margin: float = 0.12          # KEEP elements this far inside the bbox
                                       #   (raise to push scale bar / arrow off edge)
    element_gap: float = 0.05          # extra gap so elements never touch the edge

    # cartographic element sizes
    boundary_lw: float = 1.2
    station_size: float = 26
    station_edge: str = "white"
    north_fontsize_delta: int = 2      # added to axis_size
    scalebar_lw: float = 3.0
    grid_lw: float = 0.4
    grid_color: str = "0.85"

    # interpolation
    grid_n: int = 220
    idw_power: float = 2.0

    # colorbar
    colorbar_shrink: float = 0.85
    colorbar_aspect: int = 28
    colorbar_fraction: float = 0.040
    colorbar_pad: float = 0.015

    # station labels (optional)
    show_station_labels: bool = False
    station_label_size: int = 7
    station_label_dx: float = 0.012    # offset (fraction of width) to avoid the marker
    station_label_dy: float = 0.0

    # export
    dpi: int = 600

    def apply_rcparams(self):
        for fam in self.font_candidates:
            if any(fam in f.name for f in font_manager.fontManager.ttflist):
                plt.rcParams["font.family"] = fam
                break
        plt.rcParams.update({
            "font.size": self.axis_size,
            "axes.titlesize": self.panel_title_size,
            "axes.labelsize": self.axis_size,
            "xtick.labelsize": self.axis_size - 1,
            "ytick.labelsize": self.axis_size - 1,
            "legend.fontsize": self.legend_size,
            "savefig.dpi": self.dpi,
        })


@dataclass
class GisData:
    geometry: object
    bounds: tuple
    stations: pd.DataFrame


# ─────────────────────────────────────────────────────────────────────────────────
def load_gis(gis_dir: str | Path) -> GisData:
    """Read boundary.shp (→ lat/lon) + station_coordinates.csv (station, lat, lon)."""
    import geopandas as gpd
    b = gpd.read_file(Path(gis_dir) / "boundary.shp").to_crs(4326)
    geom = b.union_all() if hasattr(b, "union_all") else b.unary_union
    st = pd.read_csv(Path(gis_dir) / "station_coordinates.csv")
    st["station"] = st["station"].astype(str)
    return GisData(geom, tuple(b.total_bounds), st)


def _nice_scale_km(width_deg: float) -> int:
    km = width_deg * 111.0
    target = 10
    for cand in (10, 20, 25, 50, 100, 200):
        if cand <= km * 0.5:
            target = cand
    return target


def _layout(bounds, style: MapStyle) -> dict:
    x0, y0, x1, y1 = bounds
    w, h = x1 - x0, y1 - y0
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "w": w, "h": h,
            "xlim": (x0 - style.bbox_pad * w, x1 + style.bbox_pad * w),
            "ylim": (y0 - style.bbox_pad * h, y1 + style.bbox_pad * h),
            "scale_km": _nice_scale_km(w)}


def _free_corners(mask: np.ndarray, lay: dict, style: MapStyle):
    """Pick emptiest upper corner (north arrow) and lower corner (scale bar),
    keeping a configurable margin off the edge so nothing touches the boundary."""
    ny, nx = mask.shape
    hy, hx = ny // 2, nx // 2
    dens = {"ll": mask[:hy, :hx].mean(), "lr": mask[:hy, hx:].mean(),
            "ul": mask[hy:, :hx].mean(), "ur": mask[hy:, hx:].mean()}
    north_c = "ul" if dens["ul"] <= dens["ur"] else "ur"
    scale_c = "ll" if dens["ll"] <= dens["lr"] else "lr"
    m = style.edge_margin + style.element_gap
    x0, y0, w, h = lay["x0"], lay["y0"], lay["w"], lay["h"]

    def pos(cc):
        cx = x0 + (m if cc[1] == "l" else 1 - m) * w
        cy = y0 + (m if cc[0] == "l" else 1 - m) * h
        return (cx, cy)
    return pos(north_c), pos(scale_c), scale_c


def _idw(xy, vals, gx, gy, power):
    pts = np.column_stack([gx.ravel(), gy.ravel()])
    d = np.sqrt(((pts[:, None, :] - xy[None, :, :]) ** 2).sum(axis=2))
    d = np.where(d < 1e-9, 1e-9, d)
    w = 1.0 / d ** power
    z = (w * vals[None, :]).sum(axis=1) / w.sum(axis=1)
    return z.reshape(gx.shape)


def _mask_inside(gx, gy, geom):
    pg = prep(geom)
    flat = np.fromiter((pg.contains(Point(x, y)) for x, y in zip(gx.ravel(), gy.ravel())),
                       dtype=bool, count=gx.size)
    return flat.reshape(gx.shape)


def _draw_boundary(ax, geom, style: MapStyle):
    polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    for p in polys:
        xs, ys = p.exterior.xy
        ax.plot(xs, ys, color="#222", lw=style.boundary_lw, zorder=5)


def _add_north(ax, xy, lay, style: MapStyle):
    x, y = xy
    ax.annotate("N", xy=(x, y), xytext=(x, y - 0.07 * lay["h"]), ha="center", va="center",
                fontsize=style.axis_size + style.north_fontsize_delta, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color="k", lw=1.6), zorder=8)


def _add_scalebar(ax, xy, lay, style: MapStyle, scale_corner: str):
    x, y = xy; km = lay["scale_km"]; deg = km / 111.0
    # if placed in a right corner, extend leftwards so the bar stays off the edge
    x_start = x - deg if scale_corner.endswith("r") else x
    ax.plot([x_start, x_start + deg], [y, y], "k-", lw=style.scalebar_lw, zorder=8,
            solid_capstyle="butt")
    ax.text(x_start + deg / 2, y + 0.015 * lay["h"], f"{km} km",
            ha="center", va="bottom", fontsize=style.axis_size - 1, zorder=8)


def _add_graticule(ax, style: MapStyle):
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
    ax.tick_params(direction="out", length=3)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.2f}"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.2f}"))
    ax.grid(True, color=style.grid_color, lw=style.grid_lw, ls=":", zorder=1)


# ─────────────────────────────────────────────────────────────────────────────────
def new_figure(n_panels: int, style: MapStyle):
    style.apply_rcparams()
    fig, axes = plt.subplots(1, n_panels,
                             figsize=(style.panel_w_in * n_panels, style.panel_h_in),
                             constrained_layout=True)
    if n_panels == 1:
        axes = [axes]
    return fig, list(axes)


def surface_panel(ax, gis: GisData, stations_xy: np.ndarray, values: np.ndarray,
                  cmap: str, vmin: float, vmax: float, panel_title: str,
                  style: MapStyle):
    """Render one Q1 surface panel: IDW → clip → overlay → cartography."""
    lay = _layout(gis.bounds, style)
    x0, y0, x1, y1 = gis.bounds
    gx, gy = np.meshgrid(np.linspace(x0, x1, style.grid_n),
                         np.linspace(y0, y1, style.grid_n))
    finite = np.isfinite(values)
    z = _idw(stations_xy[finite], values[finite], gx, gy, style.idw_power)
    mask = _mask_inside(gx, gy, gis.geometry)
    z = np.ma.array(z, mask=~mask)
    im = ax.pcolormesh(gx, gy, z, cmap=cmap, vmin=vmin, vmax=vmax, shading="auto", zorder=2)
    _draw_boundary(ax, gis.geometry, style)
    ax.scatter(stations_xy[:, 0], stations_xy[:, 1], s=style.station_size, c="k",
               edgecolor=style.station_edge, lw=0.4, zorder=6)
    ax.set_xlim(*lay["xlim"]); ax.set_ylim(*lay["ylim"])
    ax.set_aspect("equal", adjustable="box"); ax.margins(0)
    north_xy, scale_xy, scorner = _free_corners(mask, lay, style)
    _add_graticule(ax, style)
    _add_north(ax, north_xy, lay, style)
    _add_scalebar(ax, scale_xy, lay, style, scorner)
    ax.set_title(panel_title, fontsize=style.panel_title_size)
    return im


def station_labels(ax, stations: pd.DataFrame, lay_bounds, style: MapStyle,
                   id_col: str = "station"):
    """Optional station-id labels, offset to avoid the marker (config-driven)."""
    if not style.show_station_labels:
        return
    w = lay_bounds[2] - lay_bounds[0]
    for _, r in stations.iterrows():
        ax.annotate(str(r[id_col]), (r["lon"], r["lat"]),
                    xytext=(r["lon"] + style.station_label_dx * w,
                            r["lat"] + style.station_label_dy * w),
                    fontsize=style.station_label_size, zorder=7,
                    ha="left", va="center")


def finalize(fig, axes, im, title: str, colorbar_label: str, out_path: str | Path,
             style: MapStyle):
    """Shared colorbar + suptitle + tight export (PNG 600 dpi)."""
    if im is not None:
        cb = fig.colorbar(im, ax=axes, fraction=style.colorbar_fraction,
                          pad=style.colorbar_pad, shrink=style.colorbar_shrink,
                          aspect=style.colorbar_aspect)
        cb.set_label(colorbar_label, fontsize=style.colorbar_size)
        cb.ax.tick_params(labelsize=style.colorbar_size - 1)
    fig.suptitle(title, fontsize=style.title_size)
    out_path = Path(out_path)
    fig.savefig(out_path, dpi=style.dpi, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    return out_path
