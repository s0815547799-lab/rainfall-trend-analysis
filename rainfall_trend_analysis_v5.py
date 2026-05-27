"""
rainfall_trend_analysis_v5.py — Province-independent Q1 spatial mapping
orchestrator (v5).

READS  (no statistical recomputation):
  results/final_N33/excel/*_Results.xlsx    — trend results archive
  boundaries/current_boundary/              — boundary.shp / .dbf / .shx / .prj
  data/stations.csv                         — station_id, lat, lon, altitude

WRITES:
  results/final_N33_v5/
    comparison_maps/
      Fig_Compare_MK_vs_MMK.{png,tif,pdf,svg}       × 3 scales
      Fig_Compare_PW_vs_TFPW.{png,tif,pdf,svg}      × 3 scales
    single_method_maps/
      Fig_Standard_MK.{png,tif,pdf,svg}             × 3 scales
      Fig_Modified_MK.{png,tif,pdf,svg}             × 3 scales
      Fig_PW_MK.{png,tif,pdf,svg}                   × 3 scales
      Fig_TFPW_MK.{png,tif,pdf,svg}                 × 3 scales
      Fig_Sen_Slope.{png,tif,pdf,svg}               × 3 scales

  [REGEN_MAIN=True only]
  results/final_N33_v5/publication_maps_v51/
      Fig_Q1_SpatialTrend_v5.{png,tif,pdf,svg}      × 3 scales

SAFETY:
  v4 files and results/final_N33/ are untouched.
  results/final_N33_v5/publication_maps/    NOT overwritten.
  results/final_N33_v5/publication_maps_v51/ NOT overwritten (REGEN_MAIN=False).
  MK / MMK / PW / TFPW / Sen slope statistics are NOT recomputed.

Run:
    python rainfall_trend_analysis_v5.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── Output control ─────────────────────────────────────────────────────────────
# Set True ONLY if you want to regenerate the 5-panel publication_maps_v51/ files.
# Kept False to avoid overwriting existing publication_maps_v51/ outputs.
REGEN_MAIN = False

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).parent
BOUNDARY_DIR = ROOT / "boundaries" / "current_boundary"
STATIONS_CSV = ROOT / "data" / "stations.csv"
FINAL_N33    = ROOT / "results" / "final_N33"
V5_ROOT      = ROOT / "results" / "final_N33_v5"
PUB_DIR      = V5_ROOT / "publication_maps_v51"   # existing — only if REGEN_MAIN
COMP_DIR     = V5_ROOT / "comparison_maps"         # NEW
SINGLE_DIR   = V5_ROOT / "single_method_maps"      # NEW
VAL_DIR      = V5_ROOT / "validation"
MAN_DIR      = V5_ROOT / "manuscript"
PERIOD       = "1981–2014"
DPI          = 600

EXCEL_PATH = next((FINAL_N33 / "excel").glob("*_Results.xlsx"), None)

# ── Pre-flight checks ─────────────────────────────────────────────────────────
print("=" * 68)
print("  Rainfall Trend Analysis v5 — Spatial Publication System")
print("=" * 68)

errors = []
for p, label in [
    (BOUNDARY_DIR / "boundary.shp", "boundary.shp"),
    (BOUNDARY_DIR / "boundary.dbf", "boundary.dbf"),
    (BOUNDARY_DIR / "boundary.shx", "boundary.shx"),
    (BOUNDARY_DIR / "boundary.prj", "boundary.prj"),
    (STATIONS_CSV, "data/stations.csv"),
    (EXCEL_PATH,   "results/final_N33/excel/*_Results.xlsx"),
]:
    if p is None or not Path(p).exists():
        errors.append(f"  MISSING: {label}")
if errors:
    print("\nERROR — required input files not found:")
    for e in errors:
        print(e)
    sys.exit(1)

print(f"\n  Boundary   : {BOUNDARY_DIR}")
print(f"  Stations   : {STATIONS_CSV.name}")
print(f"  Excel      : {EXCEL_PATH.name}")
print(f"  Compare    : {COMP_DIR}")
print(f"  Single     : {SINGLE_DIR}")
print(f"  REGEN_MAIN : {REGEN_MAIN}")
print()

# ── Load inputs ───────────────────────────────────────────────────────────────
print("Loading data …")
comp4_df = pd.read_excel(
    EXCEL_PATH,
    sheet_name="S7 4-Method Comparison",
    header=1, skiprows=[0],
)
comp4_df = comp4_df[comp4_df["Station"].notna()].copy()
comp4_df["Station"] = comp4_df["Station"].astype(str)
print(f"  Trend rows : {len(comp4_df)}  "
      f"Scales: {comp4_df['Scale'].unique().tolist()}")

coords_df = pd.read_csv(STATIONS_CSV, dtype=str)
coords_df["lat"] = coords_df["lat"].astype(float)
coords_df["lon"] = coords_df["lon"].astype(float)
print(f"  Stations   : {len(coords_df)}")

# ── Import v5 modules ─────────────────────────────────────────────────────────
from rta_v5.spatial_publication_q1_v5 import (
    fig_q1_spatial_trend_v5,
    fig_compare_v5,
    fig_single_v5,
)
from rta_v5.spatial_validation_v5 import (
    run_loocv_all, load_field_sig,
)
from rta_v5.spatial_export_v5 import (
    write_fig_metadata, write_boundary_config,
    write_spatial_methods, write_validation_excel,
)
from rta_v5.spatial_interpolation_v5 import load_boundary

# ── Scale-suffix mapping ──────────────────────────────────────────────────────
_SCALES = {
    "Annual (Jan–Dec)":     "",
    "Wet Season (May–Oct)": "_Wet",
    "Dry Season (Nov–Apr)": "_Dry",
}

# ── [Optional] Regenerate 5-panel figures ────────────────────────────────────
if REGEN_MAIN:
    print("\n── LOOCV — all scales (for 5-panel figures) ─────────────────────")
    loocv_all, best_methods, _method_cmp = run_loocv_all(
        comp4_df, coords_df,
        scale_keys=list(_SCALES),
    )
    all_loocv_rows: list[dict] = []
    best_methods_fig: dict[str, str] = {}
    _STEM_BASE = "Fig_Q1_SpatialTrend_v5"

    for scale, suffix in _SCALES.items():
        print(f"\n── {scale} ─────────────────────────────────────────────────")
        rows, bm, _ = fig_q1_spatial_trend_v5(
            comp4_df=comp4_df, coords_df=coords_df,
            boundary_dir=BOUNDARY_DIR, out_dir=PUB_DIR,
            stem=f"{_STEM_BASE}{suffix}", period=PERIOD,
            scale_key=scale, dpi=DPI,
        )
        all_loocv_rows.extend(rows)
        best_methods_fig[scale] = bm

    _annual_cmp = _method_cmp.get("Annual (Jan–Dec)", {})
    write_validation_excel(all_loocv_rows, {"Annual (Jan–Dec)": _annual_cmp}, VAL_DIR)
    write_boundary_config(MAN_DIR)
    write_spatial_methods(
        out_dir=MAN_DIR, loocv_rows=all_loocv_rows,
        best_methods=best_methods_fig, all_metrics=_annual_cmp,
        period=PERIOD, n_stations=int(comp4_df["Station"].nunique()),
        scale_key="Annual (Jan–Dec)",
    )
    polys = load_boundary(BOUNDARY_DIR)
    write_fig_metadata(
        out_dir=PUB_DIR, stem=_STEM_BASE,
        loocv_rows=all_loocv_rows, best_methods=best_methods_fig,
        all_metrics={"Annual (Jan–Dec)": _annual_cmp},
        field_sig_df=load_field_sig(str(EXCEL_PATH)),
        n_stations=int(comp4_df["Station"].nunique()),
        n_polygons=len(polys), period=PERIOD, grid_n=120, z_vabs=2.6,
    )

# ── Comparison figures ────────────────────────────────────────────────────────
print("\n── Comparison figures ───────────────────────────────────────────────")

_COMPARE_SPECS = [
    {
        "stem_base": "Fig_Compare_MK_vs_MMK",
        "col_a": "MK_Z",    "sig_a": "MK_sig",
        "title_a": "(a) Standard MK — Z Statistic",
        "col_b": "MMK_Z",   "sig_b": "MMK_sig",
        "title_b": "(b) Modified MK — Z Statistic",
    },
    {
        "stem_base": "Fig_Compare_PW_vs_TFPW",
        "col_a": "PW_Z",    "sig_a": "PW_sig",
        "title_a": "(a) PW-MK — Z Statistic",
        "col_b": "TFPW_Z",  "sig_b": "TFPW_sig",
        "title_b": "(b) TFPW-MK — Z Statistic",
    },
]

for spec in _COMPARE_SPECS:
    for scale, suffix in _SCALES.items():
        stem = spec["stem_base"] + suffix
        print(f"\n  {stem}")
        fig_compare_v5(
            comp4_df=comp4_df, coords_df=coords_df,
            boundary_dir=BOUNDARY_DIR, out_dir=COMP_DIR,
            stem=stem, period=PERIOD, scale_key=scale,
            col_a=spec["col_a"], sig_a=spec["sig_a"], title_a=spec["title_a"],
            col_b=spec["col_b"], sig_b=spec["sig_b"], title_b=spec["title_b"],
            dpi=DPI,
        )

# ── Single-method figures ─────────────────────────────────────────────────────
print("\n── Single-method figures ────────────────────────────────────────────")

_SINGLE_SPECS = [
    {
        "stem_base":   "Fig_Standard_MK",
        "col":         "MK_Z",
        "sig_col":     "MK_sig",
        "panel_title": "Standard MK — Z Statistic",
        "is_slope":    False,
    },
    {
        "stem_base":   "Fig_Modified_MK",
        "col":         "MMK_Z",
        "sig_col":     "MMK_sig",
        "panel_title": "Modified MK — Z Statistic",
        "is_slope":    False,
    },
    {
        "stem_base":   "Fig_PW_MK",
        "col":         "PW_Z",
        "sig_col":     "PW_sig",
        "panel_title": "PW-MK — Z Statistic",
        "is_slope":    False,
    },
    {
        "stem_base":   "Fig_TFPW_MK",
        "col":         "TFPW_Z",
        "sig_col":     "TFPW_sig",
        "panel_title": "TFPW-MK — Z Statistic",
        "is_slope":    False,
    },
    {
        "stem_base":   "Fig_Sen_Slope",
        "col":         "MK_slope",
        "sig_col":     "MK_sig",
        "panel_title": "Sen's Slope — mm yr⁻¹",
        "is_slope":    True,
    },
]

for spec in _SINGLE_SPECS:
    for scale, suffix in _SCALES.items():
        stem = spec["stem_base"] + suffix
        print(f"\n  {stem}")
        fig_single_v5(
            comp4_df=comp4_df, coords_df=coords_df,
            boundary_dir=BOUNDARY_DIR, out_dir=SINGLE_DIR,
            stem=stem, period=PERIOD, scale_key=scale,
            col=spec["col"], sig_col=spec["sig_col"],
            panel_title=spec["panel_title"],
            is_slope=spec["is_slope"],
            dpi=DPI,
        )

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 68)
print("  v5 complete.")
print(f"  comparison_maps/    : {COMP_DIR}")
print(f"  single_method_maps/ : {SINGLE_DIR}")
if REGEN_MAIN:
    print(f"  publication_maps/   : {PUB_DIR}")
print("=" * 68)
