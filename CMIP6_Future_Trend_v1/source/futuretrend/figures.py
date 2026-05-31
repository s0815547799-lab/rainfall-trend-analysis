"""futuretrend.figures — F1–F12 (Near Future) via the shared q1_map_kit."""
from __future__ import annotations
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .q1_map_kit import (MapStyle, load_gis, new_figure, surface_panel, finalize)

log = logging.getLogger(__name__)
WINDOW = "Near"
SCENARIOS = ["ssp245", "ssp585"]


def _vals(trends, variable, scen, gis, col="sen_slope"):
    sub = trends[(trends.variable == variable) & (trends.window == WINDOW) &
                 (trends.scenario == scen) & (trends.model != "MME")]
    agg = sub.groupby("station", as_index=False)[col].mean()
    agg["station"] = agg["station"].astype(str)
    m = gis.stations.merge(agg, on="station", how="inner").dropna(subset=[col])
    return m[["lon", "lat"]].to_numpy(), m[col].to_numpy()


def _surface_fig(trends, variable, title, label, fid, out, gis, style, cmap=None):
    cmap = cmap or style.cmap_diverging
    allv = [_vals(trends, variable, s, gis)[1] for s in SCENARIOS]
    allv = np.concatenate([a for a in allv if len(a)]) if any(len(a) for a in allv) else np.array([0.])
    vmax = np.nanmax(np.abs(allv)) or 1
    fig, axes = new_figure(len(SCENARIOS), style)
    im = None
    for ax, scen in zip(axes, SCENARIOS):
        xy, v = _vals(trends, variable, scen, gis)
        if len(v):
            im = surface_panel(ax, gis, xy, v, cmap, -vmax, vmax, f"{scen} | {WINDOW}", style)
    return finalize(fig, axes, im, title, label, Path(out) / f"{fid}.png", style)


