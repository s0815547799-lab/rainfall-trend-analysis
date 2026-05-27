"""
rta.spatial_publication_q1 — Q1 publication-grade spatial trend maps.

Generates Fig_Q1_SpatialTrend with 5 panels per temporal scale:
  (a) Standard MK      Z-statistic
  (b) Modified MK      Z-statistic  (Hamed & Rao 1998)
  (c) PW-MK            Z-statistic  (Yue & Wang 2004)
  (d) TFPW-MK          Z-statistic  (Yue et al. 2002)
  (e) Sen's Slope      mm yr⁻¹

Province boundary is loaded exclusively from the supplied shapefile —
no convex-hull or bounding-box fallback is used.

Interpolation background: best of IDW / RBF selected by LOOCV RMSE.
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
import matplotlib.patches as mpatches

from .spatial_interpolation import (
    make_boundary_mask,
    idw_interpolate,
    rbf_interpolate,
    loocv,
    select_best,
    load_boundary,
    save_validation_tables,
)

# ── Constants ─────────────────────────────────────────────────────────────────
_PROVINCE_PAD = 0.18   # degrees of padding around province bbox
_GRID_N       = 120    # interpolation grid size (NxN)
_Z_ABS        = 2.6    # colormap Z saturation  (≈ Z_0.01 = 2.576)

_C_INC  = "#1B5E20"    # dark green — significant increasing
_C_DEC  = "#B71C1C"    # dark red   — significant decreasing
_C_NS   = "#78909C"    # grey       — not significant

_SCALE_MAP = {
    "annual": "Annual (Jan–Dec)",
    "wet":    "Wet Season (May–Oct)",
    "dry":    "Dry Season (Nov–Apr)",
}
_SCALE_SUFFIX = {
    "Annual (Jan–Dec)":   "",
    "Wet Season (May–Oct)": "_Wet",
    "Dry Season (Nov–Apr)": "_Dry",
}


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Internal helpers                                                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def _draw_province(ax, polys, lw=0.65, color="#2a2a2a", zorder=5):
    for pts in polys:
        ax.plot(pts[:, 0], pts[:, 1],
                color=color, lw=lw, solid_capstyle="round", zorder=zorder)


def _north_arrow(ax, x=0.91, y=0.86, length=0.09, fontsize=6.5):
    ax.annotate(
        "", xy=(x, y + length), xytext=(x, y),
        xycoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color="#111111",
                        lw=1.0, mutation_scale=8),
    )
    ax.text(x, y + length + 0.025, "N",
            transform=ax.transAxes, ha="center", va="bottom",
            fontsize=fontsize, fontweight="bold", color="#111111", zorder=10)


def _scale_bar(ax, xmin, xmax, ymin, ymax, km=25):
    lat_c      = (ymin + ymax) / 2.0
    dlon_per_km = 1.0 / (111.32 * np.cos(np.radians(lat_c)))
    bar_lon     = km * dlon_per_km
    x0 = xmin + 0.06 * (xmax - xmin)
    y0 = ymin + 0.04 * (ymax - ymin)
    x1 = x0 + bar_lon
    dy = 0.009 * (ymax - ymin)
    ax.plot([x0, x1], [y0, y0], color="#111111", lw=2.0,
            solid_capstyle="butt", zorder=9)
    for xx in (x0, x1):
        ax.plot([xx, xx], [y0 - dy, y0 + dy], color="#111111", lw=1.2, zorder=9)
    ax.text((x0 + x1) / 2, y0 + 1.8 * dy,
            f"{km} km", ha="center", va="bottom",
            fontsize=5.5, color="#111111", zorder=9)


def _panel_letter(ax, letter, fontsize=9.5):
    ax.text(0.02, 0.98, letter,
            transform=ax.transAxes, ha="left", va="top",
            fontsize=fontsize, fontweight="bold", color="#111111", zorder=11,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))


def _plot_map_panel(ax, polys, gl, gt, mask,
                    zz, cmap, vmin, vmax,
                    lons, lats, z_vals, sig_arr,
                    codes, letter, title,
                    xmin, xmax, ymin, ymax):
    """
    Draw one spatial map panel: interpolated background + province
    outlines + station markers + decorations.
    """
    # Background: masked interpolated surface via imshow
    zz_ma = np.ma.array(zz, mask=~mask)
    ax.imshow(
        zz_ma,
        extent=[xmin, xmax, ymin, ymax],
        origin="lower", cmap=cmap, vmin=vmin, vmax=vmax,
        interpolation="bilinear", aspect="auto", zorder=1,
    )

    # Province / district outlines
    _draw_province(ax, polys, zorder=5)

    # Station markers
    for lon, lat, z, sig in zip(lons, lats, z_vals, sig_arr):
        if np.isnan(z):
            continue
        if sig:
            marker = "^" if z > 0 else "v"
            fc     = _C_INC if z > 0 else _C_DEC
        else:
            marker = "o"
            fc     = _C_NS
        ax.scatter(lon, lat, marker=marker, s=55, c=fc,
                   edgecolors="white", linewidths=0.4, zorder=7)

    # Station codes (tiny offset labels)
    if codes is not None:
        offsets = {"x": 0.022, "y": 0.022}
        for lon, lat, code in zip(lons, lats, codes):
            ax.text(lon + offsets["x"], lat + offsets["y"], code,
                    fontsize=4.5, ha="left", va="bottom",
                    color="#111111", zorder=8,
                    bbox=dict(boxstyle="round,pad=0.07",
                              fc="white", ec="none", alpha=0.55))

    # Cartographic decorations
    _north_arrow(ax)
    _scale_bar(ax, xmin, xmax, ymin, ymax, km=25)

    # Panel letter
    _panel_letter(ax, letter)

    # Title
    ax.set_title(title, fontsize=7.5, pad=3.5,
                 fontfamily="DejaVu Serif")

    # Axis formatting
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    lon_ticks = np.arange(np.ceil(xmin / 0.5) * 0.5,
                          xmax + 0.001, 0.5)
    lat_ticks = np.arange(np.ceil(ymin / 0.5) * 0.5,
                          ymax + 0.001, 0.5)
    ax.set_xticks(lon_ticks)
    ax.set_yticks(lat_ticks)
    ax.set_xticklabels([f"{v:.1f}°E" for v in lon_ticks], fontsize=5.5)
    ax.set_yticklabels([f"{v:.1f}°N" for v in lat_ticks], fontsize=5.5)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.5)
    ax.spines["bottom"].set_linewidth(0.5)
    ax.tick_params(width=0.5, length=2)

    ax.set_facecolor("white")

    return ax


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Public figure function                                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def fig_q1_spatial_trend(
    comp4_df:   pd.DataFrame,
    coords_df:  pd.DataFrame,
    shp_path:   str | Path,
    out_dir:    str | Path,
    prefix:     str,
    period:     str,
    scale_key:  str = "Annual (Jan–Dec)",
    dpi:        int = 600,
) -> tuple[list[dict], str, dict]:
    """
    5-panel Q1 publication spatial trend map for one temporal scale.

    Layout
    ------
    (a) Standard MK  │ (b) Modified MK  │ (c) PW-MK
    (d) TFPW-MK      │ (e) Sen's Slope  │ [legend]
    [────── Z colorbar ──────]  [Slope cbar]

    Parameters
    ----------
    comp4_df   : DataFrame from S7 4-Method Comparison sheet (header=1)
    coords_df  : DataFrame with columns Station, Lat, Lon
    shp_path   : path to province shapefile (.shp)
    out_dir    : output directory
    prefix     : filename prefix (no trailing underscore)
    period     : period label for figure title (e.g. "1981–2014")
    scale_key  : one of the Scale column values in comp4_df
    dpi        : output resolution

    Returns
    -------
    loocv_rows   : list[dict] for LOOCV.xlsx export
    best_method  : 'IDW' | 'RBF'
    all_metrics  : {method: {RMSE, MAE, Bias, R2}}
    """
    # ── Load boundary ─────────────────────────────────────────────────────
    polys = load_boundary(shp_path)

    # ── Province map extent ───────────────────────────────────────────────
    all_pts = np.vstack(polys)
    P = _PROVINCE_PAD
    xmin = all_pts[:, 0].min() - P
    xmax = all_pts[:, 0].max() + P
    ymin = all_pts[:, 1].min() - P
    ymax = all_pts[:, 1].max() + P

    # ── Filter scale ──────────────────────────────────────────────────────
    df = comp4_df[comp4_df["Scale"] == scale_key].copy()
    if df.empty:
        raise ValueError(
            f"No rows found for scale '{scale_key}'. "
            f"Available: {comp4_df['Scale'].unique().tolist()}"
        )
    stns = df["Station"].astype(str).values

    # ── Station coordinates ───────────────────────────────────────────────
    cd = dict(zip(
        coords_df["Station"].astype(str),
        zip(coords_df["Lon"].astype(float), coords_df["Lat"].astype(float)),
    ))
    lons = np.array([cd[s][0] for s in stns])
    lats = np.array([cd[s][1] for s in stns])
    pts  = np.column_stack([lons, lats])
    codes = [f"S{i+1:02d}" for i in range(len(stns))]

    # ── Build grid and province mask ──────────────────────────────────────
    gl_1d = np.linspace(xmin, xmax, _GRID_N)
    gt_1d = np.linspace(ymin, ymax, _GRID_N)
    gl, gt = np.meshgrid(gl_1d, gt_1d)
    xi     = np.column_stack([gl.ravel(), gt.ravel()])
    mask   = make_boundary_mask(gl, gt, polys)

    # ── Select best interpolation method via LOOCV (on MMK_Z) ────────────
    mmk_z  = df["MMK_Z"].values.astype(float)
    ok_idx = ~np.isnan(mmk_z)
    if ok_idx.sum() >= 4:
        _, best_name, all_metrics = select_best(
            pts[ok_idx], mmk_z[ok_idx], gl, gt, xi
        )
    else:
        best_name   = "IDW"
        all_metrics = {}
    print(f"    Interpolation method selected: {best_name}")

    def _interp(vals: np.ndarray) -> np.ndarray:
        v  = vals.astype(float)
        ok = ~np.isnan(v)
        if ok.sum() < 3:
            return np.full(gl.shape, np.nan)
        if best_name == "RBF":
            return rbf_interpolate(pts[ok], v[ok], xi).reshape(gl.shape)
        return idw_interpolate(pts[ok], v[ok], xi).reshape(gl.shape)

    def _masked(zz: np.ndarray) -> np.ndarray:
        out = zz.copy().astype(float)
        out[~mask] = np.nan
        return out

    # ── Interpolate all variables + collect LOOCV rows ───────────────────
    loocv_rows: list[dict] = []

    spec = [
        ("MK_Z",     "Standard MK",     "MK_sig"),
        ("MMK_Z",    "Modified MK",     "MMK_sig"),
        ("PW_Z",     "PW-MK",           "PW_sig"),
        ("TFPW_Z",   "TFPW-MK",         "TFPW_sig"),
    ]

    grids: dict[str, np.ndarray] = {}
    sigs:  dict[str, np.ndarray] = {}

    for col, mname, sig_col in spec:
        v  = df[col].values.astype(float)
        ok = ~np.isnan(v)
        cv = loocv(pts[ok], v[ok], best_name)
        loocv_rows.append({"Scale": scale_key, "Variable": col,
                           "Interp_Method": best_name, **cv})
        grids[col] = _masked(_interp(v))
        sigs[col]  = np.array([str(s) in ("*", "**")
                                for s in df[sig_col].values])

    # Sen's slope (use MK_slope as canonical)
    slope_v  = df["MK_slope"].values.astype(float)
    ok_s     = ~np.isnan(slope_v)
    cv_s     = loocv(pts[ok_s], slope_v[ok_s], best_name)
    loocv_rows.append({"Scale": scale_key, "Variable": "Sen_Slope",
                       "Interp_Method": best_name, **cv_s})
    grids["slope"] = _masked(_interp(slope_v))
    slope_sig      = np.array([str(s) in ("*", "**")
                                for s in df["MK_sig"].values])

    # ── Colormap bounds ───────────────────────────────────────────────────
    cmap_z = matplotlib.colormaps["RdBu_r"].copy()
    cmap_z.set_bad("white")
    vz_min, vz_max = -_Z_ABS, _Z_ABS

    cmap_s = matplotlib.colormaps["RdYlGn"].copy()
    cmap_s.set_bad("white")
    finite_slope = grids["slope"][mask & np.isfinite(grids["slope"])]
    if len(finite_slope) > 0:
        slp_abs = float(np.ceil(max(np.abs(finite_slope).max(), 5.0) / 5) * 5)
    else:
        slp_abs = 15.0
    vs_min, vs_max = -slp_abs, slp_abs

    # ── Figure ────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(11, 10.5))

    gs = fig.add_gridspec(
        3, 3,
        hspace=0.32, wspace=0.20,
        left=0.06, right=0.97, top=0.925, bottom=0.08,
        height_ratios=[1, 1, 0.055],
    )

    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[0, 2])
    ax_d = fig.add_subplot(gs[1, 0])
    ax_e = fig.add_subplot(gs[1, 1])
    ax_f = fig.add_subplot(gs[1, 2])   # legend
    ax_cz = fig.add_subplot(gs[2, 0:2])  # Z colorbar
    ax_cs = fig.add_subplot(gs[2, 2])    # slope colorbar

    common = dict(
        polys=polys, gl=gl, gt=gt, mask=mask,
        lons=lons, lats=lats, codes=codes,
        xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
    )

    _plot_map_panel(ax_a, **common,
        zz=grids["MK_Z"], cmap=cmap_z, vmin=vz_min, vmax=vz_max,
        z_vals=df["MK_Z"].values, sig_arr=sigs["MK_Z"],
        letter="(a)", title="Standard MK — Z Statistic")

    _plot_map_panel(ax_b, **common,
        zz=grids["MMK_Z"], cmap=cmap_z, vmin=vz_min, vmax=vz_max,
        z_vals=df["MMK_Z"].values, sig_arr=sigs["MMK_Z"],
        letter="(b)", title="Modified MK (H&R 1998) — Z Statistic")

    _plot_map_panel(ax_c, **common,
        zz=grids["PW_Z"], cmap=cmap_z, vmin=vz_min, vmax=vz_max,
        z_vals=df["PW_Z"].values, sig_arr=sigs["PW_Z"],
        letter="(c)", title="PW-MK (Yue & Wang 2004) — Z Statistic")

    _plot_map_panel(ax_d, **common,
        zz=grids["TFPW_Z"], cmap=cmap_z, vmin=vz_min, vmax=vz_max,
        z_vals=df["TFPW_Z"].values, sig_arr=sigs["TFPW_Z"],
        letter="(d)", title="TFPW-MK (Yue et al. 2002) — Z Statistic")

    _plot_map_panel(ax_e, **common,
        zz=grids["slope"], cmap=cmap_s, vmin=vs_min, vmax=vs_max,
        z_vals=slope_v, sig_arr=slope_sig,
        letter="(e)", title="Sen's Slope (mm yr⁻¹)")

    # ── Legend panel ──────────────────────────────────────────────────────
    ax_f.axis("off")
    handles = [
        mpatches.Patch(color=_C_INC, label="Increasing  (p < 0.05)"),
        mpatches.Patch(color=_C_DEC, label="Decreasing  (p < 0.05)"),
        mpatches.Patch(color=_C_NS,  label="Not significant"),
    ]
    ax_f.legend(
        handles=handles,
        loc="upper center",
        fontsize=8,
        frameon=True, framealpha=0.9, edgecolor="#cccccc",
        title="Trend Classification", title_fontsize=8.5,
        handlelength=1.4,
    )

    # Method note
    ax_f.text(0.5, 0.25,
              f"Interpolation: {best_name}\n"
              f"Grid: {_GRID_N}×{_GRID_N}\n"
              f"Stations: {len(stns)}\n"
              f"LOOCV RMSE (Z): {_loocv_rmse(loocv_rows, 'MMK_Z'):.3f}",
              transform=ax_f.transAxes, ha="center", va="center",
              fontsize=7, style="italic", color="#444444",
              bbox=dict(boxstyle="round,pad=0.4", fc="#f9f9f9",
                        ec="#cccccc", alpha=0.9))

    # ── Z colorbar ────────────────────────────────────────────────────────
    norm_z = mcolors.Normalize(vmin=vz_min, vmax=vz_max)
    sm_z   = plt.cm.ScalarMappable(cmap=cmap_z, norm=norm_z)
    sm_z.set_array([])
    cbar_z = fig.colorbar(sm_z, cax=ax_cz, orientation="horizontal")
    cbar_z.set_label("Z Statistic", fontsize=7.5)
    cbar_z.ax.tick_params(labelsize=6.5)
    # Significance thresholds
    for zv, style in [(-1.96, "--"), (1.96, "--"), (-2.576, ":"), (2.576, ":")]:
        if vz_min < zv < vz_max:
            norm_pos = (zv - vz_min) / (vz_max - vz_min)
            cbar_z.ax.axvline(norm_pos, color="k", lw=0.9, ls=style)
    cbar_z.ax.text(
        (1.96 - vz_min) / (vz_max - vz_min) + 0.01, 0.5,
        "±1.96", va="center", fontsize=5.5, color="#333333",
        transform=cbar_z.ax.transAxes,
    )

    # ── Slope colorbar ────────────────────────────────────────────────────
    norm_s = mcolors.Normalize(vmin=vs_min, vmax=vs_max)
    sm_s   = plt.cm.ScalarMappable(cmap=cmap_s, norm=norm_s)
    sm_s.set_array([])
    cbar_s = fig.colorbar(sm_s, cax=ax_cs, orientation="horizontal")
    cbar_s.set_label("Sen's Slope  (mm yr⁻¹)", fontsize=7.5)
    cbar_s.ax.tick_params(labelsize=6.5)

    # ── Figure title ──────────────────────────────────────────────────────
    scale_labels = {
        "Annual (Jan–Dec)":   "Annual (Jan–Dec)",
        "Wet Season (May–Oct)": "Wet Season (May–Oct)",
        "Dry Season (Nov–Apr)": "Dry Season (Nov–Apr)",
    }
    scale_label = scale_labels.get(scale_key, scale_key)
    fig.suptitle(
        f"Spatial Distribution of Rainfall Trends — {scale_label}  |  {period}\n"
        f"Prachuap Khiri Khan Province, Western Thailand  "
        f"(IDW / RBF interpolation via LOOCV; boundary: official province shapefile)",
        fontsize=9, fontfamily="DejaVu Serif", y=0.975,
    )

    # ── Save ──────────────────────────────────────────────────────────────
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    suffix = _SCALE_SUFFIX.get(scale_key, "")
    stem   = f"{prefix}_Fig_Q1_SpatialTrend{suffix}"

    _save_formats(fig, out_dir, stem, dpi)
    plt.close(fig)

    return loocv_rows, best_name, all_metrics


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Helpers                                                                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def _loocv_rmse(rows: list[dict], variable: str) -> float:
    for r in rows:
        if r.get("Variable") == variable:
            v = r.get("RMSE", float("nan"))
            return float(v) if v is not None else float("nan")
    return float("nan")


def _save_formats(fig, out_dir: Path, stem: str, dpi: int) -> None:
    formats = [
        ("png", {"dpi": dpi}),
        ("tif", {"dpi": dpi, "pil_kwargs": {"compression": "tiff_lzw"}}),
        ("pdf", {"dpi": dpi}),
        ("svg", {}),
    ]
    for fmt, kw in formats:
        path = out_dir / f"{stem}.{fmt}"
        try:
            fig.savefig(path, format=fmt, bbox_inches="tight", **kw)
            print(f"    ✓ {path.name}")
        except Exception as exc:
            warnings.warn(f"Could not save {fmt.upper()}: {exc}")


def write_spatial_manuscript(
    loocv_all:  list[dict],
    best_method: str,
    all_metrics: dict,
    out_dir:    Path,
    prefix:     str,
    period:     str,
    n_stations: int,
    scale_key:  str = "Annual (Jan–Dec)",
) -> None:
    """
    Write Spatial_Methods_Q1.md — methods & results text for the
    spatial interpolation section of the manuscript.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "Spatial_Methods_Q1.md"

    mmk_row = next((r for r in loocv_all
                    if r.get("Variable") == "MMK_Z"
                    and r.get("Scale") == scale_key), None)
    slope_row = next((r for r in loocv_all
                      if r.get("Variable") == "Sen_Slope"
                      and r.get("Scale") == scale_key), None)

    def _fmt(d, key):
        v = d.get(key, float("nan")) if d else float("nan")
        try:
            return f"{float(v):.4f}"
        except Exception:
            return "n/a"

    lines = [
        "# Spatial Interpolation Methods — Q1 Publication Notes",
        "",
        f"**Analysis period:** {period}",
        f"**Province:** Prachuap Khiri Khan, Western Thailand",
        f"**Stations:** {n_stations}",
        f"**Boundary source:** Official province shapefile "
        f"(30_amarea_prachuap_khiri_khan.shp, polygon type)",
        "",
        "## 2.5 Spatial Interpolation",
        "",
        "Spatially continuous rainfall trend fields were estimated by interpolating "
        "station-level Mann–Kendall Z statistics and Sen's slope estimates onto a "
        f"{_GRID_N}×{_GRID_N} regular grid covering the province extent. "
        "Two methods were evaluated:",
        "",
        "**Inverse-Distance Weighting (IDW, power = 2):** A deterministic method "
        "assigning weights proportional to the reciprocal squared distance from each "
        "query point to the data stations (Shepard, 1968).",
        "",
        "**Radial-Basis Function (RBF, thin-plate spline, smoothing = 0.5):** "
        "A kernel-based interpolant fitted via `scipy.interpolate.RBFInterpolator`; "
        "the thin-plate spline kernel minimises bending energy and provides smooth "
        "gradients (Wahba, 1990).",
        "",
        "Method selection used Leave-One-Out Cross-Validation (LOOCV). "
        "At each iteration, one station is withheld, the surface is refit on the "
        "remaining n−1 stations, and the withheld value is predicted. "
        "The method with the lower root-mean-square error (RMSE) was applied "
        "for all variables and scales.",
        "",
        f"**Selected method: {best_name}**",
        "",
        "### LOOCV Results — Annual Scale",
        "",
        "| Variable | RMSE | MAE | Bias | R² |",
        "|----------|------|-----|------|-----|",
    ]

    for row in loocv_all:
        if row.get("Scale") == scale_key:
            lines.append(
                f"| {row.get('Variable','?')} | "
                f"{_fmt(row,'RMSE')} | {_fmt(row,'MAE')} | "
                f"{_fmt(row,'Bias')} | {_fmt(row,'R2')} |"
            )

    lines += [
        "",
        "### IDW vs RBF comparison (reference variable: MMK_Z)",
        "",
        "| Method | RMSE | MAE | Bias | R² |",
        "|--------|------|-----|------|-----|",
    ]
    for mname, mets in all_metrics.items():
        lines.append(
            f"| {mname} | "
            f"{_fmt(mets,'RMSE')} | {_fmt(mets,'MAE')} | "
            f"{_fmt(mets,'Bias')} | {_fmt(mets,'R2')} |"
        )

    lines += [
        "",
        "## References",
        "",
        "- Shepard, D. (1968). A two-dimensional interpolation function for "
        "irregularly-spaced data. *Proc. 23rd ACM National Conference*, 517–524.",
        "- Wahba, G. (1990). *Spline Models for Observational Data*. "
        "SIAM, Philadelphia.",
        "- Mann, H.B. (1945). Non-parametric tests against trend. "
        "*Econometrica*, 13, 245–259.",
        "- Kendall, M.G. (1975). *Rank Correlation Methods* (4th ed.). "
        "Griffin, London.",
        "- Hamed, K.H. & Rao, A.R. (1998). A modified Mann–Kendall trend test "
        "for autocorrelated data. *Journal of Hydrology*, 204, 182–196.",
        "- Yue, S. & Wang, C. (2004). The Mann–Kendall test modified by effective "
        "sample size to detect trend in serially correlated hydrological series. "
        "*Water Resources Research*, 40, W08307.",
        "- Yue, S., Pilon, P., Phinney, B. & Cavadias, G. (2002). The influence "
        "of autocorrelation on the ability to detect trend in hydrological series. "
        "*Hydrological Processes*, 16, 1807–1829.",
        "- Sen, P.K. (1968). Estimates of the regression coefficient based on "
        "Kendall's tau. *JASA*, 63, 1379–1389.",
        "",
        "---",
        f"*Generated automatically by rta.spatial_publication_q1 "
        f"from results/final_N33/ publication archive.*",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"    ✓ {path.name}")


# expose best_name at module level for write_spatial_manuscript caller
best_name = "IDW"
