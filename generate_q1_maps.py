"""
generate_q1_maps.py — Generate Q1 publication spatial maps from final_N33 archive.

Reads:
  results/final_N33/excel/*_Results.xlsx   (4-method comparison data)
  station_coordinates.csv                   (WGS84 coordinates)
  30_amarea_prachuap_khiri_khan.shp         (province shapefile)

Writes:
  results/final_N33/publication_maps/
    Fig_Q1_SpatialTrend.png/.tif/.pdf/.svg       (Annual)
    Fig_Q1_SpatialTrend_Wet.png/.tif/.pdf/.svg   (Wet season)
    Fig_Q1_SpatialTrend_Dry.png/.tif/.pdf/.svg   (Dry season)
    validation/
      Interpolation_Comparison.xlsx
      LOOCV.xlsx
    Spatial_Methods_Q1.md

Run from repository root:
    python generate_q1_maps.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).parent
SHP_PATH  = ROOT / "30_amarea_prachuap_khiri_khan.shp"
COORDS_CSV = ROOT / "station_coordinates.csv"
FINAL_N33 = ROOT / "results" / "final_N33"

EXCEL_PATH = next(
    (FINAL_N33 / "excel").glob("*_Results.xlsx"), None
)
OUT_DIR = FINAL_N33 / "publication_maps"
PERIOD  = "1981–2014"
DPI     = 600

# ── Validate required files ───────────────────────────────────────────────────
missing = []
for p, label in [
    (SHP_PATH,   "province shapefile"),
    (COORDS_CSV, "station_coordinates.csv"),
    (EXCEL_PATH, "Results.xlsx (final_N33/excel/)"),
]:
    if p is None or not Path(p).exists():
        missing.append(f"  MISSING: {label}")
if missing:
    print("ERROR — required files not found:")
    for m in missing:
        print(m)
    sys.exit(1)

print(f"  Shapefile : {SHP_PATH.name}")
print(f"  Coords    : {COORDS_CSV.name}")
print(f"  Excel     : {EXCEL_PATH.name}")
print(f"  Output    : {OUT_DIR}")
print()

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading trend data from Excel …")
comp4_df = pd.read_excel(
    EXCEL_PATH, sheet_name="S7 4-Method Comparison", header=1, skiprows=[0]
)
comp4_df = comp4_df[comp4_df["Station"].notna()].copy()
comp4_df["Station"] = comp4_df["Station"].astype(str)
print(f"  {len(comp4_df)} rows, scales: {comp4_df['Scale'].unique().tolist()}")

coords_df = pd.read_csv(COORDS_CSV, dtype=str)
coords_df["Lat"] = coords_df["Lat"].astype(float)
coords_df["Lon"] = coords_df["Lon"].astype(float)

# Prefix for output filenames (Excel stem already contains "Output_TrendV4_…")
PREFIX = EXCEL_PATH.stem.replace("_Results", "")

# Import after path validation so import errors are distinct
from rta.spatial_publication_q1 import (
    fig_q1_spatial_trend,
    write_spatial_manuscript,
)
from rta.spatial_interpolation import save_validation_tables

# ── Generate figures for all three scales ─────────────────────────────────────
scales = [
    "Annual (Jan–Dec)",
    "Wet Season (May–Oct)",
    "Dry Season (Nov–Apr)",
]

all_loocv_rows  = []
all_metrics_ref = {}   # from annual run (for manuscript)
best_method_ref = "IDW"

for scale in scales:
    print(f"\n── {scale} ──────────────────────────────────────────────────")
    loocv_rows, best_method, all_metrics = fig_q1_spatial_trend(
        comp4_df   = comp4_df,
        coords_df  = coords_df,
        shp_path   = SHP_PATH,
        out_dir    = OUT_DIR,
        prefix     = PREFIX,
        period     = PERIOD,
        scale_key  = scale,
        dpi        = DPI,
    )
    all_loocv_rows.extend(loocv_rows)
    if scale == "Annual (Jan–Dec)":
        all_metrics_ref = all_metrics
        best_method_ref = best_method

# ── Validation tables ─────────────────────────────────────────────────────────
print("\n── Validation tables ────────────────────────────────────────────────")
val_dir = OUT_DIR / "validation"

# Interpolation_Comparison.xlsx  (IDW vs RBF on annual MMK_Z)
save_validation_tables(
    all_metrics  = all_metrics_ref,
    loocv_detail = all_loocv_rows,
    out_dir      = OUT_DIR,
)

# ── Manuscript text ───────────────────────────────────────────────────────────
print("\n── Manuscript text ──────────────────────────────────────────────────")
stns = comp4_df["Station"].unique().tolist()
write_spatial_manuscript(
    loocv_all   = all_loocv_rows,
    best_method = best_method_ref,
    all_metrics = all_metrics_ref,
    out_dir     = OUT_DIR,
    prefix      = PREFIX,
    period      = PERIOD,
    n_stations  = len(stns),
    scale_key   = "Annual (Jan–Dec)",
)

print("\n✓ All outputs written to:", OUT_DIR)
print("  Run complete.")
