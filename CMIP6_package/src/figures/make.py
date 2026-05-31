"""figures.make — Figures 1–7 (single+double column, no title/footnote, (a)(b)(c)).

Q1 publication standards applied throughout:
  • Serif font (set in base.py rcParams)
  • No top/right spines; light dashed grid at α 0.45
  • Colorblind-safe diverging palette (RdBu) and sequential (YlGnBu)
  • 600 DPI PNG + TIFF + PDF for every figure × {single, double} column
  • Taylor diagram: dynamic rmax; clipping guard; standard construction
  • Spatial maps: station-based (honest for N≈12); shared colour scale per figure
  • vals_for results cached to avoid double-computation
  • np.concatenate guard when no stations match meta index
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec

from .base import save_dual, panel_tag, add_panel_label, auto_color_range
from ..gis.interp import load_boundary

log = logging.getLogger(__name__)
SCEN = ["ssp245", "ssp585"]

# Scenario display labels and colours (colorblind-safe)
_SCEN_COL = {"ssp245": "#0072B2", "ssp585": "#D55E00"}
_SCEN_LAB = {"ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5"}


# ── Shared map helper ─────────────────────────────────────────────────────────

def _boundary_plot(ax, geom):
    polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    for p in polys:
        xs, ys = p.exterior.xy
        ax.plot(xs, ys, color="#333333", lw=0.9, zorder=5)


def _map_axes_style(ax, bounds):
    x0, y0, x1, y1 = bounds
    mx, my = (x1 - x0) * 0.05, (y1 - y0) * 0.05
    ax.set_xlim(x0 - mx, x1 + mx)
    ax.set_ylim(y0 - my, y1 + my)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.5)
        spine.set_color("#888")


# ── Figure 1 — Taylor diagram ─────────────────────────────────────────────────

def fig1_taylor(d: dict, cfg: dict) -> list[Path]:
    """Taylor diagram (Annual): per-station Raw MME & BC-MME vs Observed.

    Standard construction (Taylor 2001):
      radius    = σ_sim / σ_obs   (normalised standard deviation)
      azimuth   = arccos(r)        (Pearson correlation)
      reference arc at radius = 1 represents perfect σ match.
    rmax is set dynamically from data (max σ_ratio + 10% headroom, min 1.6).
    """
    obs    = d["obs"]
    bc     = d["bc_mme"]
    raw    = d["raw_mme"]
    o_year = (obs[obs.season == "Annual"]
              .groupby(["station", "year"]).rainfall.mean())

    def _points(mme: pd.DataFrame) -> list[tuple[float, float]]:
        out = []
        for st in o_year.index.get_level_values(0).unique():
            oo = o_year.loc[st]
            sub = mme[(mme.season == "Annual") & (mme.scenario == "historical")
                      & (mme.station == st)]
            ss = sub.set_index("year")["mean"]
            idx = oo.index.intersection(ss.index)
            if len(idx) < 3:
                continue
            ov = oo.loc[idx].to_numpy()
            sv = ss.loc[idx].to_numpy()
            std_o = np.std(ov, ddof=0)
            std_s = np.std(sv, ddof=0)
            if std_o == 0 or std_s == 0:
                continue
            corr     = float(np.corrcoef(ov, sv)[0, 1])
            sd_ratio = std_s / std_o
            out.append((np.arccos(np.clip(corr, -1.0, 1.0)), sd_ratio))
        return out

    raw_pts = _points(raw)
    bc_pts  = _points(bc)

    # Dynamic rmax: accommodate all points with 10% headroom
    all_r = [r for _, r in raw_pts + bc_pts] + [1.0]
    rmax = max(max(all_r) * 1.10, 1.6)

    def build(w: float):
        fig = plt.figure(figsize=(w, w * 0.95))
        ax = fig.add_subplot(111, polar=True)
        ax.set_thetamin(0)
        ax.set_thetamax(90)

        # Correlation labels on the azimuth axis
        corr_vals = [1.0, 0.99, 0.95, 0.90, 0.80, 0.60, 0.40, 0.20, 0.0]
        theta_locs = [np.degrees(np.arccos(c)) for c in corr_vals]
        theta_labs = [str(c) for c in corr_vals]
        ax.set_thetagrids(theta_locs, labels=theta_labs, fontsize=7)

        # Reference arc (σ_ratio = 1) and normalised std radial labels
        arc = np.linspace(0, np.pi / 2, 180)
        ax.plot(arc, np.ones_like(arc), color="0.55", lw=0.9, ls="--",
                zorder=2, label="_nolegend_")
        ax.set_rlabel_position(90)
        ax.set_rticks([0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
        ax.set_rmax(rmax)

        # Correlation axis label — placed just beyond rmax in the NW direction
        label_r = rmax * 1.22
        ax.text(np.deg2rad(52), label_r, "Correlation",
                ha="center", va="center", fontsize=8, rotation=-38,
                style="italic")

        # Data points
        for pts, color, lab, mk in [
            (raw_pts, "#C62828", "Raw MME",  "o"),
            (bc_pts,  "#2E7D32", "BC-MME",   "s"),
        ]:
            if pts:
                th, r = zip(*pts)
                ax.scatter(th, r, c=color, marker=mk,
                           s=30, alpha=0.80, edgecolors="k", linewidths=0.4,
                           label=lab, zorder=4)

        # Observed reference point
        ax.scatter([0], [1], c="k", marker="*", s=200,
                   label="Observed (ref.)", zorder=6)

        ax.set_ylabel("Normalised standard deviation", labelpad=26, fontsize=8)
        ax.legend(loc="upper right", bbox_to_anchor=(1.32, 1.14),
                  frameon=True, framealpha=0.9, fontsize=8, handlelength=1.4)
        fig.subplots_adjust(left=0.04, right=0.78, top=0.92, bottom=0.08)
        return fig

    return save_dual(build, "Figure1_Taylor", cfg)


# ── Figure 2 — Validation Cleveland dot plot ──────────────────────────────────

def fig2_validation(d: dict, cfg: dict) -> list[Path]:
    """3×1 Cleveland dot plot: (a) KGE  (b) NSE  (c) PBIAS, ranked by BC value."""
    vm = d["vm"]
    a  = vm[vm.season == "Annual"].copy()

    # Reference lines for KGE and NSE at 0 and 1
    REFS = {"KGE": [0.0, 1.0], "NSE": [0.0, 1.0], "PBIAS": [0.0]}

    def build(w: float):
        fig, axes = plt.subplots(3, 1, figsize=(w, w * 1.6), sharey=False)
        for ax, (metric, tag) in zip(axes, [("KGE", "a"), ("NSE", "b"), ("PBIAS", "c")]):
            s = a.dropna(subset=[f"{metric}_Raw", f"{metric}_BC"])
            s = s.sort_values(f"{metric}_BC").reset_index(drop=True)
            y = np.arange(len(s))
            # connector line
            ax.hlines(y, s[f"{metric}_Raw"], s[f"{metric}_BC"],
                      color="0.75", lw=0.9, zorder=1)
            # points
            ax.scatter(s[f"{metric}_Raw"], y, c="#C62828", s=22,
                       label="Raw MME", zorder=3, edgecolors="none")
            ax.scatter(s[f"{metric}_BC"],  y, c="#2E7D32", s=22,
                       label="BC-MME",  zorder=3, edgecolors="none")
            # reference lines
            for ref in REFS.get(metric, []):
                ax.axvline(ref, color="0.40", lw=0.7, ls=":", zorder=0)

            ax.set_yticks(y)
            ax.set_yticklabels(s.station.astype(str), fontsize=6.5)
            ax.set_xlabel(metric, fontsize=9)
            ax.yaxis.set_tick_params(length=0)
            panel_tag(ax, tag)
            if tag == "a":
                ax.legend(frameon=True, framealpha=0.9,
                          loc="lower right", fontsize=7.5,
                          handlelength=1.0, borderpad=0.5)
        fig.tight_layout(h_pad=0.8)
        return fig

    return save_dual(build, "Figure2_Validation", cfg)


# ── Figure 3 — Continuous time-series (anomaly) ───────────────────────────────

def fig3_timeseries(d: dict, cfg: dict) -> list[Path]:
    """3×1 continuous 1981–2050 anomaly series: Observed + BC hist + BC SSP245/585.

    Anomaly base = observed spatial mean per season (1981–2014).
    5-yr centred moving average applied to all series.
    P25–P75 ensemble spread shaded at α=0.15.
    Near-future mean change annotated per scenario.
    """
    obs    = d["obs"]
    bc     = d["bc_mme"]
    change = d["change"]

    COL = {
        "Observed":   "#000000",
        "historical": "#4D4D4D",
        "ssp245":     _SCEN_COL["ssp245"],
        "ssp585":     _SCEN_COL["ssp585"],
    }
    LAB = {
        "historical": "BC historical",
        "ssp245":     f"BC {_SCEN_LAB['ssp245']}",
        "ssp585":     f"BC {_SCEN_LAB['ssp585']}",
    }

    def _ma5(s: pd.Series) -> pd.Series:
        return s.rolling(5, center=True, min_periods=1).mean()

    # Baseline: spatial-mean per season over ALL stations and ALL obs years
    base = obs.groupby("season").rainfall.mean()

    def build(w: float):
        fig = plt.figure(figsize=(w, w * 1.45))
        gs  = GridSpec(3, 1, height_ratios=[1.2, 1.2, 1.0],
                       hspace=0.10, figure=fig)
        axes = [fig.add_subplot(gs[i]) for i in range(3)]
        handles_labels = None

        for ax, (se, tag) in zip(axes, [("Annual", "a"), ("Wet", "b"), ("Dry", "c")]):
            b = base[se]

            # Observed anomaly
            o_anom = (obs[obs.season == se]
                      .groupby("year").rainfall.mean() - b)
            ax.plot(o_anom.index, _ma5(o_anom),
                    color=COL["Observed"], lw=1.8,
                    label="Observed", zorder=6)

            # MME scenarios
            for scen in ["historical", "ssp245", "ssp585"]:
                sub = bc[(bc.season == se) & (bc.scenario == scen)]
                if sub.empty:
                    continue
                gm  = sub.groupby("year")["mean"].mean() - b
                p25 = sub.groupby("year")["p25"].mean() - b
                p75 = sub.groupby("year")["p75"].mean() - b
                lw  = 1.0 if scen == "historical" else 1.8
                ax.plot(gm.index, _ma5(gm),
                        color=COL[scen], lw=lw, label=LAB[scen], zorder=5)
                ax.fill_between(gm.index, p25, p75,
                                color=COL[scen], alpha=0.15, lw=0, zorder=2)

            ax.axhline(0, color="0.55", lw=0.7, ls="--", zorder=1)

            # Near-future change annotation
            ann_lines = []
            for scen in ["ssp245", "ssp585"]:
                sub = change[(change.season == se) & (change.scenario == scen)]
                if sub.empty:
                    continue
                cc = sub.change_pct.mean()
                if np.isfinite(cc):
                    arrow = "↑" if cc > 0 else "↓"
                    ann_lines.append(f"{_SCEN_LAB[scen]}: {cc:+.1f}% {arrow}")
            if ann_lines:
                ax.text(0.985, 0.94, "\n".join(ann_lines),
                        transform=ax.transAxes, ha="right", va="top",
                        fontsize=7.5,
                        bbox=dict(boxstyle="round,pad=0.3",
                                  fc="white", ec="0.65", alpha=0.92))

            ax.set_ylabel(f"{se}\nanomaly (mm)", fontsize=9)
            add_panel_label(ax, tag)
            ax.set_xlim(1981, 2050)
            ax.yaxis.set_major_locator(mticker.MaxNLocator(5))
            if tag != "c":
                ax.tick_params(labelbottom=False)
            if handles_labels is None:
                handles_labels = ax.get_legend_handles_labels()

        axes[-1].set_xlabel("Year", fontsize=9)

        # Shared legend above the top panel
        fig.legend(
            *handles_labels,
            loc="upper center", ncol=4, frameon=True, framealpha=0.9,
            fontsize=8, bbox_to_anchor=(0.5, 1.01),
            columnspacing=1.2, handlelength=1.6, borderpad=0.5,
        )
        fig.subplots_adjust(top=0.93, left=0.15, right=0.97, bottom=0.07)
        return fig

    return save_dual(build, "Figure3_TimeSeries", cfg)


# ── Spatial map helpers ───────────────────────────────────────────────────────

def _station_change_map(ax, geom, bounds, xy: np.ndarray, vals: np.ndarray,
                        vlim: tuple, label_units: str,
                        show_legend: bool = False):
    """Proportional-symbol map: size ∝ |ΔP|, colour = diverging (RdBu)."""
    _boundary_plot(ax, geom)
    _map_axes_style(ax, bounds)
    smax = max(float(np.nanmax(np.abs(vals))), 1e-9)
    sizes = 35 + 320 * (np.abs(vals) / smax)
    sc = ax.scatter(
        xy[:, 0], xy[:, 1], s=sizes, c=vals,
        cmap="RdBu", vmin=vlim[0], vmax=vlim[1],
        edgecolors="k", linewidths=0.5, zorder=6,
    )
    if show_legend:
        for frac, lab in [(0.33, "small"), (0.66, "medium"), (1.0, "large")]:
            ax.scatter([], [], s=35 + 320 * frac, c="0.55",
                       edgecolors="k", linewidths=0.5,
                       label=f"{frac * smax:.0f}")
        ax.legend(title=f"|{label_units}|", loc="lower left",
                  frameon=True, framealpha=0.9,
                  fontsize=6, title_fontsize=6.5,
                  labelspacing=1.0, borderpad=0.6)
    return sc


def _station_value_map(ax, geom, bounds, xy: np.ndarray, vals: np.ndarray,
                       vlim: tuple, cmap: str = "YlGnBu"):
    """Fixed-size symbol map: colour = rainfall value."""
    _boundary_plot(ax, geom)
    _map_axes_style(ax, bounds)
    sc = ax.scatter(
        xy[:, 0], xy[:, 1], s=95, c=vals,
        cmap=cmap, vmin=vlim[0], vmax=vlim[1],
        edgecolors="k", linewidths=0.5, zorder=6,
    )
    return sc


def _collect_vals(obs, bc, meta, season):
    """Pre-compute station xy + values for all 4 panels of a spatial figure.

    Returns a dict keyed by (kind, scen) with (xy, vv) arrays.
    Compute once — avoids the double-call bug.
    """
    panels_def = [("obs", None), ("bc", "historical"),
                  ("bc", "ssp245"), ("bc", "ssp585")]
    result = {}
    for kind, scen in panels_def:
        if kind == "obs":
            s = obs[obs.season == season].groupby("station").rainfall.mean()
        else:
            sub = bc[(bc.season == season) & (bc.scenario == scen)]
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


# ── Figures 4–6 — Spatial rainfall maps ──────────────────────────────────────

def _spatial_2x2(d: dict, cfg: dict, season: str, fid: str) -> list[Path]:
    """2×2 station-based maps: (a) Observed  (b) Hist BC-MME  (c) SSP245  (d) SSP585."""
    geom, bounds = load_boundary(cfg["paths"]["boundary"], cfg["gis"]["target_crs"])
    meta = d["meta"].set_index("station")

    # Pre-compute all panel data (single pass — no double-call)
    panel_data = _collect_vals(d["obs"], d["bc_mme"], meta, season)

    panels = [
        ("obs",  None,         "a", "Observed"),
        ("bc",   "historical", "b", "Hist. BC-MME"),
        ("bc",   "ssp245",     "c", _SCEN_LAB["ssp245"]),
        ("bc",   "ssp585",     "d", _SCEN_LAB["ssp585"]),
    ]

    # Shared colour scale from all non-empty panels (guard against empty data)
    all_vals = [panel_data[(k, s)][1] for k, s, _, _ in panels]
    all_vals = [v for v in all_vals if v.size > 0]
    if not all_vals:
        log.warning("_spatial_2x2 [%s]: no station data — figure skipped", season)
        return []
    vlim = auto_color_range(np.concatenate(all_vals), diverging=False)

    def build(w: float):
        fig, axes = plt.subplots(2, 2, figsize=(w, w * 1.08))
        sc = None
        for ax, (kind, scen, tag, ttl) in zip(axes.ravel(), panels):
            xy, vv = panel_data[(kind, scen)]
            if vv.size:
                sc = _station_value_map(ax, geom, bounds, xy, vv, vlim)
            add_panel_label(ax, tag, ttl)
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
    """3×2 proportional-symbol change maps: Annual/Wet/Dry × SSP245/SSP585.

    Size ∝ |ΔP%|, colour = diverging RdBu centred at 0.
    Station-based (no interpolation) — appropriate for N≈12 stations.
    """
    geom, bounds = load_boundary(cfg["paths"]["boundary"], cfg["gis"]["target_crs"])
    meta = d["meta"].set_index("station")
    ch   = d["change"]

    vlim = auto_color_range(
        ch.change_pct.dropna().to_numpy(), diverging=True
    )

    def build(w: float):
        fig, axes = plt.subplots(3, 2, figsize=(w, w * 1.28))
        sc = None
        label_iter = iter("abcdef")
        for i, se in enumerate(["Annual", "Wet", "Dry"]):
            for j, scen in enumerate(SCEN):
                ax = axes[i, j]
                sub = ch[(ch.season == se) & (ch.scenario == scen)]
                xy_list, vv_list = [], []
                for _, r in sub.iterrows():
                    if r.station in meta.index and np.isfinite(r.change_pct):
                        xy_list.append([meta.loc[r.station, "lon"],
                                        meta.loc[r.station, "lat"]])
                        vv_list.append(r.change_pct)
                if vv_list:
                    sc = _station_change_map(
                        ax, geom, bounds,
                        np.array(xy_list), np.array(vv_list),
                        vlim, "ΔP %",
                        show_legend=(i == 0 and j == 0),
                    )
                add_panel_label(ax, next(label_iter),
                                f"{se} {_SCEN_LAB[scen]}")

        if sc is not None:
            cb = fig.colorbar(sc, ax=axes, fraction=0.038, pad=0.02, aspect=30)
            cb.set_label("ΔP (%)", fontsize=9)
            cb.ax.tick_params(labelsize=7)
        fig.subplots_adjust(left=0.02, right=0.82, top=0.96,
                            bottom=0.02, wspace=0.06, hspace=0.10)
        return fig

    return save_dual(build, "Figure7_Change", cfg)


# ── Master entry point ────────────────────────────────────────────────────────

def generate_all(d: dict, cfg: dict) -> dict[str, list[Path]]:
    saved: dict[str, list[Path]] = {}
    saved["F1"]   = fig1_taylor(d, cfg)
    saved["F2"]   = fig2_validation(d, cfg)
    saved["F3"]   = fig3_timeseries(d, cfg)
    saved["F456"] = fig4_5_6_spatial(d, cfg)
    saved["F7"]   = fig7_change(d, cfg)
    total = sum(len(v) for v in saved.values())
    log.info("generate_all: %d figure files written", total)
    return saved
