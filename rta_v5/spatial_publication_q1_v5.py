"""
rta_v5.spatial_publication_q1_v5 — Q1 publication-grade spatial map.

6-axes layout — 2×3 GridSpec (8.8 × 10.8 in):
    Row 0: (a) Standard MK  │  (b) Modified MK  │  (c) PW-MK
    Row 1: (d) TFPW-MK      │  (e) Sen's Slope  │  [legend/metadata]

v5.3 refinements (in-place):
  • 2×3 GridSpec — province aspect ~99% panel fill (ratio 1.687 ≈ 1.698)
  • Per-panel inset colorbars (constrained_layout=False; explicit margins)
  • Symbol visual hierarchy: sig=full triangle, NS=50% grey circle
  • Station markers: green ^ = increasing, red v = decreasing (hydro convention)
  • Legend + metadata rendered into dedicated bottom-right axes cell
  • Geographic aspect via format_map_axes
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D

from .spatial_interpolation_v5 import (
    load_boundary,
    boundary_extent,
    build_grid,
    make_boundary_mask,
    idw_interpolate,
    rbf_interpolate,
    loocv,
    select_best,
    GRID_N,
)
from .spatial_layout_v5 import (
    apply_q1_typography, setup_fonts,
    LAYOUT, FONT_SERIF,
    C_INC, C_DEC, C_NS, Z_VABS,
    build_axes, build_axes_compare, build_axes_single, build_row_layout,
    north_arrow, scale_bar, panel_letter, format_map_axes,
    apply_global_panel_style,
)
from .spatial_export_v5 import save_formats


# ── Deterministic station label offsets (geographic degrees) ─────────────────
# Key = last 3 chars of station ID.  Value = (dlon, dlat) in degrees.
# Overrides quadrant-based fallback for known crowded stations.
_STN_LABEL_OFFSETS: dict[str, tuple[float, float]] = {
    "005": ( 0.010, -0.010),
    "006": ( 0.012,  0.012),
    "007": ( 0.010,  0.015),
    "201": ( 0.012, -0.014),
    "003": ( 0.010,  0.010),
    "001": (-0.012,  0.008),
    "202": (-0.014,  0.010),
}


# ── Province outline ──────────────────────────────────────────────────────────

def _draw_province(ax, polys, zorder: int = 5) -> None:
    """Draw the outer boundary ring only (largest bbox area = province outline)."""
    if not polys:
        return
    def _bbox_area(pts):
        return (pts[:, 0].max() - pts[:, 0].min()) * (pts[:, 1].max() - pts[:, 1].min())
    outer = max(polys, key=_bbox_area)
    ax.plot(outer[:, 0], outer[:, 1],
            color=LAYOUT["poly_color"], lw=LAYOUT["poly_lw"],
            solid_capstyle="round", zorder=zorder)


# ── Interpolation helper ──────────────────────────────────────────────────────

def _interp_masked(pts, vals, xi, gl, mask, method):
    """Interpolate and apply province mask; returns (n,n) float array."""
    v  = vals.astype(float)
    ok = ~np.isnan(v)
    if ok.sum() < 3:
        return np.full(gl.shape, np.nan)
    if method == "RBF":
        zz = rbf_interpolate(pts[ok], v[ok], xi).reshape(gl.shape)
    else:
        zz = idw_interpolate(pts[ok], v[ok], xi).reshape(gl.shape)
    out = zz.astype(float)
    out[~mask] = np.nan
    return out


# ── Inset colorbar ────────────────────────────────────────────────────────────

def _add_inset_cbar(
    ax,
    cmap,
    vmin: float,
    vmax: float,
    label: str,
    ticks: list[float],
    threshold_lines: list[tuple] | None = None,
) -> None:
    """Compact horizontal inset colorbar at lower-right of ax."""
    L = LAYOUT
    axins = ax.inset_axes([L["cbar_x0"], L["cbar_y0"], L["cbar_w"], L["cbar_h"]])

    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    sm   = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    cbar = ax.figure.colorbar(sm, cax=axins, orientation="horizontal")
    cbar.set_ticks(ticks)
    # Label above the bar — avoids collision with tick labels below
    cbar.ax.xaxis.set_label_position("top")
    cbar.set_label(label, fontsize=5.0, fontfamily=FONT_SERIF, labelpad=2.0)
    cbar.ax.tick_params(labelsize=4.0, length=2, pad=1.0, width=0.5)

    # Semi-transparent backing so the colorbar reads over any map colour
    axins.patch.set_facecolor("white")
    axins.patch.set_alpha(0.83)
    for sp in axins.spines.values():
        sp.set_edgecolor("#555555")
        sp.set_linewidth(0.35)

    # Significance threshold tick-lines on Z-stat colorbars
    if threshold_lines:
        for zv, ls in threshold_lines:
            if vmin < zv < vmax:
                npos = (zv - vmin) / (vmax - vmin)
                cbar.ax.axvline(npos, color="#333333", lw=0.65, ls=ls, zorder=5)


# ── Shared figure-level annotation helpers ────────────────────────────────────

def _add_figure_legend(fig, x0: float | None = None, y0: float | None = None) -> None:
    """Trend classification legend at figure bottom-left (shared by all figure types)."""
    _x0 = x0 if x0 is not None else LAYOUT["leg_x0"]
    _y0 = y0 if y0 is not None else LAYOUT["leg_y0"]
    _ms_tri = LAYOUT["leg_marker_tri"]
    _ms_cir = LAYOUT["leg_marker_cir"]
    handles = [
        Line2D([0], [0], marker="^", linestyle="none",
               markerfacecolor=C_INC, markeredgecolor="white",
               markersize=_ms_tri, label="Increasing  (p < 0.05)"),
        Line2D([0], [0], marker="v", linestyle="none",
               markerfacecolor=C_DEC, markeredgecolor="white",
               markersize=_ms_tri, label="Decreasing  (p < 0.05)"),
        Line2D([0], [0], marker="o", linestyle="none",
               markerfacecolor=C_NS, markeredgecolor="white",
               markersize=_ms_cir, label="Not significant"),
    ]
    fig.legend(
        handles=handles, loc="lower left",
        bbox_to_anchor=(_x0, _y0), bbox_transform=fig.transFigure,
        ncol=3, fontsize=LAYOUT["leg_fontsize"], framealpha=0.88,
        edgecolor="#999999", handletextpad=0.35,
        columnspacing=0.7, handlelength=0.9,
        borderpad=0.4,
    )


def _add_figure_metadata(fig, method_name: str,
                         x1: float = 0.97, y0: float = 0.01) -> None:
    """Compact interpolation method/grid text at figure bottom-right."""
    fig.text(
        x1, y0,
        f"Method: {method_name}  |  Grid: {GRID_N}×{GRID_N}",
        fontsize=4.5, color="#666666",
        fontfamily=FONT_SERIF, ha="right",
    )


def _finalize_figure(fig, out_dir, stem: str, dpi: int,
                     add_legend: bool = True,
                     legend_x0: float | None = None,
                     legend_y0: float | None = None) -> None:
    """Add optional figure-level legend, save all formats, and close figure."""
    if add_legend:
        _add_figure_legend(fig, x0=legend_x0, y0=legend_y0)
    save_formats(fig, Path(out_dir), stem, dpi)
    plt.close(fig)


def _add_inset_legend(ax) -> None:
    """Compact trend-direction legend placed inside the map panel (lower-left).

    Used for standalone single-panel figures to make them fully self-contained.
    Positioned at lower-left to avoid the inset colorbar at lower-right.
    """
    _ms_tri = LAYOUT["leg_marker_tri"]
    _ms_cir = LAYOUT["leg_marker_cir"]
    handles = [
        Line2D([0], [0], marker="^", linestyle="none",
               markerfacecolor=C_INC, markeredgecolor="white",
               markeredgewidth=0.4, markersize=_ms_tri,
               label="Increasing (p<0.05)"),
        Line2D([0], [0], marker="v", linestyle="none",
               markerfacecolor=C_DEC, markeredgecolor="white",
               markeredgewidth=0.4, markersize=_ms_tri,
               label="Decreasing (p<0.05)"),
        Line2D([0], [0], marker="o", linestyle="none",
               markerfacecolor=C_NS, markeredgecolor="white",
               markeredgewidth=0.3, markersize=_ms_cir,
               label="Not significant"),
    ]
    leg = ax.legend(
        handles=handles,
        loc="lower left",
        fontsize=LAYOUT["leg_fontsize"],
        framealpha=0.90, edgecolor="#888888",
        handletextpad=0.30, labelspacing=0.35,
        handlelength=0.9, borderpad=0.4,
    )
    leg.set_zorder(12)
    for text in leg.get_texts():
        text.set_fontfamily(FONT_SERIF)


def _export_panel_standalone(
    out_dir: Path, stem: str, dpi: int,
    polys, gl, gt, mask, zz,
    cmap, vmin, vmax,
    lons, lats, z_vals, sig_arr,
    full_title: str,
    cb_label: str, cb_ticks: list, cb_thresholds,
    xmin: float, xmax: float, ymin: float, ymax: float,
    station_ids=None,
) -> None:
    """
    Export one map panel as a fully self-contained standalone figure.

    Creates a new single-panel figure at sgl_fig_w × sgl_fig_h, renders the
    panel (raster + province + stations + decorations + inset colorbar), adds
    an inset legend inside the map, and saves in all formats.
    """
    fig = plt.figure(figsize=(LAYOUT["sgl_fig_w"], LAYOUT["sgl_fig_h"]),
                     constrained_layout=True)
    ax = build_axes_single(fig)
    _draw_panel(
        ax, polys=polys, gl=gl, gt=gt, mask=mask, zz=zz,
        cmap=cmap, vmin=vmin, vmax=vmax,
        lons=lons, lats=lats, z_vals=z_vals, sig_arr=sig_arr,
        full_title=full_title, cb_label=cb_label,
        cb_ticks=cb_ticks, cb_thresholds=cb_thresholds,
        xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
        station_ids=station_ids,
    )
    _add_inset_legend(ax)
    save_formats(fig, Path(out_dir), stem, dpi)
    plt.close(fig)


def _draw_legend_panel(ax) -> None:
    """Symbol legend rendered directly into the bottom-right axes cell."""
    ax.set_axis_off()

    _ms_tri = LAYOUT["leg_marker_tri"] + 1
    _ms_cir = LAYOUT["leg_marker_cir"] + 0.5
    handles = [
        Line2D([0], [0], marker="^", linestyle="none",
               markerfacecolor=C_INC, markeredgecolor="white",
               markeredgewidth=0.5, markersize=_ms_tri,
               label="Increasing  (p < 0.05)"),
        Line2D([0], [0], marker="v", linestyle="none",
               markerfacecolor=C_DEC, markeredgecolor="white",
               markeredgewidth=0.5, markersize=_ms_tri,
               label="Decreasing  (p < 0.05)"),
        Line2D([0], [0], marker="o", linestyle="none",
               markerfacecolor=C_NS, markeredgecolor="white",
               markeredgewidth=0.4, markersize=_ms_cir,
               label="Not significant"),
    ]

    leg = ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.50, 0.90),
        bbox_transform=ax.transAxes,
        ncol=1, fontsize=LAYOUT["leg_fontsize"] + 1.5,
        framealpha=0.0, edgecolor="none",
        handletextpad=0.5,
        handlelength=1.4,
        labelspacing=0.55,
        title="Trend Direction",
        title_fontsize=7.0,
    )
    leg.get_title().set_fontfamily(FONT_SERIF)
    leg.get_title().set_fontweight("semibold")
    for text in leg.get_texts():
        text.set_fontfamily(FONT_SERIF)

    # Subtle border
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_edgecolor("#cccccc")
        sp.set_linewidth(0.4)


# ── Single panel renderer ─────────────────────────────────────────────────────

def _draw_panel(
    ax, polys, gl, gt, mask, zz,
    cmap, vmin, vmax,
    lons, lats, z_vals, sig_arr,
    full_title: str,          # "(a) Standard MK — Z Statistic" — never wrapped
    cb_label: str,
    cb_ticks: list[float],
    cb_thresholds: list[tuple] | None,
    xmin, xmax, ymin, ymax,
    draw_inset_cbar: bool = True,
    station_ids: list | None = None,
) -> None:
    """
    Render one map panel: raster surface → province outlines → station
    markers + labels → cartographic decorations → inset colorbar.

    z-order hierarchy:
        1  raster (imshow)
        5  province/district outlines
        7  station markers
        8  station ID labels
        9  scale bar
       10  north arrow
       11  panel letter (via inset_axes — not used here; letter is in full_title)
    """
    # ── Raster interpolation surface ─────────────────────────────────────────
    zz_ma = np.ma.array(zz, mask=~mask)
    ax.imshow(
        zz_ma,
        extent=[xmin, xmax, ymin, ymax],
        origin="lower",
        cmap=cmap, vmin=vmin, vmax=vmax,
        interpolation="lanczos",   # highest-quality resampling (values unchanged)
        aspect="auto", zorder=1,
    )

    # ── Province + district outlines ─────────────────────────────────────────
    _draw_province(ax, polys)

    # ── Station markers — colour = direction × significance ──────────────────
    # Significant triangle: reduced size (tri_factor), white edge, alpha<1
    # NS circle: slightly reduced (ns_factor), reduced opacity (ns_alpha)
    _tri_s = LAYOUT["stn_size"] * LAYOUT["tri_factor"]
    _tri_a = LAYOUT["tri_alpha"]
    _ns_s  = LAYOUT["stn_size"] * LAYOUT["ns_factor"]
    _ns_a  = LAYOUT["ns_alpha"]

    for lon, lat, z, sig in zip(lons, lats, z_vals, sig_arr):
        if np.isnan(z):
            continue
        if sig:
            marker, fc = ("^", C_INC) if z > 0 else ("v", C_DEC)
            ax.scatter(lon, lat, marker=marker, s=_tri_s,
                       c=fc, edgecolors="white", linewidths=0.4,
                       alpha=_tri_a, zorder=7)
        else:
            ax.scatter(lon, lat, marker="o", s=_ns_s,
                       c=C_NS, edgecolors="white", linewidths=0.3,
                       alpha=_ns_a, zorder=7)

    # ── Station ID labels — deterministic dict + quadrant fallback ────────────
    if station_ids is not None:
        lon_range = max(xmax - xmin, 1e-6)
        lat_range = max(ymax - ymin, 1e-6)
        _ann_kw = dict(fontsize=3.2, color="#111111", zorder=8,
                       fontfamily=FONT_SERIF,
                       bbox=dict(boxstyle="square,pad=0.05",
                                 fc="white", ec="none", alpha=0.7))

        for stn_id, lon, lat in zip(station_ids, lons, lats):
            key = str(stn_id)[-3:]

            if key in _STN_LABEL_OFFSETS:
                # Deterministic geographic offset — consistent across all panels
                dlon, dlat = _STN_LABEL_OFFSETS[key]
                ha = "right" if dlon < 0 else "left"
                ax.annotate(key,
                            xy=(lon, lat),
                            xytext=(lon + dlon, lat + dlat),
                            xycoords="data", textcoords="data",
                            ha=ha, **_ann_kw)
            else:
                # Quadrant-aware point-offset fallback for unlisted stations
                x_frac = (lon - xmin) / lon_range
                y_frac = (lat - ymin) / lat_range
                near_cbar  = x_frac > 0.60 and y_frac < 0.20
                right_side = x_frac > 0.70 or (x_frac > 0.80 and y_frac > 0.78)
                south_edge = y_frac < 0.15
                if near_cbar:
                    dx, dy, ha = -6, 7, "right"
                elif right_side:
                    dx, dy, ha = -6, 4, "right"
                elif south_edge:
                    dx, dy, ha =  4, 8, "left"
                else:
                    dx, dy, ha =  5, 5, "left"
                ax.annotate(key,
                            xy=(lon, lat), xytext=(dx, dy),
                            textcoords="offset points",
                            ha=ha, **_ann_kw)

    # ── Cartographic decorations ─────────────────────────────────────────────
    ax.set_title(full_title, fontsize=7.5, pad=3.0,
                 fontfamily=FONT_SERIF, loc="center")

    apply_global_panel_style(ax, xmin, xmax, ymin, ymax)

    # ── Per-panel inset colorbar ─────────────────────────────────────────────
    if draw_inset_cbar:
        _add_inset_cbar(ax, cmap, vmin, vmax,
                        label=cb_label, ticks=cb_ticks,
                        threshold_lines=cb_thresholds)


# ── Public figure function ────────────────────────────────────────────────────

def fig_q1_spatial_trend_v5(
    comp4_df:     pd.DataFrame,
    coords_df:    pd.DataFrame,
    boundary_dir: str | Path,
    out_dir:      str | Path,
    stem:         str,
    period:       str,
    scale_key:    str = "Annual (Jan–Dec)",
    dpi:          int = 600,
) -> tuple[list[dict], str, dict]:
    """
    Generate the 5-panel Q1 spatial trend figure.

    Parameters
    ----------
    comp4_df     : S7 4-Method Comparison DataFrame (header=1, skip [0])
    coords_df    : stations DataFrame (columns: station_id, lat, lon)
    boundary_dir : directory containing boundary.shp / .dbf / .shx / .prj
    out_dir      : output directory
    stem         : filename stem (no extension)
    period       : label for figure title, e.g. "1981–2014"
    scale_key    : temporal scale label matching comp4_df["Scale"]
    dpi          : output resolution

    Returns
    -------
    loocv_rows   : list[dict]
    best_name    : 'IDW' | 'RBF'
    all_metrics  : {method: {RMSE, MAE, Bias, R2}}
    """
    apply_q1_typography()

    # ── Boundary ────────────────────────────────────────────────────────────
    polys = load_boundary(boundary_dir)
    xmin, xmax, ymin, ymax = boundary_extent(polys)

    # ── Filter scale ─────────────────────────────────────────────────────────
    df = comp4_df[comp4_df["Scale"] == scale_key].copy()
    if df.empty:
        raise ValueError(
            f"No data for scale '{scale_key}'. "
            f"Available: {comp4_df['Scale'].unique().tolist()}"
        )

    stns = df["Station"].astype(str).values
    cd   = dict(zip(
        coords_df["station_id"].astype(str),
        zip(coords_df["lon"].astype(float), coords_df["lat"].astype(float)),
    ))
    lons = np.array([cd[s][0] for s in stns])
    lats = np.array([cd[s][1] for s in stns])
    pts  = np.column_stack([lons, lats])

    # ── Grid and mask ─────────────────────────────────────────────────────────
    gl, gt, xi = build_grid(xmin, xmax, ymin, ymax, GRID_N)
    mask       = make_boundary_mask(gl, gt, polys)

    # ── Select best interpolation method (LOOCV on MMK_Z) ────────────────────
    mmk_z = df["MMK_Z"].values.astype(float)
    ok    = ~np.isnan(mmk_z)
    if ok.sum() >= 4:
        _, best_name, all_metrics = select_best(pts[ok], mmk_z[ok], gl, gt, xi)
    else:
        best_name, all_metrics = "IDW", {}
    print(f"    Method: {best_name}")

    # ── Interpolate all variables ─────────────────────────────────────────────
    loocv_rows: list[dict] = []

    def _interp(vals):
        return _interp_masked(pts, vals, xi, gl, mask, best_name)

    def _cv(col, vals):
        v, ok_ = vals.astype(float), ~np.isnan(vals.astype(float))
        if ok_.sum() >= 4:
            return loocv(pts[ok_], v[ok_], best_name)
        return {"RMSE": np.nan, "MAE": np.nan, "Bias": np.nan, "R2": np.nan}

    z_spec = [
        ("MK_Z",   "MK_sig"),
        ("MMK_Z",  "MMK_sig"),
        ("PW_Z",   "PW_sig"),
        ("TFPW_Z", "TFPW_sig"),
    ]

    grids: dict[str, np.ndarray] = {}
    sigs:  dict[str, np.ndarray] = {}

    for col, sig_col in z_spec:
        v = df[col].values.astype(float)
        loocv_rows.append({"Scale": scale_key, "Variable": col,
                           "Method": best_name, **_cv(col, v)})
        grids[col] = _interp(v)
        sigs[col]  = np.array([str(s) in ("*", "**")
                                for s in df[sig_col].values])

    slope_v  = df["MK_slope"].values.astype(float)
    loocv_rows.append({"Scale": scale_key, "Variable": "Sen_Slope",
                       "Method": best_name, **_cv("MK_slope", slope_v)})
    grids["slope"] = _interp(slope_v)
    slope_sig      = np.array([str(s) in ("*", "**")
                                for s in df["MK_sig"].values])

    # ── Colormap setup ────────────────────────────────────────────────────────
    cmap_z = matplotlib.colormaps["RdBu_r"].copy()
    cmap_z.set_bad("white")

    cmap_s = matplotlib.colormaps["RdYlGn"].copy()
    cmap_s.set_bad("white")
    fin_s   = grids["slope"][mask & np.isfinite(grids["slope"])]
    slp_abs = float(
        np.ceil(max(np.abs(fin_s).max() if len(fin_s) else 5, 5) / 5) * 5
    )

    # Colorbar ticks and ±1.96 / ±2.576 threshold markers
    z_ticks     = [-Z_VABS, 0.0, Z_VABS]
    z_thresh    = [(-1.960, "--"), (1.960, "--"), (-2.576, ":"), (2.576, ":")]
    slope_ticks = [-slp_abs, 0.0, slp_abs]

    # ── Figure: 2×3 GridSpec, constrained_layout=False ───────────────────────
    # Row 0: (a) Standard MK | (b) Modified MK | (c) PW-MK
    # Row 1: (d) TFPW-MK    | (e) Sen's Slope | [legend/metadata]
    fig = plt.figure(figsize=(LAYOUT["fig_w"], LAYOUT["fig_h"]),
                     constrained_layout=False)
    ax_a, ax_b, ax_c, ax_d, ax_e, ax_leg = build_axes(fig)

    # Shared geographic kwargs (station_ids → labels rendered inside every panel)
    geo = dict(polys=polys, gl=gl, gt=gt, mask=mask,
               lons=lons, lats=lats,
               station_ids=stns,
               xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

    # Z-stat kwargs — per-panel inset colorbars (draw_inset_cbar=True default)
    z_kw = dict(cmap=cmap_z, vmin=-Z_VABS, vmax=Z_VABS,
                cb_label="Z", cb_ticks=z_ticks, cb_thresholds=z_thresh)

    _draw_panel(ax_a, zz=grids["MK_Z"], z_vals=df["MK_Z"].values,
                sig_arr=sigs["MK_Z"],
                full_title="(a) Standard MK — Z Statistic",
                **geo, **z_kw)

    _draw_panel(ax_b, zz=grids["MMK_Z"], z_vals=df["MMK_Z"].values,
                sig_arr=sigs["MMK_Z"],
                full_title="(b) Modified MK (Hamed 1998) — Z Statistic",
                **geo, **z_kw)

    _draw_panel(ax_c, zz=grids["PW_Z"], z_vals=df["PW_Z"].values,
                sig_arr=sigs["PW_Z"],
                full_title="(c) PW-MK (Yue & Wang 2004) — Z Statistic",
                **geo, **z_kw)

    _draw_panel(ax_d, zz=grids["TFPW_Z"], z_vals=df["TFPW_Z"].values,
                sig_arr=sigs["TFPW_Z"],
                full_title="(d) TFPW-MK (Yue et al. 2002) — Z Statistic",
                **geo, **z_kw)

    _draw_panel(ax_e, zz=grids["slope"], z_vals=slope_v,
                sig_arr=slope_sig,
                full_title="(e) Sen's Slope (mm yr⁻¹)",
                cmap=cmap_s, vmin=-slp_abs, vmax=slp_abs,
                cb_label="mm yr⁻¹", cb_ticks=slope_ticks,
                cb_thresholds=None,
                **geo)

    # Legend panel (bottom-right)
    _draw_legend_panel(ax_leg)

    # ── Suptitle ──────────────────────────────────────────────────────────────
    scale_short = {
        "Annual (Jan–Dec)":     "Annual (Jan–Dec)",
        "Wet Season (May–Oct)": "Wet Season (May–Oct)",
        "Dry Season (Nov–Apr)": "Dry Season (Nov–Apr)",
    }.get(scale_key, scale_key)

    fig.suptitle(
        f"Spatial Rainfall Trend Distribution — {scale_short}  |  {period}",
        fontsize=9.5, fontfamily=FONT_SERIF, y=0.975,
    )

    # ── Save composite figure ────────────────────────────────────────────────
    out_dir = Path(out_dir)
    _finalize_figure(fig, out_dir, stem, dpi, add_legend=False)

    # ── Standalone panel exports ─────────────────────────────────────────────
    _panels = [
        ("a", "Standard MK — Z Statistic",        grids["MK_Z"],   df["MK_Z"].values,   sigs["MK_Z"],   cmap_z, -Z_VABS, Z_VABS,    "Z",       z_ticks,     z_thresh),
        ("b", "Modified MK (Hamed 1998) — Z",      grids["MMK_Z"],  df["MMK_Z"].values,  sigs["MMK_Z"],  cmap_z, -Z_VABS, Z_VABS,    "Z",       z_ticks,     z_thresh),
        ("c", "PW-MK (Yue & Wang 2004) — Z",       grids["PW_Z"],   df["PW_Z"].values,   sigs["PW_Z"],   cmap_z, -Z_VABS, Z_VABS,    "Z",       z_ticks,     z_thresh),
        ("d", "TFPW-MK (Yue et al. 2002) — Z",     grids["TFPW_Z"], df["TFPW_Z"].values, sigs["TFPW_Z"], cmap_z, -Z_VABS, Z_VABS,    "Z",       z_ticks,     z_thresh),
        ("e", "Sen's Slope (mm yr⁻¹)",             grids["slope"],  slope_v,             slope_sig,      cmap_s, -slp_abs, slp_abs,  "mm yr⁻¹", slope_ticks, None),
    ]
    for letter, title, zz, z_vals, sig, cmap, vmin, vmax, cbl, ticks, thresh in _panels:
        _export_panel_standalone(
            out_dir=out_dir, stem=f"{stem}_panel_{letter}", dpi=dpi,
            polys=polys, gl=gl, gt=gt, mask=mask, zz=zz,
            cmap=cmap, vmin=vmin, vmax=vmax,
            lons=lons, lats=lats, z_vals=z_vals, sig_arr=sig,
            full_title=title, cb_label=cbl,
            cb_ticks=ticks, cb_thresholds=thresh,
            xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
            station_ids=stns,
        )

    return loocv_rows, best_name, all_metrics


# ── Comparison figure ─────────────────────────────────────────────────────────

def fig_compare_v5(
    comp4_df:     pd.DataFrame,
    coords_df:    pd.DataFrame,
    boundary_dir: str | Path,
    out_dir:      str | Path,
    stem:         str,
    period:       str,
    scale_key:    str,
    col_a:        str,   # left panel column  (e.g. "MK_Z")
    sig_a:        str,   # left panel sig col (e.g. "MK_sig")
    title_a:      str,   # left panel title   (e.g. "(a) Standard MK — Z Statistic")
    col_b:        str,   # right panel column
    sig_b:        str,   # right panel sig col
    title_b:      str,   # right panel title
    dpi:          int = 600,
) -> None:
    """
    2-panel side-by-side method comparison figure.

    Both panels share identical Z-stat colormap, normalization, and
    significance symbology for direct visual comparison.
    """
    apply_q1_typography()

    polys = load_boundary(boundary_dir)
    xmin, xmax, ymin, ymax = boundary_extent(polys)

    df = comp4_df[comp4_df["Scale"] == scale_key].copy()
    if df.empty:
        raise ValueError(f"No data for scale '{scale_key}'")

    stns = df["Station"].astype(str).values
    cd   = dict(zip(
        coords_df["station_id"].astype(str),
        zip(coords_df["lon"].astype(float), coords_df["lat"].astype(float)),
    ))
    lons = np.array([cd[s][0] for s in stns])
    lats = np.array([cd[s][1] for s in stns])
    pts  = np.column_stack([lons, lats])

    gl, gt, xi = build_grid(xmin, xmax, ymin, ymax, GRID_N)
    mask       = make_boundary_mask(gl, gt, polys)

    # Best method from LOOCV on MMK_Z
    mmk_z = df["MMK_Z"].values.astype(float)
    ok    = ~np.isnan(mmk_z)
    best_name = select_best(pts[ok], mmk_z[ok], gl, gt, xi)[1] if ok.sum() >= 4 else "IDW"
    print(f"    Method: {best_name}")

    va = df[col_a].values.astype(float)
    vb = df[col_b].values.astype(float)
    grid_a = _interp_masked(pts, va, xi, gl, mask, best_name)
    grid_b = _interp_masked(pts, vb, xi, gl, mask, best_name)

    sig_arr_a = np.array([str(s) in ("*", "**") for s in df[sig_a].values])
    sig_arr_b = np.array([str(s) in ("*", "**") for s in df[sig_b].values])

    # Synchronized colormap and normalization
    cmap_z = matplotlib.colormaps["RdBu_r"].copy()
    cmap_z.set_bad("white")
    z_ticks  = [-Z_VABS, 0.0, Z_VABS]
    z_thresh = [(-1.960, "--"), (1.960, "--"), (-2.576, ":"), (2.576, ":")]

    geo = dict(polys=polys, gl=gl, gt=gt, mask=mask,
               lons=lons, lats=lats,
               station_ids=stns,
               xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
    z_kw = dict(cmap=cmap_z, vmin=-Z_VABS, vmax=Z_VABS,
                cb_label="Z", cb_ticks=z_ticks, cb_thresholds=z_thresh)

    fig = plt.figure(figsize=(LAYOUT["cmp_fig_w"], LAYOUT["cmp_fig_h"]),
                     constrained_layout=True)
    ax_a, ax_b = build_axes_compare(fig)

    _draw_panel(ax_a, zz=grid_a, z_vals=va, sig_arr=sig_arr_a,
                full_title=title_a, **geo, **z_kw)
    _draw_panel(ax_b, zz=grid_b, z_vals=vb, sig_arr=sig_arr_b,
                full_title=title_b, **geo, **z_kw)

    scale_short = {
        "Annual (Jan–Dec)":     "Annual (Jan–Dec)",
        "Wet Season (May–Oct)": "Wet Season (May–Oct)",
        "Dry Season (Nov–Apr)": "Dry Season (Nov–Apr)",
    }.get(scale_key, scale_key)

    fig.suptitle(
        f"Method Comparison — {scale_short}  |  {period}",
        fontsize=9.5, fontfamily=FONT_SERIF,
    )
    _finalize_figure(fig, out_dir, stem, dpi, add_legend=True, legend_x0=0.07)

    # ── Standalone panel exports ─────────────────────────────────────────────
    _pair = [
        ("a", title_a, grid_a, va, sig_arr_a),
        ("b", title_b, grid_b, vb, sig_arr_b),
    ]
    for letter, title, zz, z_vals, sig in _pair:
        _export_panel_standalone(
            out_dir=Path(out_dir), stem=f"{stem}_panel_{letter}", dpi=dpi,
            polys=polys, gl=gl, gt=gt, mask=mask, zz=zz,
            cmap=cmap_z, vmin=-Z_VABS, vmax=Z_VABS,
            lons=lons, lats=lats, z_vals=z_vals, sig_arr=sig,
            full_title=title, cb_label="Z",
            cb_ticks=z_ticks, cb_thresholds=z_thresh,
            xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
            station_ids=stns,
        )


# ── Single-method figure ──────────────────────────────────────────────────────

def fig_single_v5(
    comp4_df:     pd.DataFrame,
    coords_df:    pd.DataFrame,
    boundary_dir: str | Path,
    out_dir:      str | Path,
    stem:         str,
    period:       str,
    scale_key:    str,
    col:          str,       # data column (e.g. "MK_Z" or "MK_slope")
    sig_col:      str,       # significance column (e.g. "MK_sig")
    panel_title:  str,       # axes title (e.g. "Standard MK — Z Statistic")
    is_slope:     bool = False,
    dpi:          int  = 600,
) -> None:
    """
    Single-panel standalone publication figure for one trend method.

    Portrait orientation, province-shape-aware aspect.
    """
    apply_q1_typography()

    polys = load_boundary(boundary_dir)
    xmin, xmax, ymin, ymax = boundary_extent(polys)

    df = comp4_df[comp4_df["Scale"] == scale_key].copy()
    if df.empty:
        raise ValueError(f"No data for scale '{scale_key}'")

    stns = df["Station"].astype(str).values
    cd   = dict(zip(
        coords_df["station_id"].astype(str),
        zip(coords_df["lon"].astype(float), coords_df["lat"].astype(float)),
    ))
    lons = np.array([cd[s][0] for s in stns])
    lats = np.array([cd[s][1] for s in stns])
    pts  = np.column_stack([lons, lats])

    gl, gt, xi = build_grid(xmin, xmax, ymin, ymax, GRID_N)
    mask       = make_boundary_mask(gl, gt, polys)

    mmk_z = df["MMK_Z"].values.astype(float)
    ok    = ~np.isnan(mmk_z)
    best_name = select_best(pts[ok], mmk_z[ok], gl, gt, xi)[1] if ok.sum() >= 4 else "IDW"
    print(f"    Method: {best_name}")

    v   = df[col].values.astype(float)
    grd = _interp_masked(pts, v, xi, gl, mask, best_name)
    sig_arr = np.array([str(s) in ("*", "**") for s in df[sig_col].values])

    if is_slope:
        cmap = matplotlib.colormaps["RdYlGn"].copy()
        cmap.set_bad("white")
        fin    = grd[mask & np.isfinite(grd)]
        slpabs = float(np.ceil(max(np.abs(fin).max() if len(fin) else 5, 5) / 5) * 5)
        vmin, vmax = -slpabs, slpabs
        ticks  = [-slpabs, 0.0, slpabs]
        thresh = None
        cb_lbl = "mm yr⁻¹"
    else:
        cmap = matplotlib.colormaps["RdBu_r"].copy()
        cmap.set_bad("white")
        vmin, vmax = -Z_VABS, Z_VABS
        ticks  = [-Z_VABS, 0.0, Z_VABS]
        thresh = [(-1.960, "--"), (1.960, "--"), (-2.576, ":"), (2.576, ":")]
        cb_lbl = "Z"

    geo = dict(polys=polys, gl=gl, gt=gt, mask=mask,
               lons=lons, lats=lats,
               station_ids=stns,
               xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

    fig = plt.figure(figsize=(LAYOUT["sgl_fig_w"], LAYOUT["sgl_fig_h"]),
                     constrained_layout=True)
    ax = build_axes_single(fig)

    _draw_panel(ax, zz=grd, z_vals=v, sig_arr=sig_arr,
                full_title=panel_title,
                cmap=cmap, vmin=vmin, vmax=vmax,
                cb_label=cb_lbl, cb_ticks=ticks, cb_thresholds=thresh,
                **geo)

    scale_short = {
        "Annual (Jan–Dec)":     "Annual (Jan–Dec)",
        "Wet Season (May–Oct)": "Wet Season (May–Oct)",
        "Dry Season (Nov–Apr)": "Dry Season (Nov–Apr)",
    }.get(scale_key, scale_key)

    fig.suptitle(
        f"{scale_short}  |  {period}",
        fontsize=9.0, fontfamily=FONT_SERIF,
    )
    # Standalone figure: inset legend inside the map panel (fully self-contained)
    _add_inset_legend(ax)
    _finalize_figure(fig, out_dir, stem, dpi, add_legend=False)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Modular row-figure helpers                                              ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def _row_setup(comp4_df, coords_df, boundary_dir, scale_key):
    """Shared setup: boundary, coords, grid, mask, best interpolation method."""
    polys = load_boundary(boundary_dir)
    xmin, xmax, ymin, ymax = boundary_extent(polys)

    df = comp4_df[comp4_df["Scale"] == scale_key].copy()
    if df.empty:
        raise ValueError(
            f"No data for scale '{scale_key}'. "
            f"Available: {comp4_df['Scale'].unique().tolist()}"
        )

    stns = df["Station"].astype(str).values
    cd   = dict(zip(
        coords_df["station_id"].astype(str),
        zip(coords_df["lon"].astype(float), coords_df["lat"].astype(float)),
    ))
    lons = np.array([cd[s][0] for s in stns])
    lats = np.array([cd[s][1] for s in stns])
    pts  = np.column_stack([lons, lats])

    gl, gt, xi = build_grid(xmin, xmax, ymin, ymax, GRID_N)
    mask        = make_boundary_mask(gl, gt, polys)

    mmk_z = df["MMK_Z"].values.astype(float)
    ok    = ~np.isnan(mmk_z)
    method = select_best(pts[ok], mmk_z[ok], gl, gt, xi)[1] if ok.sum() >= 4 else "IDW"

    return polys, df, stns, lons, lats, pts, gl, gt, xi, mask, xmin, xmax, ymin, ymax, method


def plot_method_panel(ax, df_row, col, sig_col, pts, gl, gt, xi, mask, method,
                      cmap, vmin, vmax, z_ticks, z_thresh, title,
                      polys, lons, lats, xmin, xmax, ymin, ymax,
                      station_ids=None) -> None:
    """Render one Z-statistic method panel (reuses _draw_panel)."""
    vals    = df_row[col].values.astype(float)
    sig_arr = np.array([str(s) in ("*", "**") for s in df_row[sig_col].values])
    zz      = _interp_masked(pts, vals, xi, gl, mask, method)
    _draw_panel(ax, polys=polys, gl=gl, gt=gt, mask=mask, zz=zz,
                cmap=cmap, vmin=vmin, vmax=vmax,
                lons=lons, lats=lats, z_vals=vals, sig_arr=sig_arr,
                full_title=title, cb_label="Z",
                cb_ticks=z_ticks, cb_thresholds=z_thresh,
                xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                station_ids=station_ids)


def plot_senslope_panel(ax, slope_vals, sig_arr, pts, gl, gt, xi, mask, method,
                        cmap, vabs, title,
                        polys, lons, lats, xmin, xmax, ymin, ymax,
                        station_ids=None) -> None:
    """Render one Sen's slope panel (reuses _draw_panel)."""
    zz = _interp_masked(pts, slope_vals, xi, gl, mask, method)
    _draw_panel(ax, polys=polys, gl=gl, gt=gt, mask=mask, zz=zz,
                cmap=cmap, vmin=-vabs, vmax=vabs,
                lons=lons, lats=lats, z_vals=slope_vals, sig_arr=sig_arr,
                full_title=title, cb_label="mm yr⁻¹",
                cb_ticks=[-vabs, 0.0, vabs], cb_thresholds=None,
                xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                station_ids=station_ids)


