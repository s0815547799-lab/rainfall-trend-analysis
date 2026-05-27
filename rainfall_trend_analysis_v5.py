"""
rainfall_trend_analysis_v5.py — Province-independent Q1 spatial mapping
orchestrator (v5).

READS  (no statistical recomputation):
  results/final_N33/excel/*_Results.xlsx    — trend results archive
  boundaries/current_boundary/              — boundary.shp / .dbf / .shx / .prj
  data/stations.csv                         — station_id, lat, lon, altitude

WRITES:
  results/final_N33_v5/publication_maps_v5/
    Fig_Q1_SpatialTrend_v5.{png,tif,pdf,svg}       Annual
    Fig_Q1_SpatialTrend_v5_Wet.{png,tif,pdf,svg}   Wet season
    Fig_Q1_SpatialTrend_v5_Dry.{png,tif,pdf,svg}   Dry season
    Fig_Metadata_Q1.txt
    validation/LOOCV.xlsx
    validation/Interpolation_Comparison.xlsx
    docs/Boundary_Config_v5.md
    docs/Spatial_Methods_Q1_v5.md

SAFETY:
  v4 files and results/final_N33/ are untouched.
  MK / MMK / PW / TFPW / Sen slope statistics are NOT recomputed.

Run:
    python rainfall_trend_analysis_v5.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).parent
BOUNDARY_DIR  = ROOT / "boundaries" / "current_boundary"
STATIONS_CSV  = ROOT / "data" / "stations.csv"
FINAL_N33     = ROOT / "results" / "final_N33"
OUT_BASE      = ROOT / "results" / "final_N33_v5" / "publication_maps_v5"
PERIOD        = "1981–2014"
DPI           = 600

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
    print("\nFix the above before running v5.")
    sys.exit(1)

print(f"\n  Boundary : {BOUNDARY_DIR}")
print(f"  Stations : {STATIONS_CSV.name}")
print(f"  Excel    : {EXCEL_PATH.name}")
print(f"  Output   : {OUT_BASE}")
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
print(f"  Trend rows: {len(comp4_df)}  "
      f"Scales: {comp4_df['Scale'].unique().tolist()}")

coords_df = pd.read_csv(STATIONS_CSV, dtype=str)
coords_df["lat"] = coords_df["lat"].astype(float)
coords_df["lon"] = coords_df["lon"].astype(float)
print(f"  Stations in coords file: {len(coords_df)}")

# Stem for output filenames
_STEM_BASE = "Fig_Q1_SpatialTrend_v5"

# ── Import v5 modules (after path validation) ─────────────────────────────────
from rta_v5.spatial_publication_q1_v5 import fig_q1_spatial_trend_v5
from rta_v5.spatial_validation_v5 import (
    run_loocv_all, load_field_sig, format_loocv_table
)
from rta_v5.spatial_export_v5 import (
    write_fig_metadata, write_boundary_config,
    write_spatial_methods, write_validation_excel,
)
from rta_v5.spatial_interpolation_v5 import load_boundary

# ── LOOCV for all scales ──────────────────────────────────────────────────────
print("\n── LOOCV — all scales ──────────────────────────────────────────────")
loocv_all, best_methods, _method_cmp = run_loocv_all(
    comp4_df, coords_df,
    scale_keys=[
        "Annual (Jan–Dec)",
        "Wet Season (May–Oct)",
        "Dry Season (Nov–Apr)",
    ],
)

# ── Generate figures ──────────────────────────────────────────────────────────
_SCALE_SUFFIX = {
    "Annual (Jan–Dec)":   "",
    "Wet Season (May–Oct)": "_Wet",
    "Dry Season (Nov–Apr)": "_Dry",
}

all_loocv_rows: list[dict] = []
best_methods_fig: dict[str, str] = {}
all_metrics_fig:  dict[str, dict] = {}

for scale, suffix in _SCALE_SUFFIX.items():
    print(f"\n── {scale} ─────────────────────────────────────────────────────")
    stem = f"{_STEM_BASE}{suffix}"
    rows, bm, metrics = fig_q1_spatial_trend_v5(
        comp4_df     = comp4_df,
        coords_df    = coords_df,
        boundary_dir = BOUNDARY_DIR,
        out_dir      = OUT_BASE,
        stem         = stem,
        period       = PERIOD,
        scale_key    = scale,
        dpi          = DPI,
    )
    all_loocv_rows.extend(rows)
    best_methods_fig[scale] = bm

# _method_cmp from run_loocv_all: {scale: {method: {RMSE,…}}}
# Use annual slice for the IDW vs RBF comparison table
_annual_cmp = _method_cmp.get("Annual (Jan–Dec)", {})

# ── Validation Excel ──────────────────────────────────────────────────────────
print("\n── Validation tables ────────────────────────────────────────────────")
write_validation_excel(all_loocv_rows, {"Annual (Jan–Dec)": _annual_cmp}, OUT_BASE)

# ── Documentation ─────────────────────────────────────────────────────────────
print("\n── Documentation ────────────────────────────────────────────────────")
docs_dir = OUT_BASE / "docs"
write_boundary_config(docs_dir)
write_spatial_methods(
    out_dir      = docs_dir,
    loocv_rows   = all_loocv_rows,
    best_methods = best_methods_fig,
    all_metrics  = _annual_cmp,
    period       = PERIOD,
    n_stations   = int(comp4_df["Station"].nunique()),
    scale_key    = "Annual (Jan–Dec)",
)

# ── Fig_Metadata_Q1.txt ───────────────────────────────────────────────────────
print("\n── Figure metadata ──────────────────────────────────────────────────")
polys = load_boundary(BOUNDARY_DIR)
field_sig_df = load_field_sig(str(EXCEL_PATH))

write_fig_metadata(
    out_dir      = OUT_BASE,
    stem         = _STEM_BASE,
    loocv_rows   = all_loocv_rows,
    best_methods = best_methods_fig,
    all_metrics  = {"Annual (Jan–Dec)": _annual_cmp},
    field_sig_df = field_sig_df,
    n_stations   = int(comp4_df["Station"].nunique()),
    n_polygons   = len(polys),
    period       = PERIOD,
    grid_n       = 120,
    z_vabs       = 2.6,
)

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 68)
print("  v5 complete.")
print(f"  Output: {OUT_BASE}")
print("=" * 68)
