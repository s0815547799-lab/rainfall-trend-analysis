"""
rta_v5.spatial_publication_q1_v5 — Refined Q1 publication-grade spatial map.

5-panel layout:
    (a) Standard MK   │  (b) Modified MK
    (c) PW-MK         │  (d) TFPW-MK
              (e) Sen's Slope   ← exactly centred

Design decisions:
  • Province boundary from boundary.shp only — no fallback
  • No legend or metric boxes inside the figure body
  • One shared Z colorbar (a–d) + one slope colorbar (e), equal width, horizontal
  • North arrow + scale bar + lat/lon ticks on every panel
  • Times New Roman / DejaVu Serif serif font throughout
  • >85 % of canvas occupied by map panels
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
    setup_fonts,
    LAYOUT, FONT_SERIF,
    C_INC, C_DEC, C_NS, Z_VABS,
    build_axes,
    north_arrow, scale_bar, panel_letter, format_map_axes,
)
from .spatial_export_v5 import save_formats


# ── Internal helpers ──────────────────────────────────────────────────────────

def _draw_province(ax, polys, zorder: int = 5) -> None:
    """Draw all boundary polygons (district outlines → province boundary)."""
    for pts in polys:
        ax.plot(pts[:, 0], pts[:, 1],
                color=LAYOUT["poly_color"], lw=LAYOUT["poly_lw"],
                solid_capstyle="round", zorder=zorder)


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


def _draw_panel(
    ax, polys, gl, gt, mask, zz,
    cmap, vmin, vmax,
    lons, lats, z_vals, sig_arr,
    letter, title,
    xmin, xmax, ymin, ymax,
) -> None:
    """Render one map panel: surface + outlines + stations + decorations."""
    # Background surface
    zz_ma = np.ma.array(zz, mask=~mask)
    ax.imshow(
        zz_ma,
        extent=[xmin, xmax, ymin, ymax],
        origin="lower",
        cmap=cmap, vmin=vmin, vmax=vmax,
        interpolation="bilinear",
        aspect="auto", zorder=1,
    )

    # Province/district outlines
    _draw_province(ax, polys)

    # Station markers
    for lon, lat, z, sig in zip(lons, lats, z_vals, sig_arr):
        if np.isnan(z):
            continue
        if sig:
            marker, fc = ("^", C_INC) if z > 0 else ("v", C_DEC)
        else:
            marker, fc = "o", C_NS
        ax.scatter(lon, lat, marker=marker, s=LAYOUT["stn_size"],
                   c=fc, edgecolors="white", linewidths=0.4, zorder=7)

    # Cartographic decorations
    north_arrow(ax)
    scale_bar(ax, xmin, xmax, ymin, ymax, km=25)
    panel_letter(ax, letter)

    # Title and axes
    ax.set_title(title, fontsize=8, pad=3.5, fontfamily=FONT_SERIF)
    format_map_axes(ax, xmin, xmax, ymin, ymax)


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
    setup_fonts()

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

    spec = [
        ("MK_Z",   "MK_sig",   "Standard MK",      "(a)"),
        ("MMK_Z",  "MMK_sig",  "Mod. MK (H&R98)",  "(b)"),
        ("PW_Z",   "PW_sig",   "PW-MK",            "(c)"),
        ("TFPW_Z", "TFPW_sig", "TFPW-MK",          "(d)"),
    ]

    grids: dict[str, np.ndarray] = {}
    sigs:  dict[str, np.ndarray] = {}

    for col, sig_col, _, _ in spec:
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

    # ── Colormap bounds ───────────────────────────────────────────────────────
    cmap_z = matplotlib.colormaps["RdBu_r"].copy()
    cmap_z.set_bad("white")

    cmap_s = matplotlib.colormaps["RdYlGn"].copy()
    cmap_s.set_bad("white")
    fin_s  = grids["slope"][mask & np.isfinite(grids["slope"])]
    slp_abs = float(np.ceil(max(np.abs(fin_s).max() if len(fin_s) else 5, 5) / 5) * 5)

    # ── Figure ────────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(LAYOUT["fig_w"], LAYOUT["fig_h"]))
    ax_a, ax_b, ax_c, ax_d, ax_e, ax_cz, ax_cs = build_axes(fig)

    common = dict(polys=polys, gl=gl, gt=gt, mask=mask,
                  lons=lons, lats=lats,
                  xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

    _draw_panel(ax_a, cmap=cmap_z, vmin=-Z_VABS, vmax=Z_VABS,
                zz=grids["MK_Z"],   z_vals=df["MK_Z"].values,
                sig_arr=sigs["MK_Z"],
                letter="(a)", title="Standard MK — Z Statistic", **common)

    _draw_panel(ax_b, cmap=cmap_z, vmin=-Z_VABS, vmax=Z_VABS,
                zz=grids["MMK_Z"],  z_vals=df["MMK_Z"].values,
                sig_arr=sigs["MMK_Z"],
                letter="(b)", title="Modified MK (H&R 1998) — Z Statistic", **common)

    _draw_panel(ax_c, cmap=cmap_z, vmin=-Z_VABS, vmax=Z_VABS,
                zz=grids["PW_Z"],   z_vals=df["PW_Z"].values,
                sig_arr=sigs["PW_Z"],
                letter="(c)", title="PW-MK (Yue & Wang 2004) — Z Statistic", **common)

    _draw_panel(ax_d, cmap=cmap_z, vmin=-Z_VABS, vmax=Z_VABS,
                zz=grids["TFPW_Z"], z_vals=df["TFPW_Z"].values,
                sig_arr=sigs["TFPW_Z"],
                letter="(d)", title="TFPW-MK (Yue et al. 2002) — Z Statistic", **common)

    _draw_panel(ax_e, cmap=cmap_s, vmin=-slp_abs, vmax=slp_abs,
                zz=grids["slope"],  z_vals=slope_v,
                sig_arr=slope_sig,
                letter="(e)", title="Sen's Slope  (mm yr⁻¹)", **common)

    # ── Z colorbar (shared, left half) ───────────────────────────────────────
    norm_z = mcolors.Normalize(vmin=-Z_VABS, vmax=Z_VABS)
    sm_z   = plt.cm.ScalarMappable(cmap=cmap_z, norm=norm_z)
    sm_z.set_array([])
    cbar_z = fig.colorbar(sm_z, cax=ax_cz, orientation="horizontal")
    cbar_z.set_label("Z Statistic  (panels a–d)", fontsize=7.5,
                     fontfamily=FONT_SERIF)
    cbar_z.ax.tick_params(labelsize=6.5)
    # Mark critical thresholds
    for zv, ls in [(-1.960, "--"), (1.960, "--"), (-2.576, ":"), (2.576, ":")]:
        if -Z_VABS < zv < Z_VABS:
            norm_pos = (zv - (-Z_VABS)) / (2 * Z_VABS)
            cbar_z.ax.axvline(norm_pos, color="#222222", lw=0.85, ls=ls)
    # Threshold labels
    cbar_z.ax.text(
        (1.96 + Z_VABS) / (2 * Z_VABS) + 0.008, 0.5,
        "±1.96", va="center", fontsize=5.0, color="#333333",
        transform=cbar_z.ax.transAxes,
    )

    # ── Slope colorbar (right half) ───────────────────────────────────────────
    norm_s = mcolors.Normalize(vmin=-slp_abs, vmax=slp_abs)
    sm_s   = plt.cm.ScalarMappable(cmap=cmap_s, norm=norm_s)
    sm_s.set_array([])
    cbar_s = fig.colorbar(sm_s, cax=ax_cs, orientation="horizontal")
    cbar_s.set_label("Sen's Slope  (mm yr⁻¹, panel e)", fontsize=7.5,
                     fontfamily=FONT_SERIF)
    cbar_s.ax.tick_params(labelsize=6.5)

    # ── Title (one compact line) ──────────────────────────────────────────────
    scale_short = {
        "Annual (Jan–Dec)":   "Annual (Jan–Dec)",
        "Wet Season (May–Oct)": "Wet Season (May–Oct)",
        "Dry Season (Nov–Apr)": "Dry Season (Nov–Apr)",
    }.get(scale_key, scale_key)

    fig.suptitle(
        f"Spatial Rainfall Trend Distribution — {scale_short}  |  {period}",
        fontsize=9.5, fontfamily=FONT_SERIF, y=0.981,
    )

    # ── Save ──────────────────────────────────────────────────────────────────
    out_dir = Path(out_dir)
    save_formats(fig, out_dir, stem, dpi)
    plt.close(fig)

    return loocv_rows, best_name, all_metrics