# ── Four-method comparison row ────────────────────────────────────────────────

def fig_4method_row_v5(
    comp4_df:     pd.DataFrame,
    coords_df:    pd.DataFrame,
    boundary_dir: str | Path,
    out_dir:      str | Path,
    stem:         str,
    period:       str,
    scale_key:    str,
    dpi:          int = 600,
) -> None:
    """
    Single-row 4-panel: (a) MK  (b) MMK  (c) PW-MK  (d) TFPW-MK.

    All panels share Z-stat colormap; per-panel inset colorbars.
    """
    apply_q1_typography()
    polys, df, stns, lons, lats, pts, gl, gt, xi, mask, xmin, xmax, ymin, ymax, method = \
        _row_setup(comp4_df, coords_df, boundary_dir, scale_key)
    print(f"    Method: {method}")

    cmap_z = matplotlib.colormaps["RdBu_r"].copy()
    cmap_z.set_bad("white")
    z_ticks  = [-Z_VABS, 0.0, Z_VABS]
    z_thresh = [(-1.960, "--"), (1.960, "--"), (-2.576, ":"), (2.576, ":")]

    geo = dict(polys=polys, lons=lons, lats=lats,
               xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

    specs = [
        ("MK_Z",   "MK_sig",   "(a) Standard MK — Z"),
        ("MMK_Z",  "MMK_sig",  "(b) Modified MK (Hamed 1998) — Z"),
        ("PW_Z",   "PW_sig",   "(c) PW-MK (Yue & Wang 2004) — Z"),
        ("TFPW_Z", "TFPW_sig", "(d) TFPW-MK (Yue et al. 2002) — Z"),
    ]

    fig = plt.figure(figsize=(LAYOUT["row4_fig_w"], LAYOUT["row4_fig_h"]),
                     constrained_layout=False)
    axes = build_row_layout(fig, 4)

    for ax, (col, sig_col, title) in zip(axes, specs):
        plot_method_panel(ax, df, col, sig_col, pts, gl, gt, xi, mask, method,
                          cmap_z, -Z_VABS, Z_VABS, z_ticks, z_thresh, title,
                          station_ids=stns, **geo)

    scale_short = {
        "Annual (Jan–Dec)":     "Annual (Jan–Dec)",
        "Wet Season (May–Oct)": "Wet Season (May–Oct)",
        "Dry Season (Nov–Apr)": "Dry Season (Nov–Apr)",
    }.get(scale_key, scale_key)
    fig.suptitle(
        f"Four-Method MK Comparison — {scale_short}  |  {period}",
        fontsize=9.0, fontfamily=FONT_SERIF, y=0.97,
    )
    _finalize_figure(fig, out_dir, stem, dpi, add_legend=True)

    # ── Standalone panel exports ─────────────────────────────────────────────
    for col, sig_col, title in specs:
        vals = df[col].values.astype(float)
        sig  = np.array([str(s) in ("*", "**") for s in df[sig_col].values])
        zz   = _interp_masked(pts, vals, xi, gl, mask, method)
        _export_panel_standalone(
            out_dir=Path(out_dir), stem=f"{stem}_{col.lower()}", dpi=dpi,
            polys=polys, gl=gl, gt=gt, mask=mask, zz=zz,
            cmap=cmap_z, vmin=-Z_VABS, vmax=Z_VABS,
            lons=lons, lats=lats, z_vals=vals, sig_arr=sig,
            full_title=title.replace("(a) ", "").replace("(b) ", "")
                             .replace("(c) ", "").replace("(d) ", ""),
            cb_label="Z", cb_ticks=z_ticks, cb_thresholds=z_thresh,
            xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
            station_ids=stns,
        )


# ── Sen's slope all-scales row ────────────────────────────────────────────────

def fig_senslope_row_v5(
    comp4_df:     pd.DataFrame,
    coords_df:    pd.DataFrame,
    boundary_dir: str | Path,
    out_dir:      str | Path,
    stem:         str,
    period:       str,
    scale_keys:   list[str],
    dpi:          int = 600,
) -> None:
    """
    Single-row Sen's slope panels across all temporal scales.

    Panels share identical color scale (global |slope| max).
    """
    apply_q1_typography()

    # Boundary and grid are the same for every scale
    polys = load_boundary(boundary_dir)
    xmin, xmax, ymin, ymax = boundary_extent(polys)
    gl, gt, xi = build_grid(xmin, xmax, ymin, ymax, GRID_N)
    mask        = make_boundary_mask(gl, gt, polys)

    cmap_s = matplotlib.colormaps["RdYlGn"].copy()
    cmap_s.set_bad("white")

    panels: list[dict] = []
    global_vabs = 5.0

    for scale_key in scale_keys:
        df = comp4_df[comp4_df["Scale"] == scale_key].copy()
        if df.empty:
            continue

        stns = df["Station"].astype(str).values
        cd   = dict(zip(
            coords_df["station_id"].astype(str),
            zip(coords_df["lon"].astype(float), coords_df["lat"].astype(float)),
        ))
        lons = np.array([cd[s][0] for s in stns])
        lats = np.array([cd[s][1] for s in stns])
        pts  = np.column_stack([lons, lats])

        mmk_z = df["MMK_Z"].values.astype(float)
        ok    = ~np.isnan(mmk_z)
        method = select_best(pts[ok], mmk_z[ok], gl, gt, xi)[1] if ok.sum() >= 4 else "IDW"
        print(f"    {scale_key}: {method}")

        slope_v = df["MK_slope"].values.astype(float)
        sig_arr = np.array([str(s) in ("*", "**") for s in df["MK_sig"].values])
        zz      = _interp_masked(pts, slope_v, xi, gl, mask, method)

        fin = zz[mask & np.isfinite(zz)]
        if len(fin):
            global_vabs = max(global_vabs,
                              float(np.ceil(np.abs(fin).max() / 5) * 5))

        panels.append(dict(lons=lons, lats=lats, pts=pts, slope_v=slope_v,
                           sig_arr=sig_arr, zz=zz, scale_key=scale_key,
                           method=method, stns=stns))

    global_vabs = float(np.ceil(max(global_vabs, 5) / 5) * 5)

    _LABELS = {
        "Annual (Jan–Dec)":     "Annual",
        "Wet Season (May–Oct)": "Wet Season",
        "Dry Season (Nov–Apr)": "Dry Season",
    }
    letters = ["(a)", "(b)", "(c)", "(d)"]

    fig = plt.figure(figsize=(LAYOUT["row_sens_fig_w"], LAYOUT["row_sens_fig_h"]),
                     constrained_layout=False)
    axes = build_row_layout(fig, len(panels))

    # Track method names for metadata (use the last scale's method as representative)
    method_label = panels[-1]["method"] if panels else "IDW"

    for ax, pdata, letter in zip(axes, panels, letters):
        title = (f"{letter} {_LABELS.get(pdata['scale_key'], pdata['scale_key'])}"
                 f" — mm yr⁻¹")
        plot_senslope_panel(
            ax, pdata["slope_v"], pdata["sig_arr"],
            pts=pdata["pts"], gl=gl, gt=gt, xi=xi, mask=mask,
            method=pdata["method"], cmap=cmap_s, vabs=global_vabs,
            title=title, polys=polys,
            lons=pdata["lons"], lats=pdata["lats"],
            xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
            station_ids=pdata["stns"],
        )

    fig.suptitle(
        f"Sen's Slope — All Temporal Scales  |  {period}",
        fontsize=9.0, fontfamily=FONT_SERIF, y=0.97,
    )
    _finalize_figure(fig, out_dir, stem, dpi, add_legend=True)

    # ── Standalone panel exports ─────────────────────────────────────────────
    for pdata in panels:
        scale_label = _LABELS.get(pdata["scale_key"], pdata["scale_key"])
        panel_stem  = f"{stem}_{scale_label.replace(' ', '_')}"
        _export_panel_standalone(
            out_dir=Path(out_dir), stem=panel_stem, dpi=dpi,
            polys=polys, gl=gl, gt=gt, mask=mask, zz=pdata["zz"],
            cmap=cmap_s, vmin=-global_vabs, vmax=global_vabs,
            lons=pdata["lons"], lats=pdata["lats"],
            z_vals=pdata["slope_v"], sig_arr=pdata["sig_arr"],
            full_title=f"{scale_label} — Sen's Slope (mm yr⁻¹)",
            cb_label="mm yr⁻¹",
            cb_ticks=[-global_vabs, 0.0, global_vabs], cb_thresholds=None,
            xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
            station_ids=pdata["stns"],
        )
