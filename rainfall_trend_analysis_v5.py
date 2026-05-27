"""
rainfall_trend_analysis_v5.py — Province-independent Q1 spatial mapping
orchestrator (v5).

READS  (no statistical recomputation):
  results/final_N33/excel/*_Results.xlsx    — trend results archive
  boundaries/current_boundary/              — boundary.shp / .dbf / .shx / .prj
  data/stations.csv                         — station_id, lat, lon, altitude

WRITES:
  results/final_N33_v5/publication_maps_v51/
    MK_vs_MMK/
      Fig_Compare_MK_vs_MMK.{png,tif,pdf,svg}       × 3 scales
    PW_vs_TFPW/
      Fig_Compare_PW_vs_TFPW.{png,tif,pdf,svg}      × 3 scales
    Individual_Methods/
      Fig_Standard_MK.{png,tif,pdf,svg}             × 3 scales
      Fig_Modified_MK.{png,tif,pdf,svg}             × 3 scales
      Fig_PW_MK.{png,tif,pdf,svg}                   × 3 scales
      Fig_TFPW_MK.{png,tif,pdf,svg}                 × 3 scales
      Fig_Sen_Slope.{png,tif,pdf,svg}               × 3 scales

  [REGEN_MAIN=True only]
  results/final_N33_v5/publication_maps_v51/
    annual/  Fig_Q1_SpatialTrend_v5.{png,tif,pdf,svg}
    wet/     Fig_Q1_SpatialTrend_v5.{png,tif,pdf,svg}
    dry/     Fig_Q1_SpatialTrend_v5.{png,tif,pdf,svg}
    Fig_Metadata_Q1.txt

SAFETY:
  v4 files and results/final_N33/ are untouched.
  results/final_N33_v5/publication_maps/    NOT overwritten.
  results/final_N33_v5/comparison_maps/     NOT overwritten (legacy, kept as-is).
  results/final_N33_v5/single_method_maps/  NOT overwritten (legacy, kept as-is).
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
PUB_DIR      = V5_ROOT / "publication_maps_v51"   # top-level; subfolders below
# ── Subdirectories under publication_maps_v51/ ────────────────────────────────
MK_MMK_DIR   = PUB_DIR / "MK_vs_MMK"
PW_TFPW_DIR  = PUB_DIR / "PW_vs_TFPW"
INDIV_DIR    = PUB_DIR / "Individual_Methods"
ROW4_DIR     = PUB_DIR / "comparison_row"
SENS_ROW_DIR = PUB_DIR / "senslope_row"
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
print(f"  Exports    : {PUB_DIR}")
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
    fig_4method_row_v5,
    fig_senslope_row_v5,
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
_SCALE_DIRS = {
    "Annual (Jan–Dec)":     PUB_DIR / "annual",
    "Wet Season (May–Oct)": PUB_DIR / "wet",
    "Dry Season (Nov–Apr)": PUB_DIR / "dry",
}
_STEM_BASE = "Fig_Q1_SpatialTrend_v5"

if REGEN_MAIN:
    print("\n── LOOCV — all scales (for 5-panel figures) ─────────────────────")
    loocv_all, best_methods, _method_cmp = run_loocv_all(
        comp4_df, coords_df,
        scale_keys=list(_SCALES),
    )
    all_loocv_rows: list[dict] = []
    best_methods_fig: dict[str, str] = {}

    for scale in _SCALES:
        print(f"\n── {scale} ─────────────────────────────────────────────────")
        rows, bm, _ = fig_q1_spatial_trend_v5(
            comp4_df=comp4_df, coords_df=coords_df,
            boundary_dir=BOUNDARY_DIR, out_dir=_SCALE_DIRS[scale],
            stem=_STEM_BASE, period=PERIOD,
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
        out_dir=PUB_DIR, stem=_STEM_BASE,          # metadata at PUB_DIR root
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
        "out_dir":   MK_MMK_DIR,
        "stem_base": "Fig_Compare_MK_vs_MMK",
        "col_a": "MK_Z",    "sig_a": "MK_sig",
        "title_a": "(a) Standard MK — Z Statistic",
        "col_b": "MMK_Z",   "sig_b": "MMK_sig",
        "title_b": "(b) Modified MK — Z Statistic",
    },
    {
        "out_dir":   PW_TFPW_DIR,
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
            boundary_dir=BOUNDARY_DIR, out_dir=spec["out_dir"],
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
            boundary_dir=BOUNDARY_DIR, out_dir=INDIV_DIR,
            stem=stem, period=PERIOD, scale_key=scale,
            col=spec["col"], sig_col=spec["sig_col"],
            panel_title=spec["panel_title"],
            is_slope=spec["is_slope"],
            dpi=DPI,
        )

# ── 4-method comparison row figures ──────────────────────────────────────────
print("\n── 4-method row figures ─────────────────────────────────────────────")

_ROW4_STEMS = {
    "Annual (Jan–Dec)":     ("annual", "Fig_4Method_Row"),
    "Wet Season (May–Oct)": ("wet",    "Fig_4Method_Row_Wet"),
    "Dry Season (Nov–Apr)": ("dry",    "Fig_4Method_Row_Dry"),
}

for scale, (subdir, stem) in _ROW4_STEMS.items():
    print(f"\n  {stem}  ({scale})")
    fig_4method_row_v5(
        comp4_df=comp4_df, coords_df=coords_df,
        boundary_dir=BOUNDARY_DIR,
        out_dir=ROW4_DIR / subdir,
        stem=stem, period=PERIOD,
        scale_key=scale, dpi=DPI,
    )

# ── Sen's slope all-scales row figure ────────────────────────────────────────
print("\n── Sen's slope row figure ───────────────────────────────────────────")
fig_senslope_row_v5(
    comp4_df=comp4_df, coords_df=coords_df,
    boundary_dir=BOUNDARY_DIR,
    out_dir=SENS_ROW_DIR,
    stem="Fig_SenSlope_AllScales_Row",
    period=PERIOD,
    scale_keys=list(_SCALES.keys()),
    dpi=DPI,
)

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 68)
print("  v5 complete.")
print(f"  MK_vs_MMK/          : {MK_MMK_DIR}")
print(f"  PW_vs_TFPW/         : {PW_TFPW_DIR}")
print(f"  Individual_Methods/ : {INDIV_DIR}")
print(f"  comparison_row/     : {ROW4_DIR}")
print(f"  senslope_row/       : {SENS_ROW_DIR}")
if REGEN_MAIN:
    print(f"  annual/             : {_SCALE_DIRS['Annual (Jan–Dec)']}")
    print(f"  wet/                : {_SCALE_DIRS['Wet Season (May–Oct)']}")
    print(f"  dry/                : {_SCALE_DIRS['Dry Season (Nov–Apr)']}")
print("=" * 68)