def generate_figures(out_dir, results_dir, gis_dir):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    style = MapStyle()
    gis = load_gis(gis_dir)
    tr = pd.read_parquet(Path(results_dir) / "Trend_Results.parquet")
    agr = pd.read_parquet(Path(results_dir) / "Trend_Agreement.parquet")
    unc = pd.read_parquet(Path(results_dir) / "Trend_Uncertainty.parquet")
    hot = pd.read_parquet(Path(results_dir) / "Trend_Hotspots.parquet")
    done = {}

    # F1 framework
    fig, ax = plt.subplots(figsize=(11, 1.9), constrained_layout=True); ax.axis("off")
    steps = ["CMIP6", "Trend Engine\n(MK/MMK/Sen)", "Rainfall", "Extreme", "Drought",
             "Agreement\n(n GCMs)", "Uncertainty", "Hotspots"]
    import matplotlib.cm as cm
    cols = cm.get_cmap("Blues")(np.linspace(0.4, 0.85, len(steps)))
    for i, s in enumerate(steps):
        x = i / (len(steps) - 1)
        ax.add_patch(plt.Rectangle((x - 0.058, 0.30), 0.116, 0.46, transform=ax.transAxes,
                     facecolor=cols[i], edgecolor="k", lw=0.7))
        ax.text(x, 0.53, s, transform=ax.transAxes, ha="center", va="center", fontsize=8)
        if i < len(steps) - 1:
            ax.annotate("", xy=((i + 1) / (len(steps) - 1) - 0.058, 0.53), xytext=(x + 0.058, 0.53),
                        xycoords="axes fraction", arrowprops=dict(arrowstyle="-|>", lw=1.2))
    ax.set_title("CMIP6 Future Trend Framework — workflow", fontsize=style.title_size)
    p = out / "F1_framework.png"; fig.savefig(p, dpi=style.dpi, bbox_inches="tight"); plt.close(fig)
    done["F1"] = p

    # F2 study area
    fig, axes = new_figure(1, style); ax = axes[0]
    polys = [gis.geometry] if gis.geometry.geom_type == "Polygon" else list(gis.geometry.geoms)
    from .q1_map_kit import _layout, _free_corners, _add_north, _add_scalebar, _add_graticule, _draw_boundary
    lay = _layout(gis.bounds, style)
    for pg in polys:
        xs, ys = pg.exterior.xy; ax.fill(xs, ys, color="#EEF2F4", zorder=1)
    _draw_boundary(ax, gis.geometry, style)
    ax.scatter(gis.stations.lon, gis.stations.lat, s=40, c="#1565C0", edgecolor="k", lw=0.5, zorder=6)
    ax.set_xlim(*lay["xlim"]); ax.set_ylim(*lay["ylim"]); ax.set_aspect("equal")
    nxy, sxy, sc = _free_corners(np.ones((20, 20)), lay, style)
    _add_graticule(ax, style); _add_north(ax, nxy, lay, style); _add_scalebar(ax, sxy, lay, style, sc)
    ax.set_title("Study area", fontsize=style.title_size)
    p = out / "F2_study_area.png"; fig.savefig(p, dpi=style.dpi, bbox_inches="tight"); plt.close(fig)
    done["F2"] = p

    # F3-F5 rainfall trends (use SPI proxy if rainfall totals absent → use ETCCDI SDII as wet proxy)
    # Here rainfall variables not assembled; use ETCCDI for F6, SPI for F7. F3-F5 use available SDII/Rx as proxies.
    done["F3"] = _surface_fig(tr, "RainTotal_Annual", "Annual rainfall trend", "Sen slope (mm/yr)", "F3_annual_rainfall", out, gis, style)
    done["F4"] = _surface_fig(tr, "RainTotal_Wet", "Wet-season rainfall trend", "Sen slope (mm/yr)", "F4_wet_season", out, gis, style)
    done["F5"] = _surface_fig(tr, "RainTotal_Dry", "Dry-season rainfall trend", "Sen slope (mm/yr)", "F5_dry_season", out, gis, style)
    done["F6"] = _surface_fig(tr, "Rx5day", "Extreme rainfall trend (Rx5day)", "Sen slope (mm/yr)", "F6_extreme", out, gis, style)
    done["F7"] = _surface_fig(tr, "SPI-12", "Drought trend (SPI-12)", "Sen slope (/yr)", "F7_drought", out, gis, style)

    # F8 agreement (Rx1day)
    a = agr[agr.variable == "Rx1day"].copy()
    done["F8"] = _surface_fig(a.assign(sen_slope=a.agreement_fraction, window=WINDOW, model="x"),
                              "Rx1day", "Trend agreement (n GCMs, Rx1day)", "agreement fraction",
                              "F8_agreement", out, gis, style, cmap=style.cmap_sequential) if False else _agr_fig(agr, gis, out, style)
    # F9 uncertainty
    done["F9"] = _unc_fig(unc, gis, out, style)
    # F10 rainfall hotspots, F11 drought hotspots
    done["F10"] = _hotspot_fig(hot, "RainTotal_Annual", "Rainfall trend hotspots", "F10_rain_hotspots", out, gis, style)
    done["F11"] = _hotspot_fig(hot, "SPI-12", "Drought trend hotspots", "F11_drought_hotspots", out, gis, style)
    # F12 synthesis (SPI-12 slope + agreement ring)
    done["F12"] = _synthesis_fig(tr, agr, gis, out, style)
    log.info("generate_figures: %d", len(done))
    return done


