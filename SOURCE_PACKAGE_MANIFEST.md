# Source Package Manifest
**Package:** `prachuap_v1.0_runnable.zip`  
**Release:** v1.0.0  
**Total files:** 49  
**Total source lines:** 17,571  
**Uncompressed size:** 1.5 MB  
**Compressed size:** 337 KB

---

## Execution Order

| Step | Command | Runtime | Outputs |
|---|---|---|---|
| 1 | `python rainfall_trend_analysis_v4.py data/ --no-resume` | ~5–15 min | 18 PNG, 18 PDF figures; 9-sheet Excel; Research Summary MD |
| 2 | `python generate_trend_comparison_analysis.py` | ~2–5 min | 8 workbooks + 10 comparison figures + 7 manuscript tables |
| 3 | `python generate_all_vs_mk_workbook.py` | ~1 min | `Trend_Method_Comparison_All_vs_MK.xlsx` |
| 4 | `python generate_tfpw_audit.py` | ~1 min | `TFPW_Audit.xlsx` |
| 5 | `python generate_reviewer_summary.py` | ~1 min | `Reviewer_Summary.xlsx` |
| 6 | `python generate_final_validation.py` | ~1 min | `Disagreement_Stations.xlsx`, `SenSlope_Comparison.xlsx`, `Final_Methodological_Assessment.xlsx` |

---

## Required Inputs

| File | Path in package | Description |
|---|---|---|
| Daily rainfall CSV | `data/Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv` | 12,418 rows × 15 cols; 12 stations; 1981–2014 |
| Station coordinates | `data/station_coordinates.csv` | 128 stations; WGS84 lat/lon/altitude |

---

## Generated Outputs (after all 6 steps)

