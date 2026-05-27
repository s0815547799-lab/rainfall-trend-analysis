"""
rta.figures.spatial_maps — True geographic spatial trend maps.

Public functions
----------------
fig_station_distribution  — station location map with altitude colouring
fig_spatial_methods       — 4×3 method × scale geographic bubble maps
fig_spatial_field_sig     — field significance geographic summary
fig14_spatial_maps        — compact 3-panel MMK map (backward-compatible)
fig_spatial_full          — comprehensive 7-panel overview (all maps)
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
from pathlib import Path
from ..config import (C, DPI, SAVE_PDF, SCALE_META, Z_005, Z_001,
                      ALPHA_005, savefig)


# ── Shared constants ──────────────────────────────────────────────────────────
_SCALE_ORDER = ["annual", "wet", "dry"]
_SCALE_LABEL = {"annual": "Annual", "wet": "Wet Season", "dry": "Dry Season"}
_METHODS     = ["Standard MK", "Modified MK", "PW-MK", "TFPW-MK"]
_METHOD_SHORT = {
    "Standard MK": "MK",
    "Modified MK": "MMK",
    "Modified MK (H&R98)": "MMK",
    "PW-MK":  "PW",
    "TFPW-MK": "TFPW",
}
_PANEL_ALPHA = list("abcdefghijklmnopqr")

# CRS assumption banner
_CRS_NOTE = "CRS: WGS84 assumed (EPSG:4326)"


# ── Private helpers ───────────────────────────────────────────────────────────

def _bubble_size(slope_abs: float, max_slope: float,
                 s_min: float = 50.0, s_range: float = 250.0) -> float:
    if max_slope <= 0:
        return s_min
    return s_min + s_range * float(slope_abs) / float(max_slope)


def _trend_color(sig05: bool, z_val: float) -> str:
    if bool(sig05) and float(z_val) > 0:
        return C["inc"]
    if bool(sig05) and float(z_val) < 0:
        return C["dec"]
    return C["ns_col"]


def _geo_pad(xs, ys, frac=0.12, min_pad=0.05):
    if not xs or not ys:
        return min_pad, min_pad
    x_pad = max((max(xs) - min(xs)) * frac, min_pad)
    y_pad = max((max(ys) - min(ys)) * frac, min_pad)
    return x_pad, y_pad


def _draw_compass(ax, xy=(0.95, 0.95)):
    ax.annotate("N↑", xy=xy, xycoords="axes fraction",
                fontsize=11, ha="right", va="top",
                fontweight="bold", color="#212121",
                bbox=dict(boxstyle="round,pad=0.2", fc="white",
                          ec="#BDBDBD", lw=0.7))


def _draw_scale_bar(ax, xs, ys, frac=0.25):
    """Draw a simple distance scale bar using 1° ≈ 111 km approximation."""
    x_span  = max(xs) - min(xs)
    y_bot   = min(ys) - (max(ys) - min(ys)) * 0.08
    bar_deg = round(x_span * frac, 2)
    bar_km  = round(bar_deg * 111 * math.cos(math.radians(np.mean(ys))))
    x0 = min(xs)
    ax.plot([x0, x0 + bar_deg], [y_bot, y_bot], color="black", lw=2.0)
    ax.text(x0 + bar_deg / 2, y_bot - (max(ys) - min(ys)) * 0.035,
            f"{bar_km} km", ha="center", va="top", fontsize=7.5)


def _geo_axes(ax, xs, ys):
    """Standard geographic axis formatting."""
    x_pad, y_pad = _geo_pad(xs, ys)
    ax.set_xlim(min(xs) - x_pad, max(xs) + x_pad)
    ax.set_ylim(min(ys) - y_pad, max(ys) + y_pad)
    ax.set_xlabel("Longitude (°E)", fontsize=10)
    ax.set_ylabel("Latitude (°N)",  fontsize=10)
    ax.xaxis.set_major_formatter(ticker.FormatStrFormatter("%.2f°"))
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.2f°"))
    ax.grid(True, linestyle="--", linewidth=0.35, alpha=0.40, color="#B0BEC5")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _draw_compass(ax)


def _get_slope_dict(trend_df, method, scale):
    """Return {station: (slope_Q, Z, sig_05)} for a given method & scale."""
    method_keys = [method]
    if method == "Modified MK":
        method_keys.append("Modified MK (H&R98)")
    sub = trend_df[
        (trend_df["Scale"].str.lower() == scale.lower()) &
        (trend_df["Method"].isin(method_keys))
    ]
    result = {}
    for _, row in sub.iterrows():
        stn   = str(row.get("Station", ""))
        slope = float(row.get("Slope_Q", np.nan)) if pd.notna(row.get("Slope_Q")) else np.nan
        z     = float(row.get("Z", 0.0))    if pd.notna(row.get("Z"))      else 0.0
        sig05 = bool(row.get("sig_05", False))
        result[stn] = (slope, z, sig05)
    return result


def _scatter_geo_panel(ax, stns, smap, coords, data_dict, global_max,
                       panel_label, title, show_legend=True):
    """Draw one geographic bubble panel."""
    xs, ys, sizes, colors, labels_plot = [], [], [], [], []

    for stn in stns:
        if stn not in coords:
            continue
        lat, lon = coords[stn]
        if stn in data_dict:
            slope, z_v, sig05 = data_dict[stn]
        else:
            slope, z_v, sig05 = np.nan, 0.0, False

        slope_abs = abs(slope) if pd.notna(slope) else 0.0
        xs.append(float(lon));  ys.append(float(lat))
        sizes.append(_bubble_size(slope_abs, global_max))
        colors.append(_trend_color(sig05, z_v))
        labels_plot.append(smap.get(stn, stn))

    if xs:
        ax.scatter(xs, ys, s=sizes, c=colors,
                   edgecolors="black", linewidths=0.6,
                   zorder=4, alpha=0.88)
        for xi, yi, lbl in zip(xs, ys, labels_plot):
            ax.annotate(lbl, xy=(xi, yi), xytext=(3, 4),
                        textcoords="offset points",
                        fontsize=8, color="#212121", zorder=5)
        _geo_axes(ax, xs, ys)

    ax.set_title(f"({panel_label})  {title}", loc="left",
                 fontsize=10, fontweight="bold", pad=4)

    if show_legend:
        handles = [
            mpatches.Patch(facecolor=C["inc"],    edgecolor="k",
                           lw=0.6, label="Increasing (p<0.05)"),
            mpatches.Patch(facecolor=C["dec"],    edgecolor="k",
                           lw=0.6, label="Decreasing (p<0.05)"),
            mpatches.Patch(facecolor=C["ns_col"], edgecolor="k",
                           lw=0.6, label="Not significant"),
        ]
        ax.legend(handles=handles, fontsize=7, loc="lower left",
                  framealpha=0.85, handletextpad=0.4)


# ── Public figure functions ────────────────────────────────────────────────────

def fig_station_distribution(coords: dict, stns: list, smap: dict,
                              period: str, out_dir, prefix: str,
                              alt_dict: dict | None = None) -> None:
    """
    Geographic station distribution map with labels and optional altitude colouring.

    Parameters
    ----------
    coords   : {station: (lat, lon)}
    stns     : ordered station list
    smap     : {station: short_code}
    period   : study period string
    out_dir  : output directory
    prefix   : filename prefix
    alt_dict : optional {station: altitude_m}
    """
    stns = [str(s) for s in stns]
    xs   = [coords[s][1] for s in stns if s in coords]
    ys   = [coords[s][0] for s in stns if s in coords]

    if not xs:
        print(f"  ⚠ fig_station_distribution: no coordinate matches for stations "
              f"{stns[:3]}{'...' if len(stns)>3 else ''} — skipping")
        return

    fig, ax = plt.subplots(figsize=(9, 10))
    fig.subplots_adjust(left=0.10, right=0.92, top=0.90, bottom=0.09)

    # Background extent box
    x_pad, y_pad = _geo_pad(xs, ys, frac=0.15)
    ax.set_xlim(min(xs) - x_pad, max(xs) + x_pad)
    ax.set_ylim(min(ys) - y_pad, max(ys) + y_pad)

    if alt_dict:
        alts = [alt_dict.get(s, 0) for s in stns if s in coords]
        norm = mcolors.Normalize(vmin=0, vmax=max(alts) if alts else 200)
        cmap = cm.terrain
        sc   = ax.scatter(xs, ys, c=alts, cmap=cmap, norm=norm,
                          s=130, edgecolors="black", linewidths=0.7,
                          zorder=4, alpha=0.90)
        plt.colorbar(sc, ax=ax, orientation="vertical", pad=0.01,
                     shrink=0.65, label="Altitude (m asl)")
    else:
        ax.scatter(xs, ys, s=130, color=C["annual"],
                   edgecolors="black", linewidths=0.7,
                   zorder=4, alpha=0.90)

    # Labels
    for stn, xi, yi in zip([s for s in stns if s in coords], xs, ys):
        code = smap.get(stn, stn)
        ax.annotate(
            f"{code}\n({stn})", xy=(xi, yi), xytext=(6, 6),
            textcoords="offset points", fontsize=8.5,
            color="#212121", zorder=5,
            bbox=dict(boxstyle="round,pad=0.15", fc="white",
                      ec="#CFD8DC", alpha=0.75, lw=0.5)
        )

    # Geo formatting
    ax.set_xlabel("Longitude (°E)", fontsize=11)
    ax.set_ylabel("Latitude (°N)",  fontsize=11)
    ax.xaxis.set_major_formatter(ticker.FormatStrFormatter("%.2f°"))
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.2f°"))
    ax.grid(True, linestyle="--", linewidth=0.40, alpha=0.40, color="#B0BEC5")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _draw_compass(ax, xy=(0.97, 0.97))
    if len(xs) > 1:
        _draw_scale_bar(ax, xs, ys)

    ax.set_title(
        f"Study Area: Rainfall Station Network\n"
        f"Prachuap Khiri Khan Basin  |  {period}  |  N={len(xs)} stations\n"
        f"{_CRS_NOTE}",
        fontsize=12, fontweight="bold", loc="left", pad=8
    )
    savefig(fig, str(Path(out_dir) / f"{prefix}_Fig_SpatialStation"))


def fig_spatial_methods(trend_df: pd.DataFrame,
                         stns: list,
                         smap: dict,
                         coords: dict | None,
                         period: str,
                         out_dir,
                         prefix: str) -> None:
    """
    4×3 grid: 4 methods (MK, MMK, PW-MK, TFPW-MK) × 3 temporal scales.
    Each cell is a geographic bubble map (size ∝ |Sen's slope|, colour = trend).
    """
    stns = [str(s) for s in stns]
    if not coords:
        return

    all_slopes = pd.to_numeric(
        trend_df.get("Slope_Q", pd.Series(dtype=float)), errors="coerce"
    ).abs().dropna()
    global_max = float(all_slopes.max()) if len(all_slopes) > 0 else 1.0

    methods = [m for m in _METHODS if m in trend_df["Method"].unique() or
               (m == "Modified MK" and "Modified MK (H&R98)" in trend_df["Method"].unique())]

    n_m = len(methods)
    n_s = len(_SCALE_ORDER)

    fig, axes = plt.subplots(n_m, n_s, figsize=(6 * n_s, 5.5 * n_m))
    if n_m == 1:
        axes = axes[np.newaxis, :]
    fig.subplots_adjust(left=0.06, right=0.97, top=0.93,
                        bottom=0.06, hspace=0.50, wspace=0.30)

    panel_idx = 0
    for ri, method in enumerate(methods):
        for ci, scale in enumerate(_SCALE_ORDER):
            ax    = axes[ri, ci]
            label = _PANEL_ALPHA[panel_idx]; panel_idx += 1
            mshort = _METHOD_SHORT.get(method, method)
            title  = f"{_SCALE_LABEL[scale]} — {mshort}"
            data   = _get_slope_dict(trend_df, method, scale)
            show_leg = (ri == n_m - 1 and ci == 0)
            _scatter_geo_panel(ax, stns, smap, coords, data,
                               global_max, label, title, show_legend=show_leg)

    # Size-reference legend in first panel
    ax0 = axes[0, 0]
    ref_fracs  = [0.25, 0.50, 1.00]
    ref_labels = [f"|β| = {f*global_max:.1f} mm yr⁻¹" for f in ref_fracs]
    ref_handles = [
        Line2D([0],[0], marker="o", color="w",
               markerfacecolor=C["grey"], markeredgecolor="k",
               markersize=math.sqrt(_bubble_size(f*global_max, global_max)/math.pi),
               label=lbl)
        for f, lbl in zip(ref_fracs, ref_labels)
    ]
    ax0.legend(handles=ref_handles, fontsize=7, loc="lower left",
               framealpha=0.85, title="Bubble size", title_fontsize=7)

    fig.suptitle(
        f"Spatial Trend Maps — 4 Methods × 3 Temporal Scales  |  {period}\n"
        f"Bubble size ∝ |Sen's slope|  |  Colour = trend direction (p<0.05)\n"
        f"{_CRS_NOTE}",
        fontsize=12, fontweight="bold", y=0.985
    )
    savefig(fig, str(Path(out_dir) / f"{prefix}_Fig_SpatialMethods"))


def fig_spatial_field_sig(trend_df: pd.DataFrame,
                           field_sig_df: pd.DataFrame | None,
                           stns: list,
                           smap: dict,
                           coords: dict | None,
                           period: str,
                           out_dir,
                           prefix: str) -> None:
    """
    Field significance spatial summary:
    Left 3 panels — geographic Z-magnitude map per scale (MMK).
    Right panel  — Walker/LC p-value bar chart by scale.
    """
    stns = [str(s) for s in stns]
    if not coords:
        return

    fig = plt.figure(figsize=(20, 6))
    gs  = gridspec.GridSpec(1, 4, figure=fig, wspace=0.32,
                            left=0.05, right=0.97, top=0.88, bottom=0.14)
    axes_geo = [fig.add_subplot(gs[0, i]) for i in range(3)]
    ax_bar   = fig.add_subplot(gs[0, 3])

    # ── Geographic Z-magnitude panels (MMK) ──────────────────────────────────
    zmk_all = pd.to_numeric(
        trend_df[trend_df["Method"].isin(["Modified MK","Modified MK (H&R98)"])
        ].get("Z", pd.Series(dtype=float)), errors="coerce"
    ).abs().dropna()
    z_max = float(zmk_all.max()) if len(zmk_all) > 0 else 3.0

    for ci, scale in enumerate(_SCALE_ORDER):
        ax    = axes_geo[ci]
        lbl   = _PANEL_ALPHA[ci]
        data  = _get_slope_dict(trend_df, "Modified MK", scale)
        xs, ys, sizes_z, colors = [], [], [], []

        for stn in stns:
            if stn not in coords: continue
            lat, lon = coords[stn]
            slope, z_v, sig05 = data.get(stn, (np.nan, 0.0, False))
            z_abs = abs(z_v)
            xs.append(float(lon)); ys.append(float(lat))
            # Size proportional to |Z|
            sz = 50 + 200 * z_abs / max(z_max, 1.0)
            sizes_z.append(sz)
            colors.append(_trend_color(sig05, z_v))

        if xs:
            ax.scatter(xs, ys, s=sizes_z, c=colors,
                       edgecolors="black", linewidths=0.6,
                       zorder=4, alpha=0.88)
            for stn, xi, yi in zip([s for s in stns if s in coords], xs, ys):
                ax.annotate(smap.get(stn, stn), xy=(xi, yi), xytext=(3, 4),
                            textcoords="offset points", fontsize=7.5, zorder=5)
            _geo_axes(ax, xs, ys)

        # Significance threshold line annotation
        ax.set_title(f"({lbl})  {_SCALE_LABEL[scale]} |Z| (MMK)\n"
                     f"  Ring size ∝ |Z|  |  Z₀.₀₅ = {Z_005:.2f}",
                     loc="left", fontsize=9.5, fontweight="bold", pad=4)

    # ── Walker / LC bar chart ─────────────────────────────────────────────────
    if field_sig_df is not None and len(field_sig_df) > 0:
        scales_fs  = field_sig_df["Scale"].tolist()
        p_walker   = field_sig_df.get("Walker_p_MK",  pd.Series(dtype=float)).tolist()
        p_lc       = field_sig_df.get("LC_p_MK",      pd.Series(dtype=float)).tolist()
        x_pos      = np.arange(len(scales_fs))
        bw         = 0.35

        bar_w = ax_bar.bar(x_pos - bw/2, p_walker, width=bw,
                           color="#6A1B9A", alpha=0.78, label="Walker (1914)")
        bar_l = ax_bar.bar(x_pos + bw/2, p_lc,     width=bw,
                           color="#0277BD", alpha=0.78, label="LC-MC (1983)")
        ax_bar.axhline(0.05, color="red", lw=1.4, ls="--",
                       label="α = 0.05", zorder=5)

        for bar_grp in [bar_w, bar_l]:
            for bar in bar_grp:
                h = bar.get_height()
                ax_bar.text(bar.get_x() + bar.get_width()/2, h + 0.01,
                            f"{h:.3f}", ha="center", va="bottom",
                            fontsize=8, fontweight="bold")

        ax_bar.set_xticks(x_pos)
        ax_bar.set_xticklabels([_SCALE_LABEL.get(s, s) for s in scales_fs],
                               fontsize=10)
        ax_bar.set_ylim(0, max(max(p_walker + p_lc, default=0.2) * 1.25, 0.12))
        ax_bar.set_ylabel("Field-significance p-value", fontsize=10)
        ax_bar.set_title(f"(d)  Field Significance\n"
                         "Walker & Livezey-Chen MC",
                         loc="left", fontsize=10, fontweight="bold", pad=4)
        ax_bar.legend(fontsize=8, frameon=True, edgecolor="#B0BEC5")
        ax_bar.spines["top"].set_visible(False)
        ax_bar.spines["right"].set_visible(False)
    else:
        ax_bar.set_visible(False)

    fig.suptitle(
        f"Field Significance & Z-Magnitude Spatial Maps — MMK  |  {period}\n{_CRS_NOTE}",
        fontsize=12, fontweight="bold"
    )
    savefig(fig, str(Path(out_dir) / f"{prefix}_Fig_SpatialFieldSig"))


def fig_spatial_full(trend_df: pd.DataFrame,
                      stns: list,
                      smap: dict,
                      coords: dict | None,
                      field_sig_df: pd.DataFrame | None,
                      period: str,
                      out_dir,
                      prefix: str,
                      alt_dict: dict | None = None) -> None:
    """
    Comprehensive 7-panel spatial overview:
    (a) Station distribution
    (b) Annual MK
    (c) Annual MMK
    (d) Annual PW-MK
    (e) Annual TFPW-MK
    (f) Annual Sen's slope (colour = magnitude)
    (g) Field significance p-values
    """
    stns = [str(s) for s in stns]
    if not coords:
        return

    xs_all = [coords[s][1] for s in stns if s in coords]
    ys_all = [coords[s][0] for s in stns if s in coords]

    all_slopes = pd.to_numeric(
        trend_df.get("Slope_Q", pd.Series(dtype=float)), errors="coerce"
    ).abs().dropna()
    global_max = float(all_slopes.max()) if len(all_slopes) > 0 else 1.0

    fig = plt.figure(figsize=(22, 14))
    gs  = gridspec.GridSpec(2, 4, figure=fig,
                            hspace=0.50, wspace=0.30,
                            left=0.05, right=0.97, top=0.91, bottom=0.07)

    axes = [fig.add_subplot(gs[r, c]) for r in range(2) for c in range(4)]
    # 8 cells total; last cell used for field sig bar

    # ── Panel (a): Station distribution ──────────────────────────────────────
    ax = axes[0]
    if alt_dict:
        alts = [alt_dict.get(s, 0) for s in stns if s in coords]
        norm = mcolors.Normalize(vmin=0, vmax=max(alts) if alts else 200)
        cmap = cm.terrain
        sc   = ax.scatter(xs_all, ys_all, c=alts, cmap=cmap, norm=norm,
                          s=110, edgecolors="black", linewidths=0.6,
                          zorder=4, alpha=0.90)
        plt.colorbar(sc, ax=ax, orientation="vertical", pad=0.01,
                     shrink=0.65, label="Alt (m)")
    else:
        ax.scatter(xs_all, ys_all, s=110, color=C["annual"],
                   edgecolors="black", linewidths=0.6, zorder=4, alpha=0.90)
    for stn in stns:
        if stn not in coords: continue
        lat, lon = coords[stn]
        ax.annotate(smap.get(stn, stn), xy=(lon, lat), xytext=(3, 4),
                    textcoords="offset points", fontsize=8, zorder=5)
    if xs_all:
        _geo_axes(ax, xs_all, ys_all)
    ax.set_title("(a)  Station Distribution", loc="left",
                 fontsize=10, fontweight="bold", pad=4)

    # ── Panels (b–e): 4 methods, annual scale ────────────────────────────────
    methods_to_plot = []
    for m in _METHODS:
        m_keys = [m]
        if m == "Modified MK":
            m_keys.append("Modified MK (H&R98)")
        if any(k in trend_df["Method"].unique() for k in m_keys):
            methods_to_plot.append(m)
        if len(methods_to_plot) == 4:
            break

    for mi, method in enumerate(methods_to_plot[:4]):
        ax    = axes[1 + mi]
        lbl   = _PANEL_ALPHA[1 + mi]
        mshort = _METHOD_SHORT.get(method, method)
        data   = _get_slope_dict(trend_df, method, "annual")
        _scatter_geo_panel(ax, stns, smap, coords, data, global_max,
                           lbl, f"Annual — {mshort}", show_legend=(mi == 0))

    # ── Panel (f): Sen's slope magnitude heat-colour ──────────────────────────
    ax = axes[5]
    mmk_ann = _get_slope_dict(trend_df, "Modified MK", "annual")
    slopes_v = [mmk_ann.get(s, (np.nan,)*3)[0] for s in stns if s in coords]
    slopes_v_clean = [s for s in slopes_v if pd.notna(s)]
    s_min = min(slopes_v_clean) if slopes_v_clean else -10
    s_max = max(slopes_v_clean) if slopes_v_clean else 10
    vabs  = max(abs(s_min), abs(s_max), 1.0)
    norm_s  = mcolors.TwoSlopeNorm(vcenter=0, vmin=-vabs, vmax=vabs)
    cmap_s  = cm.RdYlGn
    xs_f, ys_f, clrs_f, sizes_f = [], [], [], []
    for stn in stns:
        if stn not in coords: continue
        lat, lon = coords[stn]
        slope, z_v, sig05 = mmk_ann.get(stn, (np.nan, 0.0, False))
        sabs = abs(slope) if pd.notna(slope) else 0.0
        xs_f.append(float(lon)); ys_f.append(float(lat))
        clrs_f.append(slope if pd.notna(slope) else 0.0)
        sizes_f.append(_bubble_size(sabs, global_max))
    if xs_f:
        sc2 = ax.scatter(xs_f, ys_f, c=clrs_f, cmap=cmap_s, norm=norm_s,
                         s=sizes_f, edgecolors="black", linewidths=0.6,
                         zorder=4, alpha=0.90)
        plt.colorbar(sc2, ax=ax, orientation="vertical", pad=0.01,
                     shrink=0.65, label="β (mm yr⁻¹)")
        for stn, xi, yi in zip([s for s in stns if s in coords], xs_f, ys_f):
            ax.annotate(smap.get(stn, stn), xy=(xi, yi), xytext=(3, 4),
                        textcoords="offset points", fontsize=8, zorder=5)
        _geo_axes(ax, xs_f, ys_f)
    ax.set_title(f"(f)  Annual Sen's Slope β (MMK)\n"
                 "     Colour = magnitude & direction",
                 loc="left", fontsize=10, fontweight="bold", pad=4)

    # ── Panel (g): Field significance bar ────────────────────────────────────
    ax = axes[6]
    if field_sig_df is not None and len(field_sig_df) > 0:
        scales_fs = field_sig_df["Scale"].tolist()
        p_w = field_sig_df.get("Walker_p_MK", pd.Series(dtype=float)).tolist()
        p_l = field_sig_df.get("LC_p_MK",     pd.Series(dtype=float)).tolist()
        x_p = np.arange(len(scales_fs)); bw = 0.35
        ax.bar(x_p - bw/2, p_w, width=bw, color="#6A1B9A", alpha=0.80,
               label="Walker")
        ax.bar(x_p + bw/2, p_l, width=bw, color="#0277BD", alpha=0.80,
               label="LC-MC")
        ax.axhline(0.05, color="red", lw=1.4, ls="--", label="α=0.05")
        ax.set_xticks(x_p)
        ax.set_xticklabels([_SCALE_LABEL.get(s, s) for s in scales_fs], fontsize=9)
        ax.set_ylabel("p-value", fontsize=10)
        ax.legend(fontsize=8, frameon=True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    ax.set_title("(g)  Field Significance\n     Walker & LC-MC",
                 loc="left", fontsize=10, fontweight="bold", pad=4)

    # ── Panel (h): blank or summary text ─────────────────────────────────────
    axes[7].set_visible(False)

    fig.suptitle(
        f"Comprehensive Spatial Trend Overview  |  Prachuap Khiri Khan Basin  |  {period}\n"
        f"Bubble size ∝ |Sen's slope|  |  {_CRS_NOTE}",
        fontsize=12, fontweight="bold", y=0.975
    )
    savefig(fig, str(Path(out_dir) / f"{prefix}_Fig_SpatialFull"))


# ── Backward-compatible entry point (original fig14) ─────────────────────────

def fig14_spatial_maps(trend_df: pd.DataFrame,
                        stns: list,
                        smap: dict,
                        coords: dict | None,
                        period: str,
                        out_dir: str,
                        prefix: str) -> None:
    """
    Fig 14 — Geographic bubble maps of Modified MK Sen's slope (3 scales).
    Backward-compatible signature; now uses real coordinates when available.
    """
    stns = [str(s) for s in stns]
    df   = trend_df.copy()
    if "Scale" in df.columns:
        df["Scale"] = df["Scale"].str.lower().str.strip()

    use_coords = coords is not None and len(coords) > 0

    mmk_df = df[df["Method"].isin(["Modified MK", "Modified MK (H&R98)"])].copy()

    slope_vals = pd.to_numeric(
        mmk_df.get("Slope_Q", pd.Series(dtype=float)), errors="coerce"
    ).dropna().abs()
    global_max = float(slope_vals.max()) if len(slope_vals) > 0 else 1.0

    fig, axes = plt.subplots(1, 3, figsize=(18, 7))
    fig.subplots_adjust(left=0.06, right=0.97, top=0.88,
                        bottom=0.10, wspace=0.30)

    panel_labels = ["(a)", "(b)", "(c)"]
    for col_idx, scale_key in enumerate(_SCALE_ORDER):
        ax    = axes[col_idx]
        label = panel_labels[col_idx]
        sub   = mmk_df[mmk_df["Scale"] == scale_key]

        xs, ys, sizes, colors, labels_plot = [], [], [], [], []
        for s_idx, stn in enumerate(stns):
            row_s = sub[sub["Station"] == stn]
            if len(row_s) == 0:
                continue
            r       = row_s.iloc[0]
            slope_q = pd.to_numeric(r.get("Slope_Q", np.nan), errors="coerce")
            z_val   = pd.to_numeric(r.get("Z",       np.nan), errors="coerce")
            sig05   = bool(r.get("sig_05", False))
            sabs    = abs(float(slope_q)) if pd.notna(slope_q) else 0.0
            z_f     = float(z_val)        if pd.notna(z_val)   else 0.0

            if use_coords and stn in coords:
                lat, lon = coords[stn]
                x_val, y_val = float(lon), float(lat)
            else:
                x_val, y_val = float(s_idx), 0.0

            xs.append(x_val);  ys.append(y_val)
            sizes.append(_bubble_size(sabs, global_max))
            colors.append(_trend_color(sig05, z_f))
            labels_plot.append(smap.get(stn, stn))

        if xs:
            ax.scatter(xs, ys, s=sizes, c=colors,
                       edgecolors="black", linewidths=0.7,
                       zorder=4, alpha=0.88)
            for xi, yi, lbl in zip(xs, ys, labels_plot):
                ax.annotate(lbl, xy=(xi, yi), xytext=(4, 5),
                            textcoords="offset points", fontsize=8.5,
                            color="#212121", zorder=5)

        if use_coords and xs:
            _geo_axes(ax, xs, ys)
            _draw_scale_bar(ax, xs, ys, frac=0.30)
        else:
            ax.set_xlabel("Station Index", fontsize=11)
            if xs:
                ax.set_xlim(-0.8, len(stns) - 0.2)
                ax.set_ylim(-1.0, 1.0)
                ax.set_yticks([])
            ax.set_xticks(list(range(len(stns))))
            ax.set_xticklabels([smap.get(s, s) for s in stns],
                               rotation=45, ha="right", fontsize=9)

        ax.set_title(
            f"{label} {_SCALE_LABEL[scale_key]} — Sen's Slope (MMK)\n{period}",
            fontsize=11, pad=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.35, color="#B0BEC5")

        legend_handles = [
            mpatches.Patch(facecolor=C["inc"],    edgecolor="k",
                           lw=0.7, label="Increasing (sig.)"),
            mpatches.Patch(facecolor=C["dec"],    edgecolor="k",
                           lw=0.7, label="Decreasing (sig.)"),
            mpatches.Patch(facecolor=C["ns_col"], edgecolor="k",
                           lw=0.7, label="Not significant"),
        ]
        ref_fracs  = [0.25, 0.50, 1.00]
        for rf in ref_fracs:
            size_pt = _bubble_size(rf * global_max, global_max)
            legend_handles.append(
                Line2D([0], [0], marker="o", color="w",
                       markerfacecolor=C["grey"], markeredgecolor="k",
                       markersize=math.sqrt(size_pt / math.pi),
                       label=f"|slope| = {rf*global_max:.1f} mm yr⁻¹"))
        ax.legend(handles=legend_handles, fontsize=7.5, loc="lower right",
                  framealpha=0.85)

    crs_txt = f"{_CRS_NOTE}  |  " if use_coords else ""
    fig.suptitle(
        f"Spatial Distribution of Rainfall Trends (Modified MK)  |  {period}\n"
        f"{crs_txt}Bubble size ∝ |Sen's slope|",
        fontsize=13, y=1.01
    )
    fig.tight_layout(rect=[0, 0, 1, 1])
    savefig(fig, f"{out_dir}/{prefix}_Fig14_SpatialMaps")