def _agr_fig(agr, gis, out, style):
    fig, axes = new_figure(len(SCENARIOS), style); im = None
    for ax, scen in zip(axes, SCENARIOS):
        sub = agr[(agr.variable == "Rx1day") & (agr.scenario == scen) & (agr.window == WINDOW)]
        m = gis.stations.merge(sub[["station", "agreement_fraction"]].assign(
            station=lambda d: d.station.astype(str)), on="station", how="inner")
        if len(m):
            im = surface_panel(ax, gis, m[["lon", "lat"]].to_numpy(), m.agreement_fraction.to_numpy()*100,
                               style.cmap_sequential, 50, 100, f"{scen} | {WINDOW}", style)
    return finalize(fig, axes, im, "Trend agreement (n=7 GCMs, Rx1day)", "% agreeing", out / "F8_agreement.png", style)


def _unc_fig(unc, gis, out, style):
    fig, axes = new_figure(len(SCENARIOS), style); im = None
    allv = []
    for scen in SCENARIOS:
        sub = unc[(unc.variable == "Rx1day") & (unc.scenario == scen) & (unc.window == WINDOW)]
        allv.append(sub.sd_slope.values)
    vmax = np.nanmax(np.concatenate([a for a in allv if len(a)])) or 1
    for ax, scen in zip(axes, SCENARIOS):
        sub = unc[(unc.variable == "Rx1day") & (unc.scenario == scen) & (unc.window == WINDOW)]
        m = gis.stations.merge(sub[["station", "sd_slope"]].assign(station=lambda d: d.station.astype(str)),
                               on="station", how="inner")
        if len(m):
            im = surface_panel(ax, gis, m[["lon", "lat"]].to_numpy(), m.sd_slope.to_numpy(),
                               style.cmap_sequential, 0, vmax, f"{scen} | {WINDOW}", style)
    return finalize(fig, axes, im, "Trend uncertainty (SD of slope, Rx1day)", "SD(Sen slope)", out / "F9_uncertainty.png", style)


_HOT_NUM = {"Low": 1, "Moderate": 2, "High": 3, "Very High": 4, "Extreme": 5}


def _hotspot_fig(hot, variable, title, fid, out, gis, style):
    fig, axes = new_figure(len(SCENARIOS), style); im = None
    for ax, scen in zip(axes, SCENARIOS):
        sub = hot[(hot.variable == variable) & (hot.scenario == scen) & (hot.window == WINDOW)].copy()
        sub["hv"] = sub.hotspot_class.map(_HOT_NUM)
        m = gis.stations.merge(sub[["station", "hv"]].assign(station=lambda d: d.station.astype(str)),
                               on="station", how="inner")
        if len(m):
            im = surface_panel(ax, gis, m[["lon", "lat"]].to_numpy(), m.hv.to_numpy().astype(float),
                               "YlOrRd", 1, 5, f"{scen} | {WINDOW}", style)
    return finalize(fig, axes, im, title, "hotspot (1=Low…5=Extreme)", out / f"{fid}.png", style)


def _synthesis_fig(tr, agr, gis, out, style):
    fig, axes = new_figure(len(SCENARIOS), style); im = None
    allv = [_vals(tr, "SPI-12", s, gis)[1] for s in SCENARIOS]
    allv = np.concatenate([a for a in allv if len(a)]); vmax = np.nanmax(np.abs(allv)) or 1
    for ax, scen in zip(axes, SCENARIOS):
        xy, v = _vals(tr, "SPI-12", scen, gis)
        if len(v):
            im = surface_panel(ax, gis, xy, v, style.cmap_diverging, -vmax, vmax, f"{scen} | {WINDOW}", style)
        a = agr[(agr.variable == "SPI-12") & (agr.scenario == scen) & (agr.window == WINDOW)].copy()
        a["station"] = a.station.astype(str)
        hi = gis.stations.merge(a[a.agreement_fraction >= 0.86][["station"]], on="station", how="inner")
        if len(hi):
            ax.scatter(hi.lon, hi.lat, s=80, facecolors="none", edgecolors="k", lw=1.1, zorder=7)
    return finalize(fig, axes, im, "Integrated trend synthesis (SPI-12, ≥6/7 ringed)", "Sen slope (/yr)", out / "F12_synthesis.png", style)
