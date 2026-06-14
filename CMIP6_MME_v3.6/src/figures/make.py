"""figures.make — Figures 1–7 (single+double column, no title/footnote, (a)(b)(c)).

Figure inventory:
  Figure 1 — Taylor diagram: SPATIAL-pattern climatology (across stations)
  Figure 2 — Cleveland dot plot: PBIAS / SD-ratio / PSS (distributional), Raw vs BC
  Figure 3 — Continuous 1981–future anomaly time series (Annual/Wet/Dry)
  Figure 4 — Annual spatial maps: Observed / Hist-BC / SSP245 / SSP585
  Figure 5 — Wet-season spatial maps
  Figure 6 — Dry-season spatial maps
  Figure 7 — Proportional-symbol change maps (ΔP%) Annual/Wet/Dry × SSP245/585

Q1 publication standards:
  • Serif font (Times New Roman / Liberation Serif) — set in base.py rcParams
  • No top/right spines; light dashed grid α=0.45
  • Colorblind-safe diverging palette (RdBu) and sequential (YlGnBu)
  • 600 DPI PNG + TIFF + PDF × {single, double} column
  • Taylor: dynamic rmax, standard azimuth labels
  • Spatial maps: station-based (honest for N≈12); shared colour scale per figure
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patheffects as _pe
from matplotlib.gridspec import GridSpec

from .base import (save_dual, panel_tag, add_panel_label,
                   auto_color_range, free_corner)

log = logging.getLogger(__name__)

# white halo so dark station labels stay legible over any surface colour
_TXT_HALO = [_pe.withStroke(linewidth=1.4, foreground="white")]

# Colorblind-safe scenario palette (Wong 2011)
_SCEN_COL = {"ssp245": "#0072B2", "ssp585": "#D55E00",
             "ssp126": "#009E73", "ssp370": "#CC79A7"}
_SCEN_LAB = {"ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5",
             "ssp126": "SSP1-2.6", "ssp370": "SSP3-7.0"}


def _scen_col(scen: str) -> str:
    return _SCEN_COL.get(scen.lower(), "#888888")

def _scen_lab(scen: str) -> str:
    return _SCEN_LAB.get(scen.lower(), scen.upper())


# ── Shared map helpers ────────────────────────────────────────────────────────

def _load_rings(cfg: dict):
    """Boundary rings (lon/lat) + bounds via the dependency-free geo_lite backend
    (auto-reprojects from the .prj). Falls back to geopandas if available."""
    path = cfg["paths"]["boundary"]
    try:
        from ..gis.geo_lite import load_boundary_lonlat
        rings, bounds, _crs = load_boundary_lonlat(path)
        return rings, bounds
    except Exception as exc:                                   # pragma: no cover
        log.warning("geo_lite failed (%s); trying geopandas", exc)
        from ..gis.interp import load_boundary
        geom, bounds = load_boundary(path, cfg["gis"]["target_crs"])
        polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
        rings = [np.column_stack(p.exterior.xy) for p in polys]
        return rings, bounds


def _boundary_plot(ax, rings, fill: bool = True):
    """Draw boundary rings (lon/lat). Largest ring gets a light land fill."""
    if fill and rings:
        big = max(rings, key=len)
        ax.fill(big[:, 0], big[:, 1], facecolor="#F4F1EA",
                edgecolor="none", zorder=0)
    for r in rings:
        ax.plot(r[:, 0], r[:, 1], color="#333", lw=0.8, zorder=5)


def _mask_for_corner(cfg, rings, bounds, n=80):
    """Boolean inside-mask (image orientation) for free_corner placement."""
    try:
        from ..gis.geo_lite import mask_inside
        x0, y0, x1, y1 = bounds
        gx, gy = np.meshgrid(np.linspace(x0, x1, n), np.linspace(y0, y1, n))
        m = mask_inside(rings, gx, gy)
        return np.flipud(m)            # row 0 = geographic north
    except Exception:
        return None


def _map_axes_style(ax, bounds):
    x0, y0, x1, y1 = bounds
    mx, my = (x1 - x0) * 0.02, (y1 - y0) * 0.02   # tight crop → ~90% data fill
    ax.set_xlim(x0 - mx, x1 + mx)
    ax.set_ylim(y0 - my, y1 + my)
    ax.set_aspect("equal")
    # Coordinate tick labels — required by CLAUDE.md §12.9 (WGS84 lon/lat)
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f°E"))
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f°N"))
    ax.xaxis.set_major_locator(mticker.MaxNLocator(3, integer=False))
    ax.yaxis.set_major_locator(mticker.MaxNLocator(3, integer=False))
    ax.tick_params(labelsize=6, length=3, pad=2)
    ax.grid(False)                       # Q1: interior gridlines removed (ticks only)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.5)
        spine.set_color("#888")


def _add_north_arrow(ax, xy=(0.965, 0.97)):
    """Small filled compass north arrow tucked into the corner (Q1: must not
    overlap data)."""
    x, y = xy
    ax.annotate("", xy=(x, y), xytext=(x, y - 0.06),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>,head_width=0.22,head_length=0.45",
                                fc="k", ec="k", lw=0.9), zorder=11)
    ax.text(x, y + 0.012, "N", transform=ax.transAxes,
            ha="center", va="bottom", fontsize=6, fontweight="bold", zorder=11)


def _add_scale_bar(ax, bounds, frac=0.28, y_frac=0.06):
    """Horizontal scale bar in km (geographic→km at the map's mean latitude)."""
    x0, y0, x1, y1 = bounds
    lat_mid = 0.5 * (y0 + y1)
    km_per_deg = 111.320 * np.cos(np.deg2rad(lat_mid))
    span_deg = (x1 - x0) * frac
    raw_km = span_deg * km_per_deg
    # round to a nice number (1,2,5 ×10^n)
    mag = 10 ** np.floor(np.log10(raw_km))
    nice = min([1, 2, 5, 10], key=lambda m: abs(m * mag - raw_km)) * mag
    bar_deg = nice / km_per_deg
    bx = x0 + (x1 - x0) * 0.06
    by = y0 + (y1 - y0) * y_frac
    ax.plot([bx, bx + bar_deg], [by, by], color="k", lw=2.4,
            solid_capstyle="butt", zorder=11)
    ax.plot([bx, bx], [by, by + (y1 - y0) * 0.012], color="k", lw=1.0, zorder=11)
    ax.plot([bx + bar_deg, bx + bar_deg], [by, by + (y1 - y0) * 0.012],
            color="k", lw=1.0, zorder=11)
    ax.text(bx + bar_deg / 2, by + (y1 - y0) * 0.022, f"{nice:.0f} km",
            ha="center", va="bottom", fontsize=6.5, zorder=11)


def _idw_surface(xy, vals, bounds, rings, n=260, power=3.0):
    """IDW-interpolate to an n×n grid over bounds, masked to the boundary.

    power=3 (was 2) sharpens the field so it follows stations more closely and
    looks less like over-smoothed circular blobs (Q1 reviewer note). Returns
    (grid_z masked, extent). Dependency-free (geo_lite mask)."""
    x0, y0, x1, y1 = bounds
    gx, gy = np.meshgrid(np.linspace(x0, x1, n), np.linspace(y0, y1, n))
    pts = np.column_stack([gx.ravel(), gy.ravel()])
    d = np.sqrt(((pts[:, None, :] - xy[None, :, :]) ** 2).sum(2))
    d = np.where(d < 1e-9, 1e-9, d)
    w = 1.0 / d ** power
    z = (w * vals[None, :]).sum(1) / w.sum(1)
    z = z.reshape(gx.shape)
    try:
        from ..gis.geo_lite import mask_inside
        inside = mask_inside(rings, gx, gy)
        z = np.where(inside, z, np.nan)
    except Exception:
        pass
    return z, (x0, x1, y0, y1)


def _surface_value_map(ax, rings, bounds, xy, vals, vlim, cmap="YlGnBu",
                       levels=12):
    """Filled IDW surface + station markers + boundary + compass + scale bar."""
    _map_axes_style(ax, bounds)
    if len(xy) >= 3:
        z, _ = _idw_surface(xy, vals, bounds, rings)
        lv = np.linspace(vlim[0], vlim[1], levels)
        cf = ax.contourf(np.linspace(bounds[0], bounds[2], z.shape[1]),
                         np.linspace(bounds[1], bounds[3], z.shape[0]),
                         z, levels=lv, cmap=cmap, extend="both", zorder=1)
        ax.contour(np.linspace(bounds[0], bounds[2], z.shape[1]),
                   np.linspace(bounds[1], bounds[3], z.shape[0]),
                   z, levels=lv, colors="white", linewidths=0.25, alpha=0.6, zorder=2)
    else:
        cf = None
    for r in rings:
        ax.plot(r[:, 0], r[:, 1], color="#222", lw=0.9, zorder=5)
    sc = ax.scatter(xy[:, 0], xy[:, 1], s=26, c=vals, cmap=cmap,
                    vmin=vlim[0], vmax=vlim[1], edgecolors="k",
                    linewidths=0.6, zorder=6)
    _add_north_arrow(ax); _add_scale_bar(ax, bounds)
    return cf if cf is not None else sc


def _collect_panel_data(obs: pd.DataFrame, bc: pd.DataFrame,
                        meta: pd.DataFrame, season: str,
                        scenarios: list[str],
                        fut_window: tuple[int, int] | None = None) -> dict:
    """Pre-compute station (xy, values) for every panel — computed ONCE.

    Temporal windows are made CONSISTENT: Observed and historical BC use the
    baseline years present in their series; SSP scenarios are restricted to the
    near-future window `fut_window` (e.g., 2021-2050) so the maps compare the
    SAME future horizon used in the change-% analysis — not the 2015-2100 mean.

    Returns dict keyed by (kind, scen) with (xy_array, val_array) values.
    """
    panels = [("obs", None)] + [("bc", s) for s in ["historical"] + scenarios]
    result = {}
    for kind, scen in panels:
        if kind == "obs":
            s = obs[obs.season == season].groupby("station").rainfall.mean()
        else:
            sub = bc[(bc.season == season) & (bc.scenario == scen)]
            if scen != "historical" and fut_window is not None:
                f0, f1 = fut_window
                sub = sub[(sub.year >= f0) & (sub.year <= f1)]
            s = sub.groupby("station")["mean"].mean()
        xy_list, vv_list = [], []
        for st, v in s.items():
            if st in meta.index and np.isfinite(v):
                xy_list.append([meta.loc[st, "lon"], meta.loc[st, "lat"]])
                vv_list.append(v)
        result[(kind, scen)] = (
            np.array(xy_list) if xy_list else np.empty((0, 2)),
            np.array(vv_list) if vv_list else np.array([]),
        )
    return result


# ── Figure 1 — Spatial-pattern Taylor diagram ─────────────────────────────────

def fig1_taylor(d: dict, cfg: dict) -> list[Path]:
    """Taylor diagram (Annual) of the CLIMATOLOGICAL SPATIAL PATTERN.

    Rationale (v3.7)
    ----------------
    CMIP6 historical runs are free-running, so an interannual (year-matched)
    correlation against observations is undefined as a skill measure. This
    diagram instead evaluates the **spatial** pattern: every station is reduced
    to its climatological annual mean over the baseline, giving one value per
    station. The Taylor statistics are then computed ACROSS STATIONS:

        radius  = σ_sim / σ_obs   (normalised SPATIAL standard deviation)
        azimuth = arccos(r_s)     (Pearson correlation of the spatial pattern)

    where r_s measures whether the model reproduces which stations are wetter/
    drier (the spatial gradient), not the timing of individual years. One point
    per GCM (Raw and BC), plus the MME-mean centroid.

    Caveats (see module/figure caption):
      • BC is calibrated per station to the observed means, so BC points sit
        near the reference (r≈1, σ≈1) BY CONSTRUCTION — a consistency check,
        not independent skill. The RAW points carry the informative signal.
      • Station spacing within one province may be at/below the native GCM grid;
        the spatial variance partly reflects the regridding/interpolation, so
        σ_ratio and r should be read with the effective grid resolution in mind.
    """
    b0, b1 = cfg["periods"]["baseline"]
    obs = d["obs"]
    per = d.get("per", pd.DataFrame())

    # Observed station climatology over the baseline (one value per station)
    obs_a = obs[(obs.season == "Annual") & (obs.year >= b0) & (obs.year <= b1)]
    obs_clim = obs_a.groupby("station").rainfall.mean()

    _nst = {"n": 0}

    def _spatial_point(sim_long: pd.DataFrame):
        """(arccos r_s, σ_sim/σ_obs) across stations from climatological means."""
        sim_clim = (sim_long[(sim_long.year >= b0) & (sim_long.year <= b1)]
                    .groupby("station").rainfall.mean())
        common = [s for s in obs_clim.index.intersection(sim_clim.index)
                  if np.isfinite(obs_clim[s]) and np.isfinite(sim_clim[s])]
        if len(common) < 4:                      # need a spatial sample to correlate
            return None
        o = obs_clim.loc[common].to_numpy()
        m = sim_clim.loc[common].to_numpy()
        so, sm = np.std(o, ddof=1), np.std(m, ddof=1)
        if so == 0 or sm == 0:
            return None
        r = float(np.corrcoef(o, m)[0, 1])
        if not np.isfinite(r):
            return None
        _nst["n"] = max(_nst["n"], len(common))
        return (np.arccos(np.clip(r, -1, 1)), sm / so)

    def _points_per_model(dataset: str):
        if per.empty:
            return []
        sub = per[(per.dataset == dataset) & (per.scenario == "historical")
                  & (per.season == "Annual")]
        pts = []
        for m in sorted(sub.model.unique()):
            p = _spatial_point(sub[sub.model == m][["station", "year", "rainfall"]])
            if p:
                pts.append(p)
        return pts

    raw_pts = _points_per_model("Raw")
    bc_pts  = _points_per_model("BC")

    # Fallback: spatial-pattern point from the MME mean if no per-model table
    if not raw_pts and not bc_pts:
        def _mme_point(mme):
            sl = (mme[(mme.season == "Annual") & (mme.scenario == "historical")]
                  [["station", "year", "mean"]].rename(columns={"mean": "rainfall"}))
            p = _spatial_point(sl)
            return [p] if p else []
        raw_pts = _mme_point(d["raw_mme"]); bc_pts = _mme_point(d["bc_mme"])

    def _centroid(pts):
        if not pts:
            return None
        th = np.mean([p[0] for p in pts]); r = np.mean([p[1] for p in pts])
        return (th, r)

    all_r = [r for _, r in raw_pts + bc_pts] + [1.0]
    rmax  = max(max(all_r) * 1.15, 1.15)
    n_st  = _nst["n"]

    def build(w: float):
        fig = plt.figure(figsize=(w, w * 0.95))
        ax  = fig.add_subplot(111, polar=True)
        ax.set_thetamin(0); ax.set_thetamax(90)
        corr_vals = [1.0, 0.99, 0.95, 0.90, 0.80, 0.60, 0.40, 0.20, 0.0]
        ax.set_thetagrids([np.degrees(np.arccos(c)) for c in corr_vals],
                          labels=[str(c) for c in corr_vals], fontsize=7)
        arc = np.linspace(0, np.pi / 2, 180)
        ax.plot(arc, np.ones_like(arc), color="0.55", lw=0.9, ls="--", zorder=2)
        ax.set_rlabel_position(90)
        _rt = [t for t in [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5] if t <= rmax + 1e-6]
        ax.set_rticks(_rt); ax.set_rmax(rmax)
        ax.text(np.deg2rad(52), rmax * 1.22, "Spatial pattern correlation",
                ha="center", va="center", fontsize=8, rotation=-38, style="italic")

        for pts, color, lab, mk in [(raw_pts, "#E69F00", "Raw (per GCM)", "o"),
                                    (bc_pts,  "#0072B2", "BC (per GCM)",  "s")]:
            if pts:
                th, r = zip(*pts)
                ax.scatter(th, r, c=color, marker=mk, s=34, alpha=0.80,
                           edgecolors="k", linewidths=0.4, label=lab, zorder=4)
            cen = _centroid(pts)
            if cen:
                ax.scatter([cen[0]], [cen[1]], c=color, marker=mk, s=120,
                           edgecolors="k", linewidths=1.3, zorder=5,
                           label=f"{lab.split()[0]} MME mean")
        ax.scatter([0], [1], c="k", marker="*", s=200, label="Observed (ref.)", zorder=6)
        ax.set_ylabel("Normalised spatial SD  (across stations)", labelpad=26, fontsize=8)
        if n_st:
            ax.set_title(f"Climatological spatial pattern, Annual "
                         f"({b0}\u2013{b1}; n = {n_st} stations)", fontsize=8, pad=10)
        ax.legend(loc="upper right", bbox_to_anchor=(1.34, 1.16),
                  frameon=True, framealpha=0.90, fontsize=7.5, handlelength=1.2)
        fig.subplots_adjust(left=0.04, right=0.76, top=0.90, bottom=0.08)
        return fig

    return save_dual(build, "Figure1_Taylor", cfg)


# ── Figure 2 — Distributional validation Cleveland dot plot ───────────────────

def fig2_validation(d: dict, cfg: dict) -> list[Path]:
    """3×1 Cleveland dot plot: (a) PBIAS (b) SD-ratio (c) PSS, ranked by BC value.

    Order-invariant distributional metrics (free-running-GCM appropriate);
    interannual KGE/NSE are deliberately NOT shown (see validation.metrics)."""
    vm = d["vm"]
    a  = vm[vm.season == "Annual"].copy()
    REFS = {"PBIAS": [0.0], "SDratio": [1.0], "PSS": [1.0]}

    def build(w: float):
        fig, axes = plt.subplots(3, 1, figsize=(w, w * 1.65), sharey=False)
        for ax, (metric, tag) in zip(axes, [("PBIAS", "a"), ("SDratio", "b"), ("PSS", "c")]):
            s = (a.dropna(subset=[f"{metric}_Raw", f"{metric}_BC"])
                  .sort_values(f"{metric}_BC")
                  .reset_index(drop=True))
            y = np.arange(len(s))
            if len(s) == 0:
                ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center")
                panel_tag(ax, tag)
                continue
            ax.hlines(y, s[f"{metric}_Raw"], s[f"{metric}_BC"],
                      color="0.75", lw=0.9, zorder=1)
            ax.scatter(s[f"{metric}_Raw"], y, c="#E69F00", s=22,
                       label="Raw MME", zorder=3, edgecolors="none")
            ax.scatter(s[f"{metric}_BC"],  y, c="#0072B2", s=22,
                       label="BC-MME",  zorder=3, edgecolors="none")
            for ref in REFS.get(metric, []):
                ax.axvline(ref, color="0.40", lw=0.7, ls=":", zorder=0)
            ax.set_yticks(y)
            ax.set_yticklabels(s.station.astype(str), fontsize=6.5)
            ax.set_xlabel(metric, fontsize=9)
            _full = {"PBIAS": "Percent Bias (PBIAS, %)",
                     "SDratio": "Interannual SD ratio  σ_sim/σ_obs",
                     "PSS": "Perkins Skill Score (PDF overlap)"}
            ax.set_title(_full.get(metric, metric), fontsize=8.5, pad=3)
            ax.yaxis.set_tick_params(length=0)
            panel_tag(ax, tag)
            if tag == "a":
                ax.legend(frameon=True, framealpha=0.90,
                          loc="lower right", fontsize=7.5,
                          handlelength=1.0, borderpad=0.5)
        fig.tight_layout(h_pad=0.8)
        return fig

    return save_dual(build, "Figure2_Validation", cfg)


# ── Figure 3 — Continuous time-series ────────────────────────────────────────

def fig3_timeseries(d: dict, cfg: dict) -> list[Path]:
    """3×1 anomaly time series: Observed + BC historical + BC SSP scenarios.

    Anomaly base = observed spatial mean per season over the baseline period.
    5-yr centred moving average applied. P25–P75 ensemble spread shaded.
    Near-future mean change (%) annotated per scenario.
    """
    obs      = d["obs"]
    bc       = d["bc_mme"]
    change   = d["change"]
    scenarios = cfg.get("scenarios", ["ssp245", "ssp585"])

    COL = {"Observed": "#000000", "historical": "#4D4D4D"}
    for s in scenarios:
        COL[s] = _scen_col(s)
    LAB = {"historical": "BC historical"}
    for s in scenarios:
        LAB[s] = f"BC {_scen_lab(s)}"

    def _ma5(s: pd.Series) -> pd.Series:
        return s.rolling(5, center=True, min_periods=1).mean()

    bl0, bl1 = cfg.get("periods", {}).get("baseline", [1981, 2014])
    base = (obs[(obs.year >= bl0) & (obs.year <= bl1)]
            .groupby("season").rainfall.mean())

    def build(w: float):
        fig = plt.figure(figsize=(w, w * 1.62))
        gs  = GridSpec(3, 1, height_ratios=[1.2, 1.2, 1.0],
                       hspace=0.42, figure=fig)
        axes = [fig.add_subplot(gs[i]) for i in range(3)]
        handles_labels = None

        for ax, (se, tag) in zip(axes, [("Annual", "a"), ("Wet", "b"), ("Dry", "c")]):
            b = base.get(se, 0.0)

            # Observed anomaly
            o_anom = (obs[obs.season == se]
                      .groupby("year").rainfall.mean() - b)
            ax.plot(o_anom.index, _ma5(o_anom),
                    color=COL["Observed"], lw=1.8, label="Observed", zorder=6)

            # Historical MME (grey) — plotted over its own range
            hsub = bc[(bc.season == se) & (bc.scenario == "historical")]
            gm_h  = (hsub.groupby("year")["mean"].mean() - b) if not hsub.empty else pd.Series(dtype=float)
            hp25  = (hsub.groupby("year")["p25"].mean() - b) if not hsub.empty else pd.Series(dtype=float)
            hp75  = (hsub.groupby("year")["p75"].mean() - b) if not hsub.empty else pd.Series(dtype=float)
            if not gm_h.empty:
                ax.plot(gm_h.index, _ma5(gm_h), color=COL["historical"], lw=1.0,
                        label=LAB["historical"], zorder=5)

            # SSP scenarios — bridged to the historical endpoint so there is NO
            # gap at the 2014→2015 transition (join the series, smooth across the
            # junction, then display from the transition year onward).
            for scen in scenarios:
                sub = bc[(bc.season == se) & (bc.scenario == scen)]
                if sub.empty:
                    continue
                gm_s  = sub.groupby("year")["mean"].mean() - b
                p25_s = sub.groupby("year")["p25"].mean() - b
                p75_s = sub.groupby("year")["p75"].mean() - b

                gm_j = pd.concat([gm_h, gm_s]).sort_index()
                gm_j = gm_j[~gm_j.index.duplicated(keep="last")]
                sm   = _ma5(gm_j)
                sm   = sm[sm.index >= bl1]                # start at transition year
                ax.plot(sm.index, sm.values, color=COL.get(scen, "#888"),
                        lw=1.8, label=LAB.get(scen, scen), zorder=5)

                # spread band, also bridged from the historical value at bl1
                p25_j = pd.concat([hp25[hp25.index == bl1], p25_s]).sort_index()
                p75_j = pd.concat([hp75[hp75.index == bl1], p75_s]).sort_index()
                ax.fill_between(p25_j.index, p25_j.values, p75_j.values,
                                color=COL.get(scen, "#888"), alpha=0.15, lw=0, zorder=2)

            ax.axhline(0, color="0.55", lw=0.7, ls="--", zorder=1)

            # Annotation: near-future mean change
            f0, f1 = cfg["periods"]["near_future"]
            ann_lines = []
            for scen in scenarios:
                sub = change[(change.season == se) & (change.scenario == scen)
                             & (change.year >= f0) & (change.year <= f1)
                             if "year" in change.columns
                             else (change.season == se) & (change.scenario == scen)]
                if sub.empty:
                    continue
                cc = sub.change_pct.mean()
                if np.isfinite(cc):
                    ann_lines.append(f"{_scen_lab(scen)}: {cc:+.1f}% {'↑' if cc > 0 else '↓'}")
            if ann_lines:
                ax.text(0.985, 0.94, "\n".join(ann_lines),
                        transform=ax.transAxes, ha="right", va="top",
                        fontsize=7.5,
                        bbox=dict(boxstyle="round,pad=0.3",
                                  fc="white", ec="0.65", alpha=0.92))

            ax.set_ylabel(f"{se}\nanomaly (mm)", fontsize=9)
            add_panel_label(ax, tag)
            ax.set_title(f"{se} rainfall anomaly", fontsize=8.5, loc="center", pad=3)
            b0 = cfg["periods"].get("baseline", [1981, 2014])[0]
            _fut = bc[bc.scenario.isin(scenarios)]
            ts_end = int(_fut.year.max()) if len(_fut) else cfg["periods"]["near_future"][1]
            f0, f1 = cfg["periods"]["near_future"]
            ax.axvspan(f0, f1, color="0.82", alpha=0.40, lw=0, zorder=0)  # near-future window
            ax.text((f0 + f1) / 2, 0.97, "Near future", transform=ax.get_xaxis_transform(),
                    ha="center", va="top", fontsize=6.5, style="italic", color="0.35",
                    zorder=4)
            ax.set_xlim(b0, ts_end)
            ax.yaxis.set_major_locator(mticker.MaxNLocator(5))
            ax.tick_params(labelbottom=True)                 # x values on every sub-panel
            ax.set_xlabel("Year", fontsize=8)
            if handles_labels is None:
                handles_labels = ax.get_legend_handles_labels()

        if handles_labels and handles_labels[0]:
            ncol = min(len(handles_labels[0]), 4)
            fig.legend(*handles_labels,
                       loc="upper center", ncol=ncol,
                       frameon=True, framealpha=0.90,
                       fontsize=8, bbox_to_anchor=(0.5, 1.01),
                       columnspacing=1.2, handlelength=1.6, borderpad=0.5)

        fig.subplots_adjust(top=0.90, left=0.15, right=0.97, bottom=0.06)
        return fig

    return save_dual(build, "Figure3_TimeSeries", cfg)


# ── Spatial map panel helpers ─────────────────────────────────────────────────

def _station_change_map(ax, rings, bounds, xy: np.ndarray, vals: np.ndarray,
                        vlim: tuple, label_units: str, show_legend: bool = False,
                        agree_frac: np.ndarray | None = None, agree_thr: float = 0.7,
                        surface: bool = True, station_ids=None):
    """Filled diverging IDW surface (ΔP%) + uniform DIRECTION triangles +
    agreement HATCHING.

    Encoding (single system, no redundancy):
      • surface colour  = magnitude & sign of ΔP%  (RdBu)
      • triangle marker = DIRECTION only — ▲ increase, ▼ decrease (uniform size)
      • stippling (···) = robust signal: ≥ agree_thr of GCMs agree on the sign
    Station id labels are NOT drawn here (see the study-area supplementary map).
    """
    _map_axes_style(ax, bounds)
    sc = None
    lon = lat = None
    if surface and len(xy) >= 3:
        z, _ = _idw_surface(xy, vals, bounds, rings)
        lon = np.linspace(bounds[0], bounds[2], z.shape[1])
        lat = np.linspace(bounds[1], bounds[3], z.shape[0])
        lv = np.linspace(vlim[0], vlim[1], 13)
        sc = ax.contourf(lon, lat, z, levels=lv, cmap="RdBu", extend="both", zorder=1)
        ax.contour(lon, lat, z, levels=lv, colors="0.30", linewidths=0.5,
                   alpha=0.75, zorder=2)
        ax.contour(lon, lat, z, levels=[0], colors="k", linewidths=1.0,
                   linestyles="--", zorder=3)
    elif rings:
        big = max(rings, key=len)
        ax.fill(big[:, 0], big[:, 1], facecolor="#F4F1EA", edgecolor="none", zorder=0)
    for r in rings:
        ax.plot(r[:, 0], r[:, 1], color="#222", lw=0.9, zorder=5)

    # Significance stippling: hatch where the interpolated model-agreement ≥ thr
    if agree_frac is not None and lon is not None and np.isfinite(agree_frac).any():
        af = np.where(np.isfinite(agree_frac), agree_frac, 0.0)
        zg, _ = _idw_surface(xy, af, bounds, rings, power=2.0)
        ax.contourf(lon, lat, zg, levels=[agree_thr, 1.01], colors="none",
                    hatches=["....."], zorder=4)

    # Per-station robustness ring: a black open circle marks stations where the
    # across-model sign-agreement meets the threshold (replaces the previous
    # IDW-interpolated significance hatch, which imposed structure on N≈12 pts).
    if agree_frac is not None:
        af = np.where(np.isfinite(agree_frac), agree_frac, 0.0)
        rb = af >= agree_thr
        if np.any(rb):
            ax.scatter(xy[rb, 0], xy[rb, 1], s=130, facecolors="none",
                       edgecolors="k", linewidths=1.1, zorder=7)

    # Uniform direction markers (size no longer encodes magnitude — colour does)
    pos = vals > 0
    for mask, mk in [(pos, "^"), (~pos, "v")]:
        if np.any(mask):
            _m = ax.scatter(xy[mask, 0], xy[mask, 1], s=46, c=vals[mask],
                            cmap="RdBu", vmin=vlim[0], vmax=vlim[1], marker=mk,
                            edgecolors="k", linewidths=0.6, zorder=6)
            if sc is None:
                sc = _m
    _add_north_arrow(ax)
    if show_legend:
        import matplotlib.lines as mlines
        import matplotlib.patches as mpatches
        h = [mlines.Line2D([], [], marker="^", ls="", mfc="0.5", mec="k",
                           ms=8, label="Increase"),
             mlines.Line2D([], [], marker="v", ls="", mfc="0.5", mec="k",
                           ms=8, label="Decrease"),
             mlines.Line2D([], [], marker="o", ls="", mfc="none", mec="k",
                           ms=9, mew=1.1, label=f"≥{int(agree_thr*100)}% agree")]
        ax.legend(handles=h, loc="lower left", fontsize=5.6, framealpha=0.92,
                  edgecolor="0.7", labelspacing=0.6, borderpad=0.5,
                  handletextpad=0.5)
    else:
        _add_scale_bar(ax, bounds)
    return sc


def _station_value_map(ax, rings, bounds, xy: np.ndarray, vals: np.ndarray,
                       vlim: tuple, cmap: str = "YlGnBu"):
    """Fixed-size symbol map: colour = value."""
    _boundary_plot(ax, rings)
    _map_axes_style(ax, bounds)
    _add_north_arrow(ax)
    sc = ax.scatter(xy[:, 0], xy[:, 1], s=95, c=vals,
                    cmap=cmap, vmin=vlim[0], vmax=vlim[1],
                    edgecolors="k", linewidths=0.5, zorder=6)
    return sc


# ── Figures 4–6 — Spatial rainfall maps ──────────────────────────────────────

def _spatial_2x2(d: dict, cfg: dict, season: str, fid: str) -> list[Path]:
    """2×2 station maps: Observed | Hist-BC | SSP245 | SSP585 (or configured scenarios)."""
    rings, bounds = _load_rings(cfg)
    meta = d["meta"].set_index("station")
    scenarios = cfg.get("scenarios", ["ssp245", "ssp585"])

    # Pre-compute all panel data once
    f0, f1 = cfg["periods"]["near_future"]
    b0, b1 = cfg["periods"].get("baseline", [1981, 2014])
    panel_data = _collect_panel_data(d["obs"], d["bc_mme"], meta, season, scenarios,
                                     fut_window=(f0, f1))

    panels = (
        [("obs", None, "a", f"Observed ({b0}\u2013{b1})"),
         ("bc", "historical", "b", f"Hist. BC-MME ({b0}\u2013{b1})")]
        + [("bc", s, chr(ord("c") + i), f"{_scen_lab(s)} ({f0}\u2013{f1})")
           for i, s in enumerate(scenarios)]
    )

    all_vals = [panel_data.get((k, s), (None, np.array([])))[1] for k, s, _, _ in panels]
    all_vals = [v for v in all_vals if v.size > 0]
    if not all_vals:
        log.warning("_spatial_2x2 [%s]: no station data — figure skipped", season)
        return []
    vlim = auto_color_range(np.concatenate(all_vals), diverging=False)

    ncols = 2
    nrows = int(np.ceil(len(panels) / ncols))

    def build(w: float):
        fig, axes = plt.subplots(nrows, ncols, figsize=(w, w * 1.08 * (nrows / 2)))
        if nrows * ncols == 1:
            axes = np.array([[axes]])
        elif nrows == 1:
            axes = axes[np.newaxis, :]
        ax_flat = axes.ravel()
        sc = None
        for i, (kind, scen, tag, ttl) in enumerate(panels):
            ax = ax_flat[i]
            xy, vv = panel_data.get((kind, scen), (np.empty((0, 2)), np.array([])))
            if vv.size:
                sc = _surface_value_map(ax, rings, bounds, xy, vv, vlim)
            add_panel_label(ax, tag, ttl)
        # Hide unused axes
        for j in range(len(panels), len(ax_flat)):
            ax_flat[j].set_visible(False)
        if sc is not None:
            cb = fig.colorbar(sc, ax=axes, fraction=0.038, pad=0.02, aspect=28)
            cb.set_label(f"{season} rainfall (mm)", fontsize=9)
            cb.ax.tick_params(labelsize=7)
        fig.subplots_adjust(left=0.02, right=0.84, top=0.96,
                            bottom=0.02, wspace=0.06, hspace=0.08)
        return fig

    return save_dual(build, fid, cfg)


def fig4_5_6_spatial(d: dict, cfg: dict) -> list[Path]:
    out: list[Path] = []
    out += _spatial_2x2(d, cfg, "Annual", "Figure4_Annual_Spatial")
    out += _spatial_2x2(d, cfg, "Wet",    "Figure5_Wet_Spatial")
    out += _spatial_2x2(d, cfg, "Dry",    "Figure6_Dry_Spatial")
    return out


# ── Figure 7 — Change maps ────────────────────────────────────────────────────

def fig7_change(d: dict, cfg: dict) -> list[Path]:
    """3×N proportional-symbol change maps: Annual/Wet/Dry × all SSP scenarios.

    Size ∝ |ΔP%|, colour = diverging RdBu centred at 0.
    Station-based — appropriate for sparse networks (N≈12).
    """
    rings, bounds = _load_rings(cfg)
    meta      = d["meta"].set_index("station")
    ch        = d["change"]
    cm        = d.get("change_models", pd.DataFrame())
    agree_thr = cfg.get("figures", {}).get("agreement_threshold", 0.7)
    scenarios = cfg.get("scenarios", ["ssp245", "ssp585"])
    # Diverging range: use 90th percentile of |ΔP%| (rounded) so weak-signal
    # panels still show colour instead of a wide white centre (Q1 note).
    _abs_all = np.abs(ch.change_pct.dropna().to_numpy())
    if _abs_all.size:
        vmax = max(round(float(np.percentile(_abs_all, 90))), 4)
        vlim = (-vmax, vmax)
        size_thr = (round(float(np.percentile(_abs_all, 50))) or 1,
                    round(float(np.percentile(_abs_all, 80))) or 2)
    else:
        vlim, size_thr = (-9.0, 9.0), (3, 7)
    # stable station-id labels P01..PNN (sorted by station code)
    _stations_sorted = sorted(meta.index.astype(str))
    _sid_map = {s: f"P{i+1:02d}" for i, s in enumerate(_stations_sorted)}

    def _agree_frac(se, scen, st, mme_val):
        """Fraction of models whose change sign matches the MME mean sign."""
        if cm.empty or not np.isfinite(mme_val):
            return np.nan
        sub = cm[(cm.season == se) & (cm.scenario == scen) & (cm.station == st)]
        if sub.empty:
            return np.nan
        s = np.sign(mme_val)
        return float((np.sign(sub.change_pct) == s).mean())

    seasons = ["Annual", "Wet", "Dry"]
    nrows   = len(scenarios)        # rows  = scenarios (2)  → 2×3 layout
    ncols   = len(seasons)          # cols  = seasons   (3)

    def build(w: float):
        fig, axes = plt.subplots(nrows, ncols,
                                 figsize=(w, w * 0.60 * nrows))
        if nrows == 1 and ncols == 1:
            axes = np.array([[axes]])
        elif nrows == 1:
            axes = axes[np.newaxis, :]
        elif ncols == 1:
            axes = axes[:, np.newaxis]

        sc = None
        label_iter = iter("abcdefghijkl")
        for i, scen in enumerate(scenarios):           # row = scenario
            for j, se in enumerate(seasons):           # col = season
                ax  = axes[i, j]
                sub = ch[(ch.season == se) & (ch.scenario == scen)]
                xy_list, vv_list, ag_list = [], [], []
                for _, r in sub.iterrows():
                    if r.station in meta.index and np.isfinite(r.change_pct):
                        xy_list.append([meta.loc[r.station, "lon"],
                                        meta.loc[r.station, "lat"]])
                        vv_list.append(r.change_pct)
                        ag_list.append(_agree_frac(se, scen, r.station, r.change_pct))
                if vv_list:
                    sc = _station_change_map(
                        ax, rings, bounds,
                        np.array(xy_list), np.array(vv_list),
                        vlim, "ΔP %",
                        show_legend=(i == 0 and j == 0),
                        agree_frac=np.array(ag_list), agree_thr=agree_thr,
                        surface=False,   # sparse N≈12: per-station symbols, not an
                                         # interpolated ΔP% field (Q1 defensibility)
                    )
                add_panel_label(ax, next(label_iter),
                                f"{se} {_scen_lab(scen)}")

        if sc is not None:
            cb = fig.colorbar(sc, ax=axes, fraction=0.038, pad=0.02, aspect=30)
            cb.set_label("ΔP (%)", fontsize=9)
            cb.ax.tick_params(labelsize=7)
        fig.text(0.02, 0.005,
                 f"Ringed stations: ≥{int(agree_thr*100)}% of models agree on the sign of change",
                 fontsize=6.5, style="italic", color="0.30")
        fig.subplots_adjust(left=0.02, right=0.86, top=0.95,
                            bottom=0.06, wspace=0.10, hspace=0.04)
        return fig

    return save_dual(build, "Figure7_Change", cfg)


# ── Figure 0 — Study-area / station location map ─────────────────────────────

def fig0_studyarea(d: dict, cfg: dict) -> list[Path]:
    """Single-panel study-area map: boundary + stations coloured by elevation.

    The standard 'Figure 1' context map. Stations sized uniformly, coloured by
    DEM altitude; WGS84 coordinate ticks; north arrow. Portable to any province
    via the boundary shapefile (auto-reprojected by geo_lite)."""
    rings, bounds = _load_rings(cfg)
    meta = d["meta"]
    name = cfg.get("study_area", {}).get("name", "Study area")

    def build(w: float):
        fig, ax = plt.subplots(figsize=(w, w * 1.02))
        _boundary_plot(ax, rings)
        _map_axes_style(ax, bounds)
        _add_north_arrow(ax); _add_scale_bar(ax, bounds)
        if {"lon", "lat"}.issubset(meta.columns) and len(meta):
            c = meta["elevation"] if "elevation" in meta.columns else None
            sc = ax.scatter(meta["lon"], meta["lat"], s=42,
                            c=(c if c is not None else "#0072B2"),
                            cmap="cividis" if c is not None else None,
                            edgecolors="k", linewidths=0.5, zorder=7)
            # station id labels P01..PNN (matches the code↔Pnn table in metadata)
            order = sorted(meta.index.astype(str))
            sid = {s: f"P{i+1:02d}" for i, s in enumerate(order)}
            for st, row in meta.iterrows():
                ax.annotate(sid.get(str(st), ""), (row["lon"], row["lat"]),
                            textcoords="offset points", xytext=(4, 4),
                            fontsize=5.2, color="#111", zorder=8,
                            path_effects=_TXT_HALO)
            if c is not None:
                cb = fig.colorbar(sc, ax=ax, fraction=0.043, pad=0.02)
                cb.set_label("Station elevation (m a.s.l.)", fontsize=8)
                cb.ax.tick_params(labelsize=7)
        ax.set_title(name, fontsize=9, pad=6)
        # scale-ish reference: degrees graticule already shown via ticks
        fig.tight_layout()
        return fig

    return save_dual(build, "Figure0_StudyArea", cfg)


# ── Figure 8 — Inter-model spread of projected change ────────────────────────

def fig8_spread(d: dict, cfg: dict) -> list[Path]:
    """Box plots of per-model change% by season × scenario — the ensemble
    uncertainty figure. Each box pools per-model station-mean changes; the
    spread and whether it straddles zero convey inter-model (dis)agreement."""
    cm = d.get("change_models", pd.DataFrame())
    if cm.empty:
        log.warning("fig8_spread: no per-model change data — skipped")
        return []
    seasons   = ["Annual", "Wet", "Dry"]
    scenarios = cfg.get("scenarios", ["ssp245", "ssp585"])

    def build(w: float):
        fig, ax = plt.subplots(figsize=(w, w * 0.62))
        positions, data, colors, xticks = [], [], [], []
        gap = len(scenarios) + 1
        for si, se in enumerate(seasons):
            for k, scen in enumerate(scenarios):
                vals = cm[(cm.season == se) & (cm.scenario == scen)].change_pct.dropna()
                if vals.empty:
                    continue
                pos = si * gap + k
                positions.append(pos); data.append(vals.to_numpy())
                colors.append(_scen_col(scen))
            xticks.append((si * gap + (len(scenarios) - 1) / 2, se))
        bp = ax.boxplot(data, positions=positions, widths=0.7,
                        patch_artist=True, showfliers=False,
                        medianprops=dict(color="k", lw=1.1),
                        whiskerprops=dict(color="0.4"), capprops=dict(color="0.4"))
        for patch, col in zip(bp["boxes"], colors):
            patch.set_facecolor(col); patch.set_alpha(0.55); patch.set_edgecolor("0.3")
        # overlay individual model points
        for pos, vals, col in zip(positions, data, colors):
            jit = pos + (np.random.RandomState(0).rand(len(vals)) - 0.5) * 0.25
            ax.scatter(jit, vals, s=9, c=col, edgecolors="k", linewidths=0.3,
                       alpha=0.8, zorder=4)
        ax.axhline(0, color="0.4", lw=0.8, ls="--", zorder=1)
        ax.set_xticks([t for t, _ in xticks]); ax.set_xticklabels([l for _, l in xticks])
        ax.set_ylabel("Projected change (%)", fontsize=9)
        handles = [plt.Line2D([], [], marker="s", ls="", markerfacecolor=_scen_col(s),
                              markeredgecolor="0.3", markersize=8, label=_scen_lab(s))
                   for s in scenarios]
        ax.legend(handles=handles, frameon=True, framealpha=0.9, fontsize=8,
                  loc="best")
        fig.tight_layout()
        return fig

    return save_dual(build, "Figure8_ModelSpread", cfg)


# ── Master entry point ────────────────────────────────────────────────────────

def fig9_uncertainty(d: dict, cfg: dict) -> list[Path]:
    """2×N maps of ENSEMBLE UNCERTAINTY = inter-model SD of ΔP% per station.

    Rows = SSP scenarios, cols = seasons. Sequential 'magma_r' surface (higher =
    more model disagreement). Directly answers the Q1 reviewer's most common
    ask: show ensemble spread, not just the mean field.
    """
    cm = d.get("change_models", pd.DataFrame())
    if cm.empty:
        log.warning("fig9_uncertainty: no per-model change data — skipped")
        return []
    rings, bounds = _load_rings(cfg)
    meta = d["meta"].set_index("station")
    scenarios = cfg.get("scenarios", ["ssp245", "ssp585"])
    seasons   = ["Annual", "Wet", "Dry"]

    # inter-model SD per (scenario, season, station)
    sd = (cm.groupby(["scenario", "season", "station"]).change_pct.std(ddof=1)
          .reset_index().rename(columns={"change_pct": "sd"}))
    # Interpretable discrete classes (Q1: "is 10% high or low?")
    import matplotlib.colors as mcolors
    bins   = [0, 5, 10, 15, 20, 30]            # % — Low / Moderate / High / Very high / Extreme
    cmap_d = plt.cm.get_cmap("YlOrRd", len(bins) - 1)
    norm_d = mcolors.BoundaryNorm(bins, cmap_d.N)
    cls_lbl = ["Low\n(<5)", "Moderate\n(5–10)", "High\n(10–15)",
               "Very high\n(15–20)", "Extreme\n(>20)"]

    def _sd_surface(ax, xy, vv):
        xy = np.asarray(xy, float); vv = np.asarray(vv, float)
        _map_axes_style(ax, bounds)
        if len(xy) >= 3:
            z, _ = _idw_surface(xy, vv, bounds, rings)
            lon = np.linspace(bounds[0], bounds[2], z.shape[1])
            lat = np.linspace(bounds[1], bounds[3], z.shape[0])
            cf = ax.contourf(lon, lat, z, levels=bins, cmap=cmap_d, norm=norm_d,
                             extend="max", zorder=1)
            ax.contour(lon, lat, z, levels=bins, colors="0.25", linewidths=0.8,
                       alpha=0.8, zorder=2)             # Q1: contours 0.3→0.8 pt
        else:
            cf = None
        for r in rings:
            ax.plot(r[:, 0], r[:, 1], color="#222", lw=0.9, zorder=5)
        ax.scatter(xy[:, 0], xy[:, 1], s=22, c="none",
                   edgecolors="k", linewidths=0.5, zorder=6)
        _add_north_arrow(ax); _add_scale_bar(ax, bounds)
        return cf

    def build(w: float):
        fig, axes = plt.subplots(len(scenarios), len(seasons),
                                 figsize=(w, w * 0.60 * len(scenarios)))
        axes = np.atleast_2d(axes)
        sc = None
        lab = iter("abcdefghijkl")
        for i, scen in enumerate(scenarios):
            for j, se in enumerate(seasons):
                ax = axes[i, j]
                sub = sd[(sd.scenario == scen) & (sd.season == se)]
                xy, vv = [], []
                for _, r in sub.iterrows():
                    if r.station in meta.index and np.isfinite(r.sd):
                        xy.append([meta.loc[r.station, "lon"], meta.loc[r.station, "lat"]])
                        vv.append(r.sd)
                if vv:
                    cf = _sd_surface(ax, xy, vv)
                    sc = cf if cf is not None else sc
                add_panel_label(ax, next(lab), f"{se} {_scen_lab(scen)}")
        if sc is not None:
            cb = fig.colorbar(sc, ax=axes, fraction=0.038, pad=0.02, aspect=30,
                              ticks=[2.5, 7.5, 12.5, 17.5, 25])
            cb.ax.set_yticklabels(cls_lbl, fontsize=6)
            cb.set_label("Inter-model SD of ΔP (%) — disagreement class", fontsize=8.5)
        fig.subplots_adjust(left=0.02, right=0.86, top=0.95,
                            bottom=0.06, wspace=0.10, hspace=0.04)
        return fig

    return save_dual(build, "Figure9_Uncertainty", cfg)


def generate_all(d: dict, cfg: dict) -> dict[str, list[Path]]:
    """Generate all figures for the study area.

    Returns dict mapping figure key → list of saved file paths.
    """
    saved: dict[str, list[Path]] = {}
    saved["F0"]   = fig0_studyarea(d, cfg)
    saved["F1"]   = fig1_taylor(d, cfg)
    saved["F2"]   = fig2_validation(d, cfg)
    saved["F3"]   = fig3_timeseries(d, cfg)
    saved["F456"] = fig4_5_6_spatial(d, cfg)
    saved["F7"]   = fig7_change(d, cfg)
    saved["F8"]   = fig8_spread(d, cfg)
    saved["F9"]   = fig9_uncertainty(d, cfg)
    total = sum(len(v) for v in saved.values())
    log.info("generate_all [%s]: %d figure files",
             cfg.get("study_area", {}).get("name", ""), total)
    return saved