| Type | Count | Location |
|---|---|---|
| Publication figures PNG (Fig1–14 + spatial) | 18 | `data/` |
| Publication figures PDF | 18 | `data/` |
| Comparison figures PNG+PDF+SVG | 30 | `results/final_N33_v5/Trend_Method_Comparison/Figures/` |
| Primary Excel workbook (9 sheets) | 1 | `data/` |
| Method comparison workbooks | 8 | `results/final_N33_v5/Trend_Method_Comparison/Excel/` |
| Manuscript tables CSV + XLSX | 14 | `results/final_N33_v5/Trend_Method_Comparison/Tables/` |
| Additional analysis workbooks | 3 | `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/` |
| Manuscript templates (MD) | 9 | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/` |

---

## File Inventory

### Top-Level Scripts

| File | Lines | Purpose | Step |
|---|---|---|---|
| `rainfall_trend_analysis_v4.py` | 465 | Primary pipeline orchestrator: QC → aggregation → autocorrelation → MK/MMK/PW/TFPW → field significance → 18 figures → Excel → Markdown | 1 |
| `rainfall_trend_analysis_v5.py` | 322 | Optional Q1 spatial map orchestrator; reads v4 Excel output; requires geopandas | optional |
| `generate_trend_comparison_analysis.py` | 56 | Entry point for method comparison master analysis | 2 |
| `generate_all_vs_mk_workbook.py` | 675 | Generates All-vs-MK comparison workbook | 3 |
| `generate_tfpw_audit.py` | 506 | Generates TFPW detailed audit workbook | 4 |
| `generate_reviewer_summary.py` | 507 | Generates reviewer-ready summary workbook | 5 |
| `generate_final_validation.py` | 943 | Generates disagreement, slope comparison, and methodological assessment workbooks | 6 |

### Configuration Files

| File | Purpose |
|---|---|
| `requirements.txt` | pip dependencies with tested version annotations |
| `environment.yml` | conda environment specification |
| `README_RUN.md` | Quick-run guide with commands, expected outputs, validation table |

### rta/ Core Package (19 modules)

| Module | Lines | Purpose |
|---|---|---|
| `rta/config.py` | 180 | Shared constants: colour palette, DPI, Z-thresholds, season definitions |
| `rta/io.py` | 301 | CSV/coordinate file discovery, loading, missing-value QC |
| `rta/aggregation.py` | 323 | Annual / wet-season / dry-season / monthly aggregation with completeness thresholds |
| `rta/autocorr.py` | 38 | Lag-k Pearson autocorrelation; ACF vector; significance test |
| `rta/trend_tests.py` | 343 | Standard Mann-Kendall test; Sen's slope + 95% CI; tie correction |
| `rta/batch.py` | 285 | Batch runner: all stations × scales × methods (MK, MMK, PW, TFPW) |
| `rta/pw.py` | 86 | Prewhitening MK (Yue & Wang 2004) |
| `rta/tfpw.py` | 108 | Trend-Free Prewhitening MK (Yue et al. 2002) |
| `rta/field_sig.py` | 285 | Walker (1914) binomial test + Livezey-Chen (1983) Monte Carlo (10,000 iter, seed=42) |
| `rta/field_significance.py` | 250 | Extended field significance implementation |
| `rta/checkpoint.py` | 109 | 6-step pickle checkpoint/resume system |
| `rta/excel_output.py` | 618 | 9-sheet Excel workbook writer with full cell styling |
| `rta/markdown.py` | 511 | Research summary Markdown writer |
| `rta/spatial.py` | 145 | Coordinate loading, validation, coverage reporting |
| `rta/spatial_maps.py` | ~20 | Re-export wrapper for spatial figure functions |
| `rta/trend_comparison_analysis.py` | 1,709 | Method comparison engine: 8 workbooks + 10 figures + 7 tables + 9 MD templates |
| `rta/trend_method_comparison.py` | 1,078 | Extended comparison figures (FigC01–FigC10) |
| `rta/__init__.py` | ~10 | Package init |

### rta/figures/ Subpackage (13 modules)

| Module | Lines | Figures produced |
|---|---|---|
| `timeseries.py` | 214 | Fig1 (Annual time series), Fig2 (Wet/Dry time series) |
| `bars.py` | 93 | Fig3 (Sen's slope bar charts, 3 temporal scales) |
| `comparison.py` | 155 | Fig4 (MK vs MMK comparison, 4 panels) |
| `heatmaps.py` | 82 | Fig5 (Significance heatmap, all 4 methods) |
| `acf_plots.py` | 155 | Fig6 (Autocorrelation), Fig12 (ACF diagnostics) |
| `climatology.py` | 89 | Fig7 (Monthly climatology per station) |
| `spatial.py` | 164 | Fig8 (Index-based spatial summary, no coordinates) |
| `taylor.py` | 215 | Fig9 (Taylor diagram) |
| `method_comparison.py` | 352 | Fig10 (Z-matrix heatmap, 4 methods), Fig11 (Z-scatter, 3 panels) |
| `field_sig_plot.py` | 259 | Fig13 (Field significance bar chart) |
| `spatial_maps.py` | 684 | Fig14 (geographic MMK), Fig_SpatialStation, Fig_SpatialMethods, Fig_SpatialFieldSig, Fig_SpatialFull |
| `helpers.py` | ~30 | Shared title/savefig utilities |
| `figures/__init__.py` | ~5 | Subpackage init |

### rta_v5/ Package (6 modules, optional)

| Module | Purpose |
|---|---|
| `spatial_interpolation_v5.py` | IDW/kriging spatial interpolation |
| `spatial_publication_q1_v5.py` | Q1-standard figure assembly |
| `spatial_layout_v5.py` | Multi-panel layout utilities |
| `spatial_export_v5.py` | Multi-format export (PNG/TIF/PDF/SVG) |
| `spatial_validation_v5.py` | LOOCV interpolation validation |
| `rta_v5/__init__.py` | Package init |

### Input Data

| File | Size | Description |
|---|---|---|
| `data/Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv` | 715 KB | 12,418 rows; YEAR, MONTH, DAY + stations 500001–500301 |
| `data/station_coordinates.csv` | 1.2 KB | Station, Lat, Lon, Altitude for 128 stations |

---

## Validation Results (from package run)

| Metric | Expected | Verified |
|---|---|---|
| Standard MK significant (p<0.05) | 6 / 36 | **6 / 36** ✅ |
| Modified MK significant | 4 / 36 | **4 / 36** ✅ |
| PW-MK significant | 3 / 36 | **3 / 36** ✅ |
| TFPW-MK significant | 7 / 36 | **7 / 36** ✅ |
| Annual field significance | Not significant | **Walker p=0.460, LC p=0.436** ✅ |
| Wet Season field significance | Not significant | **Walker p=0.118, LC p=0.099** ✅ |
| Dry Season field significance | Significant | **Walker p=0.020, LC p=0.016** ✅ |
| PNG figures produced (Step 1) | 18 | **18** ✅ |
| PDF figures produced (Step 1) | 18 | **18** ✅ |
| Excel workbook (Step 1) | 9 sheets | **9 sheets** ✅ |
| Pipeline exit code | 0 | **0** ✅ |
