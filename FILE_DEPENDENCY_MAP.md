# File Dependency Map
## Prachuap Khiri Khan Rainfall Trend Analysis
**Period:** 1981–2014 | **Stations:** 12 (IDs 500001–500301) | **Version:** v4 pipeline (primary)

---

## Table of Contents
1. [Repository Layout](#repository-layout)
2. [Top-Level Scripts](#top-level-scripts)
   - [rainfall_trend_analysis_v4.py](#rainfall_trend_analysis_v4py) — primary pipeline
   - [rainfall_trend_analysis_v3.py](#rainfall_trend_analysis_v3py) — legacy standalone
   - [rainfall_trend_analysis_v5.py](#rainfall_trend_analysis_v5py) — Q1 spatial orchestrator
   - [generate_trend_comparison_analysis.py](#generate_trend_comparison_analysispy)
   - [generate_trend_comparison.py](#generate_trend_comparisonpy)
   - [generate_all_vs_mk_workbook.py](#generate_all_vs_mk_workbookpy)
   - [generate_tfpw_audit.py](#generate_tfpw_auditpy)
   - [generate_reviewer_summary.py](#generate_reviewer_summarypy)
   - [generate_final_validation.py](#generate_final_validationpy)
   - [generate_q1_maps.py](#generate_q1_mapspy)
   - [calval_split.py](#calval_splitpy)
   - [Comparative_4MMK.py](#comparative_4mmkpy)
3. [rta/ Package Modules](#rta-package-modules)
4. [rta_v5/ Package Modules](#rta_v5-package-modules)
5. [Data Files](#data-files)
6. [Checkpoint Files](#checkpoint-files)
7. [Execution Order](#execution-order)
8. [Dependency Graph](#dependency-graph)

---

## Repository Layout

```
rainfall-trend-analysis/
├── rainfall_trend_analysis_v3.py      Legacy standalone pipeline
├── rainfall_trend_analysis_v4.py      PRIMARY pipeline (rta package)
├── rainfall_trend_analysis_v5.py      Q1 spatial publication system
├── generate_trend_comparison_analysis.py   Post-processor: TCA workbooks + figures
├── generate_trend_comparison.py        Post-processor: Q1 single workbook
├── generate_all_vs_mk_workbook.py      Post-processor: All-vs-MK workbook
├── generate_tfpw_audit.py              Post-processor: TFPW audit workbook
├── generate_reviewer_summary.py        Post-processor: Reviewer summary workbook
├── generate_final_validation.py        Post-processor: Methodological validation workbooks
├── generate_q1_maps.py                 Post-processor: Q1 geographic maps (first gen.)
├── calval_split.py                     OUT OF SCOPE — input files absent
├── Comparative_4MMK.py                 NON-FUNCTIONAL — requires statsmodels
├── Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv   Primary input
├── station_coordinates.csv             WGS84 coordinates for 128 stations
├── 30_amarea_prachuap_khiri_khan.shp/dbf/shx/prj  Province shapefile
├── rta/                               Core analysis package
├── rta_v5/                            v5 spatial publication package
├── checkpoints/                       Pickle resume files (6 steps)
├── results/
│   ├── final_N33/excel/               Canonical v4 Excel output archive
│   └── final_N33_v5/                  Post-processing outputs
│       ├── Trend_Method_Comparison/   TCA outputs (Excel + Figures + Manuscript)
│       ├── publication_maps_v51/      v5 spatial figures
│       └── Trend_Method_Comparison_Q1.xlsx
└── boundaries/current_boundary/       boundary.shp/.dbf/.shx/.prj (v5 input)
```

---

## Top-Level Scripts

---

### rainfall_trend_analysis_v4.py

**Purpose:** Primary end-to-end hydroclimatological trend analysis pipeline; runs all 4 MK variants, generates 14 publication figures, and writes a 9-sheet Excel workbook.

**Category:** pipeline-core

**Status:** Active

**Usage:**
```
python rainfall_trend_analysis_v4.py [folder] [--no-resume] [--no-pdf]
```

**Inputs:**
- Daily rainfall CSV (`.csv`; auto-discovered in target folder via `rta.io.find_csv()` — skips files prefixed `Output_`; prefers filenames containing "observed" or "rain")
- `station_coordinates.csv` (optional; auto-detected via `*coord*.csv` / `*station*.csv` glob; enables geographic spatial figures)

**Outputs (co-located with input CSV):**

*Backward-compatible v3-format outputs (prefix `Output_TrendV2_<basename>`):**
- `*_Fig1_AnnualTimeSeries.png/.pdf`
- `*_Fig2_WetDryTimeSeries.png/.pdf`
- `*_Fig3_SenSlope_AllScales.png/.pdf`
- `*_Fig4_MK_vs_MMK_Comparison.png/.pdf`
- `*_Fig5_Significance_Heatmap.png/.pdf`
- `*_Fig6_Autocorrelation.png/.pdf`
- `*_Fig7_MonthlyClimatology.png/.pdf`
- `*_Fig8_SpatialTrend_Summary.png/.pdf`
- `*_Results.xlsx` (6-sheet workbook: S1 Standard MK, S2 Modified MK, S3 MK vs MMK, S4 Sen's Slope, S5 Descriptive Stats, S6 Methods & References)
- `*_Research_Summary.md`

*New v4 outputs (prefix `Output_TrendV4_<basename>`):**
- `*_Fig9_TaylorDiagram.png/.pdf`
- `*_Fig10_ZComparisonMatrix.png/.pdf`
- `*_Fig11_MethodComparison.png/.pdf`
- `*_Fig12_ACF_Diagnostics.png/.pdf`
- `*_Fig13_FieldSignificance.png/.pdf`
- `*_Fig14_SpatialMaps.png/.pdf`
- `*_Fig_SpatialStation.png/.pdf` (when coordinates available)
- `*_Fig_SpatialMethods.png/.pdf` (when coordinates available)
- `*_Fig_SpatialFieldSig.png/.pdf` (when coordinates available)
- `*_Fig_SpatialFull.png/.pdf` (when coordinates available)
- `*_Results.xlsx` (9-sheet workbook: S1–S6 identical to v3 + S7 4-Method Comparison + S8 Field Significance + S9 Dry Season Validation)
- `*_Research_Summary.md`
- `*_DrySeasonValidation.txt`

*Checkpoint files (in `checkpoints/` subdirectory):*
- `checkpoints/ckpt_01_qc.pkl`
- `checkpoints/ckpt_02_aggregation.pkl`
- `checkpoints/ckpt_03_acf.pkl`
- `checkpoints/ckpt_04_trends.pkl`
- `checkpoints/ckpt_05_comparison.pkl`
- `checkpoints/ckpt_06_field_sig.pkl`

**Pipeline Steps:**
| Step | Checkpoint | Description |
|------|------------|-------------|
| 1 | `01_qc` | Load CSV + quality control (missing flags, IQR outliers, interpolation) |
| 2 | `02_aggregation` | Temporal aggregation (annual/wet/dry/monthly) + dry-season validation |
| 3 | `03_acf` | Lag-1 autocorrelation significance assessment |
| 4 | `04_trends` | Run all 4 methods × stations × scales |
| 5 | `05_comparison` | Build MK vs MMK and 4-method comparison tables |
| 6 | `06_field_sig` | Field significance (Walker + Livezey-Chen MC, 1000 permutations) |
| 7 | — | Load station coordinates (optional) |
| 8 | — | Generate Figs 1–8 (v3-compatible) |
| 9 | — | Generate Figs 9–14 + spatial variants (v4 new) |
| 10 | — | Write 9-sheet Excel |
| 11 | — | Write Research Summary Markdown |

**Upstream dependencies:** None (entry point of primary pipeline)

**Downstream consumers:**
- `rainfall_trend_analysis_v5.py` reads `results/final_N33/excel/*_Results.xlsx` (sheet "S7 4-Method Comparison")
- `generate_trend_comparison_analysis.py` reads `results/final_N33/excel/*_Results.xlsx`
- `generate_trend_comparison.py` reads `results/final_N33/excel/*_Results.xlsx`
- `generate_all_vs_mk_workbook.py` reads the Master workbook produced by `generate_trend_comparison_analysis.py` (which chains from v4 output)
- `generate_tfpw_audit.py` same chain
- `generate_reviewer_summary.py` same chain
- `generate_final_validation.py` same chain
- `generate_q1_maps.py` reads `results/final_N33/excel/*_Results.xlsx`

**rta package imports (all):**
`rta.config`, `rta.io`, `rta.aggregation`, `rta.autocorr`, `rta.trend_tests`, `rta.batch`, `rta.field_sig`, `rta.figures.timeseries`, `rta.figures.bars`, `rta.figures.comparison`, `rta.figures.heatmaps`, `rta.figures.acf_plots`, `rta.figures.climatology`, `rta.figures.spatial`, `rta.figures.taylor`, `rta.figures.method_comparison`, `rta.figures.field_sig_plot`, `rta.figures.spatial_maps`, `rta.excel_output`, `rta.markdown`

---

### rainfall_trend_analysis_v3.py

**Purpose:** Legacy single-file standalone pipeline; implements the identical MK/MMK/Sen's slope workflow as v4 but without the rta package, PW-MK, TFPW-MK, or field significance.

**Category:** legacy

**Status:** Legacy (still executable as a standalone; v4 also re-generates all v3-format outputs, making this script redundant for production runs)

**Usage:**
```
python rainfall_trend_analysis_v3.py
```
Prompts for folder path; falls back to `Path.cwd()`.

**Inputs:**
- Daily rainfall CSV (`.csv`; auto-discovered via embedded `find_csv()`)
- `station_coordinates.csv` (optional; enables Fig 8 geographic variant via graceful `rta` import fallback)

**Outputs (prefix `Output_TrendV2_<basename>`):**
- `*_Fig1_AnnualTimeSeries.png/.pdf` through `*_Fig8_SpatialTrend_Summary.png/.pdf`
- `*_Results.xlsx` (6 sheets)
- `*_Research_Summary.md`

When `_RTA_AVAILABLE = True` (rta package importable), v3 also optionally generates Figs 9–14 using the same figure modules as v4, writing them with the `Output_TrendV2_` prefix.

**Upstream dependencies:** None (self-contained)

**Downstream consumers:** None (v4 supersedes it)

---

### rainfall_trend_analysis_v5.py

**Purpose:** Province-independent Q1 spatial mapping orchestrator; reads pre-computed trend statistics from the v4 Excel archive and produces geographic interpolated publication maps without recomputing any statistics.

**Category:** post-processing

**Status:** Active (requires `geopandas` and `rta_v5` package; also requires `boundaries/current_boundary/` shapefiles)

**Usage:**
```
python rainfall_trend_analysis_v5.py
```

**Inputs:**
- `results/final_N33/excel/*_Results.xlsx` (resolved by glob; reads sheet "S7 4-Method Comparison" — produced by `rainfall_trend_analysis_v4.py`)
- `data/stations.csv` (columns: `station_id`, `lat`, `lon`, `altitude`)
- `boundaries/current_boundary/boundary.shp/.dbf/.shx/.prj` (WGS84 province boundary)

**Outputs (all under `results/final_N33_v5/publication_maps_v51/`):**

*Always generated:*
- `MK_vs_MMK/Fig_Compare_MK_vs_MMK[_Wet|_Dry].{png,tif,pdf,svg}` (3 scales)
- `PW_vs_TFPW/Fig_Compare_PW_vs_TFPW[_Wet|_Dry].{png,tif,pdf,svg}` (3 scales)
- `Individual_Methods/Fig_Standard_MK[_Wet|_Dry].{png,tif,pdf,svg}` (3 scales)
- `Individual_Methods/Fig_Modified_MK[_Wet|_Dry].{png,tif,pdf,svg}` (3 scales)
- `Individual_Methods/Fig_PW_MK[_Wet|_Dry].{png,tif,pdf,svg}` (3 scales)
- `Individual_Methods/Fig_TFPW_MK[_Wet|_Dry].{png,tif,pdf,svg}` (3 scales)
- `Individual_Methods/Fig_Sen_Slope[_Wet|_Dry].{png,tif,pdf,svg}` (3 scales)
- `comparison_row/[annual|wet|dry]/Fig_4Method_Row[_Wet|_Dry].{png,tif,pdf,svg}`
- `senslope_row/Fig_SenSlope_AllScales_Row.{png,tif,pdf,svg}`

*When `REGEN_MAIN = True` only:*
- `annual/Fig_Q1_SpatialTrend_v5.{png,tif,pdf,svg}`
- `wet/Fig_Q1_SpatialTrend_v5.{png,tif,pdf,svg}`
- `dry/Fig_Q1_SpatialTrend_v5.{png,tif,pdf,svg}`
- `Fig_Metadata_Q1.txt`
- `results/final_N33_v5/validation/` — LOOCV validation Excel files
- `results/final_N33_v5/manuscript/` — boundary config + spatial methods text

**Key constant:** `REGEN_MAIN = False` (default) suppresses the 5-panel main figures to avoid overwriting existing outputs.

**Upstream dependencies:** `rainfall_trend_analysis_v4.py` (must be run first to populate `results/final_N33/excel/`)

**Downstream consumers:** None (terminal output step)

**rta_v5 package imports:**
`rta_v5.spatial_publication_q1_v5`, `rta_v5.spatial_validation_v5`, `rta_v5.spatial_export_v5`, `rta_v5.spatial_interpolation_v5`

---

### generate_trend_comparison_analysis.py

**Purpose:** Runs the `TrendComparisonAnalysis` class to produce a comprehensive multi-workbook, multi-figure comparison of all 4 trend methods from the v4 Excel output.

**Category:** post-processing

**Status:** Active

**Usage:**
```
python generate_trend_comparison_analysis.py
```

**Inputs:**
- `results/final_N33/excel/*_Results.xlsx` — canonical v4 pipeline Excel (WB1; glob resolved)
- `data/reference/ebc6aee6-Rainfall_2Trend_Results.xlsx` (WB4; optional supplementary workbook with n_eff, Pettitt CP, significant-lag columns; path overridable via `WB4_PATH` env var)

**Outputs (all under `results/final_N33_v5/Trend_Method_Comparison/`):**
- `Excel/Master/Trend_Method_Comparison_Master.xlsx` — primary Master_DB sheet (consumed by all subsequent `generate_*.py` scripts)
- `Excel/Master/Trend_Method_Comparison_Tables.xlsx`
- `Excel/MK_Analysis/MK_Analysis.xlsx`
- `Excel/MMK_Analysis/MMK_Analysis.xlsx`
- `Excel/MMK_Analysis/MMK_vs_MK_Comparison.xlsx`
- `Excel/PW_MK_Analysis/PW_MK_Analysis.xlsx`
- `Excel/PW_MK_Analysis/PW_MK_vs_MK_Comparison.xlsx`
- `Excel/TFPW_MK_Analysis/TFPW_MK_Analysis.xlsx`
- `Excel/TFPW_MK_Analysis/TFPW_MK_vs_MK_Comparison.xlsx`
- `Tables/` — 7 × (`.xlsx` + `.csv`)
- `Figures/` — 10 × (`.png` + `.tiff` + `.pdf` + `.svg`) at 600 DPI
- `Manuscript/` — 9 × `.md` manuscript templates

**Upstream dependencies:** `rainfall_trend_analysis_v4.py`

**Downstream consumers:**
- `generate_all_vs_mk_workbook.py`
- `generate_tfpw_audit.py`
- `generate_reviewer_summary.py`
- `generate_final_validation.py`

**rta module:** `rta.trend_comparison_analysis.TrendComparisonAnalysis`

---

### generate_trend_comparison.py

**Purpose:** Standalone runner that calls `rta.trend_method_comparison.TrendMethodComparison` to produce a single consolidated Q1 comparison workbook.

**Category:** post-processing

**Status:** Active

**Usage:**
```
python generate_trend_comparison.py
```

**Inputs:**
- `results/final_N33/excel/*_Results.xlsx` (WB1; glob resolved; reads sheets S1, S2, S4, S7, S8)
- `data/reference/ebc6aee6-Rainfall_2Trend_Results.xlsx` (WB4; optional; adds Pettitt CP and significant-lag columns; path overridable via `WB4_PATH` env var)

**Outputs:**
- `results/final_N33_v5/Trend_Method_Comparison_Q1.xlsx` — single consolidated 4-method comparison workbook

**Upstream dependencies:** `rainfall_trend_analysis_v4.py`

**Downstream consumers:** None (standalone output; alternative to the full TCA suite)

**rta module:** `rta.trend_method_comparison.TrendMethodComparison`

---

### generate_all_vs_mk_workbook.py

**Purpose:** Reads the Master_DB sheet from the TCA Master workbook and builds a dedicated All-vs-MK comparison workbook with 9 styled sheets covering per-station comparisons, significance/direction change taxonomy, method ranking, and reviewer summaries.

**Category:** post-processing

**Status:** Active

**Usage:**
```
python generate_all_vs_mk_workbook.py
```

**Inputs:**
- `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/Trend_Method_Comparison_Master.xlsx` (sheet: `Master_DB`)

**Outputs:**
- `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/Trend_Method_Comparison_All_vs_MK.xlsx`
  - Sheet `MMK_vs_MK_Station` — 36 rows (12 stations × 3 scales)
  - Sheet `PW_vs_MK_Station` — 36 rows
  - Sheet `TFPW_vs_MK_Station` — 36 rows
  - Sheet `All_Scale_Summary` — 9 rows (3 methods × 3 scales)
  - Sheet `All_Manuscript_Table` — 12 rows wide format
  - Sheet `Significant_Changes` — variable (rows where significance changed)
  - Sheet `Direction_Changes` — variable (rows where direction changed)
  - Sheet `Method_Ranking` — 4 rows ranked by conservativeness
  - Sheet `Reviewer_Summary` — labelled multi-section summary

**Upstream dependencies:** `generate_trend_comparison_analysis.py` (must produce `Trend_Method_Comparison_Master.xlsx` first)

**Downstream consumers:** None (terminal analysis artifact)

---

### generate_tfpw_audit.py

**Purpose:** Reads Master_DB and builds a focused TFPW audit workbook comparing TFPW-MK results against MK, MMK, and PW-MK to isolate TFPW-specific behaviour.

**Category:** post-processing

**Status:** Active

**Usage:**
```
python generate_tfpw_audit.py
```

**Inputs:**
- `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/Trend_Method_Comparison_Master.xlsx` (sheet: `Master_DB`)

**Outputs:**
- `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/TFPW_Audit.xlsx`
  - Sheets: TFPW vs MK differences, TFPW vs MMK differences, TFPW vs PW differences, all-difference union, interpretation

**Upstream dependencies:** `generate_trend_comparison_analysis.py`

**Downstream consumers:** None

---

### generate_reviewer_summary.py

**Purpose:** Reads Master_DB and builds a structured 5-sheet Reviewer_Summary workbook covering method comparison metrics, conservativeness rankings, scientific interpretation, and use-case recommendations.

**Category:** post-processing

**Status:** Active

**Usage:**
```
python generate_reviewer_summary.py
```

**Inputs:**
- `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/Trend_Method_Comparison_Master.xlsx` (sheet: `Master_DB`)

**Outputs:**
- `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/Reviewer_Summary.xlsx`
  - Sheet `01_Method_Comparison` — side-by-side metrics for all 4 methods
  - Sheet `02_Conservativeness_Rank` — most to least conservative
  - Sheet `03_Agreement_Rank` — agreement with MK ranked
  - Sheet `04_Scientific_Interpretation` — structured interpretation table
  - Sheet `05_Recommendation` — use-case recommendations

**Upstream dependencies:** `generate_trend_comparison_analysis.py`

**Downstream consumers:** None

---

### generate_final_validation.py

**Purpose:** Reads Master_DB and produces three workbooks for final methodological validation: station-level disagreement analysis, Sen's slope cross-method comparison, and an executive methodological assessment.

**Category:** post-processing

**Status:** Active

**Usage:**
```
python generate_final_validation.py
```

**Inputs:**
- `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/Trend_Method_Comparison_Master.xlsx` (sheet: `Master_DB`)

**Outputs (all in `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/`):**
- `Disagreement_Stations.xlsx` — 4 sheets: all disagreements, significance transitions, direction transitions, reviewer notes
- `SenSlope_Comparison.xlsx` — 4 sheets: station slopes, slope difference summary, largest changes, scientific interpretation
- `Final_Methodological_Assessment.xlsx` — 3 sheets: executive summary, method ranking, reviewer defence

**Upstream dependencies:** `generate_trend_comparison_analysis.py`

**Downstream consumers:** None

---

### generate_q1_maps.py

**Purpose:** First-generation Q1 geographic spatial trend map generator; reads v4 Excel and the province shapefile to produce interpolated choropleth maps for all three temporal scales.

**Category:** post-processing

**Status:** Active (requires `rta.spatial_publication_q1` and `rta.spatial_interpolation` modules — these are in `rta/` but not listed in the package file inventory above; verify presence before running)

**Usage:**
```
python generate_q1_maps.py
```

**Inputs:**
- `results/final_N33/excel/*_Results.xlsx` (glob; reads sheet "S7 4-Method Comparison")
- `station_coordinates.csv` (WGS84 coordinates; columns: `Station`, `Lat`, `Lon`)
- `30_amarea_prachuap_khiri_khan.shp/.dbf/.shx/.prj` (province shapefile, repo root)

**Outputs (all under `results/final_N33/publication_maps/`):**
- `Fig_Q1_SpatialTrend.{png,tif,pdf,svg}` (Annual)
- `Fig_Q1_SpatialTrend_Wet.{png,tif,pdf,svg}` (Wet season)
- `Fig_Q1_SpatialTrend_Dry.{png,tif,pdf,svg}` (Dry season)
- `validation/Interpolation_Comparison.xlsx`
- `validation/LOOCV.xlsx`
- `Spatial_Methods_Q1.md`

**Upstream dependencies:** `rainfall_trend_analysis_v4.py`

**Downstream consumers:** None (superseded by `rainfall_trend_analysis_v5.py` for v5 outputs)

**rta modules:** `rta.spatial_publication_q1`, `rta.spatial_interpolation`

---

### calval_split.py

**Purpose:** Calibration/validation split analysis comparing 1981–2000 (CAL) vs 2001–2014 (VAL) periods for a climate model (ACCESS-ESM1-5 demonstrated).

**Category:** utility

**Status:** Out of scope — input files (model output CSVs) are absent from the repository. The script exits gracefully when `data/calval/` is empty or missing. Set `CALVAL_DATA_DIR` environment variable to provide an alternative path.

**Inputs:**
- Model output CSVs from `data/calval/` (or `CALVAL_DATA_DIR`; not present in repo)

**Outputs (to `results/calval/` or `CALVAL_OUT_DIR`):**
- `calval_metrics.xlsx`
- `Fig_CalVal_Overview.png/.pdf`
- `Fig_CalVal_Monthly.png/.pdf`
- `Fig_CalVal_Scatter.png/.pdf`

**Upstream dependencies:** None (independent utility)

**Downstream consumers:** None

---

### Comparative_4MMK.py

**Purpose:** Monte Carlo simulation study comparing Type-I error rates across prewhitening and Modified MK methods under synthetic AR(1) series; includes FDR analysis, variance distortion, and optional spatial outputs.

**Category:** utility

**Status:** Non-functional — imports `statsmodels` (`statsmodels.api`, `statsmodels.stats.stattools`, `statsmodels.tsa.stattools`, `statsmodels.stats.diagnostic`) which is not installed in the current Python environment. Also optionally imports `geopandas`, `shapely`, and `pymannkendall`, none of which are confirmed present. The script will raise `ModuleNotFoundError` on import.

**Inputs:** None (generates synthetic AR(1) data internally)

**Outputs (if it were runnable; path configurable):**
- Simulation result CSVs and publication figures

**Upstream dependencies:** None

**Downstream consumers:** None

---

## rta/ Package Modules

The `rta` package is the shared analysis library used by both `rainfall_trend_analysis_v3.py` (via graceful import fallback) and `rainfall_trend_analysis_v4.py` (hard import). All modules are pure Python except where noted.

### Core Modules

| Module | Purpose | Key Functions | Reads | Produces |
|--------|---------|---------------|-------|---------|
| `rta/config.py` | Shared constants, colour palette, Excel styling helpers, `savefig()` | `tb()`, `xfill()`, `xsc()`, `mxsc()`, `cw()`, `rh()`, `savefig()` | — | Constants: `VERSION`, `C`, `XC`, `DPI`, `SAVE_PDF`, `Z_005`, `Z_001`, `ALPHA_005`, `ALPHA_001`, `WET_THR`, `WET_MONTHS`, `DRY_MONTHS`, `MIN_N`, `MISS_FLAGS`, `SCALE_META`, `THIN`, `MED` |
| `rta/io.py` | Data loading, QC, checkpoint I/O, coordinate loading | `find_csv()`, `load_daily()`, `quality_control()`, `save_checkpoint()`, `load_checkpoint()`, `list_checkpoints()`, `load_coords()` | Daily CSV; `*coord*.csv` / `*station*.csv`; `ckpt_*.pkl` | Cleaned DataFrame + QC dict; `ckpt_*.pkl` files; coords dict |
| `rta/checkpoint.py` | Lightweight pickle resume system (standalone module; mirrors I/O functions from `rta/io.py` for v3 compatibility) | `save()`, `load()`, `list_steps()`, `prompt_resume()` | `checkpoints/ckpt_*.pkl` | `checkpoints/ckpt_*.pkl` |
| `rta/aggregation.py` | Temporal aggregation and descriptive statistics | `aggregate_all()`, `descriptive_stats()`, `validate_dry_season()` | Daily DataFrame (DatetimeIndex) | `dict` with keys `annual`, `wet`, `dry`, `monthly_all` → DataFrames; descriptive stats DataFrame; validation dict |
| `rta/autocorr.py` | Lag-k autocorrelation assessment | `lag_k_autocorr()`, `all_lag_autocorr()`, `is_sig_autocorr()` | NumPy array | Scalar `r_k`; ACF vector; boolean significance flag |
| `rta/trend_tests.py` | Four Mann-Kendall test implementations + Sen's slope | `mk_s_ties()`, `mk_variance_ties()`, `sens_slope()`, `standard_mk()`, `modified_mk()`, `pw_mk()`, `tfpw_mk()` | NumPy array | `dict` with keys: `Z`, `p_value`, `Trend`, `Slope_Q`, `Slope_lo`, `Slope_hi`, `sig_05`, `sig_01`, etc. |
| `rta/pw.py` | Prewhitening MK (Yue & Wang 2004) — thin wrapper | `pw_mk()` | NumPy array | Result dict (same schema as `trend_tests.pw_mk`) |
| `rta/tfpw.py` | Trend-Free Prewhitening MK (Yue et al. 2002) — thin wrapper | `tfpw_mk()` | NumPy array | Result dict (same schema as `trend_tests.tfpw_mk`) |
| `rta/batch.py` | Batch execution of all 4 methods × stations × scales | `run_all()`, `build_comparison()`, `build_4method_comparison()`, `METHOD_FN` | `scales` dict + station list | Tidy `trend_df` DataFrame; `comp_df`; `comp4_df` |
| `rta/field_sig.py` | Field significance testing (primary module used by v4) | `walker_test()`, `livezey_chen_mc()`, `field_sig_summary()` | `scales` dict + station list | `field_sig_df` DataFrame with Walker and LC-MC results per scale |
| `rta/field_significance.py` | Field significance testing (alternative module; used by v3 fallback import path) | `walker_test()`, `livezey_chen_mc()`, `field_sig_summary()` | Same as above | Same schema as `field_sig.py` |
| `rta/excel_output.py` | Write 6- or 9-sheet Excel workbook | `write_excel()` | `trend_df`, `comp_df`, `desc_df`, `qc_dict`, optional `comp4_df`, `field_sig_df`, `dry_validation` | `*_Results.xlsx` (up to 9 sheets) |
| `rta/markdown.py` | Write paper-ready Markdown research summary | `write_summary_md()` | `trend_df`, `comp_df`, `desc_df`, optional `scales`, `comp4_df`, `field_sig_df` | `*_Research_Summary.md` |
| `rta/spatial.py` | Coordinate loading and validation (standalone; mirrors `rta/io.py` coordinate functions) | `load_coords()`, `validate_coords()`, `coords_to_df()` | `*coord*.csv` / `*station*.csv` | `dict {station: (lat, lon)}`; validation report dict; coords DataFrame |
| `rta/spatial_maps.py` | Top-level re-export convenience module for spatial figures | Re-exports from `rta.figures.spatial` and `rta.figures.spatial_maps` | — | — |
| `rta/trend_comparison_analysis.py` | Full comparative analysis framework (used by `generate_trend_comparison_analysis.py`) | `TrendComparisonAnalysis` class with `run_all()` | WB1 (`*_Results.xlsx`) + optional WB4 | Multiple Excel workbooks + 10 publication figures + 9 Markdown templates (all under `Trend_Method_Comparison/`) |
| `rta/trend_method_comparison.py` | Single consolidated Q1 comparison workbook (used by `generate_trend_comparison.py`) | `TrendMethodComparison` class with `write_workbook()` | WB1 (`*_Results.xlsx`) + optional WB4 | `Trend_Method_Comparison_Q1.xlsx` |

### Figure Modules (`rta/figures/`)

| Module | Purpose | Key Functions | Inputs | Output Figures |
|--------|---------|---------------|--------|----------------|
| `rta/figures/helpers.py` | Shared figure helper utilities | `_sens_line()`, `_sig_label()`, `_col_trend()` | — | — (used internally) |
| `rta/figures/timeseries.py` | Time series figures | `fig1_annual_ts()`, `fig2_wetdry_ts()` | `scales`, `trend_df`, station info | Fig 1, Fig 2 |
| `rta/figures/bars.py` | Sen's slope bar chart | `fig3_sens_all()` | `trend_df`, station info | Fig 3 |
| `rta/figures/comparison.py` | MK vs MMK 4-panel comparison | `fig4_mk_vs_mmk()` | `comp_df`, station info | Fig 4 |
| `rta/figures/heatmaps.py` | Significance Z-statistic heatmap | `fig5_significance_heatmap()` | `trend_df`, station info | Fig 5 |
| `rta/figures/acf_plots.py` | Autocorrelation figures (v3 and v4 variants) | `fig6_autocorrelation()`, `fig12_acf_diagnostics()` | `scales`, station info | Fig 6, Fig 12 |
| `rta/figures/climatology.py` | Monthly climatology bar charts | `fig7_monthly_climatology()` | `scales`, station info | Fig 7 |
| `rta/figures/spatial.py` | Index-based (non-geographic) spatial summary | `fig8_spatial_summary()` | `trend_df`, `comp_df`, station info | Fig 8 |
| `rta/figures/taylor.py` | Taylor diagram for multi-station variability | `fig9_taylor_diagram()` | `scales`, station info | Fig 9 |
| `rta/figures/method_comparison.py` | 4-method Z matrix and scatter plots | `fig10_z_comparison_matrix()`, `fig11_method_comparison_scatter()` | `trend_df`, station info | Fig 10, Fig 11 |
| `rta/figures/field_sig_plot.py` | Field significance bar/summary figure | `fig13_field_significance()` | `field_sig_df`, period | Fig 13 |
| `rta/figures/spatial_maps.py` | Geographic spatial trend maps (true coordinates) | `fig14_spatial_maps()`, `fig_station_distribution()`, `fig_spatial_methods()`, `fig_spatial_field_sig()`, `fig_spatial_full()` | `trend_df`, `coords`, `field_sig_df`, station info | Fig 14, Fig_SpatialStation, Fig_SpatialMethods, Fig_SpatialFieldSig, Fig_SpatialFull |

#### Figure Output Naming Reference

| Figure | Prefix | Filename suffix |
|--------|--------|-----------------|
| Fig 1 | `Output_TrendV2_<base>` | `_Fig1_AnnualTimeSeries.png/.pdf` |
| Fig 2 | `Output_TrendV2_<base>` | `_Fig2_WetDryTimeSeries.png/.pdf` |
| Fig 3 | `Output_TrendV2_<base>` | `_Fig3_SenSlope_AllScales.png/.pdf` |
| Fig 4 | `Output_TrendV2_<base>` | `_Fig4_MK_vs_MMK_Comparison.png/.pdf` |
| Fig 5 | `Output_TrendV2_<base>` | `_Fig5_Significance_Heatmap.png/.pdf` |
| Fig 6 | `Output_TrendV2_<base>` | `_Fig6_Autocorrelation.png/.pdf` |
| Fig 7 | `Output_TrendV2_<base>` | `_Fig7_MonthlyClimatology.png/.pdf` |
| Fig 8 | `Output_TrendV2_<base>` | `_Fig8_SpatialTrend_Summary.png/.pdf` |
| Fig 9 | `Output_TrendV4_<base>` | `_Fig9_TaylorDiagram.png/.pdf` |
| Fig 10 | `Output_TrendV4_<base>` | `_Fig10_ZComparisonMatrix.png/.pdf` |
| Fig 11 | `Output_TrendV4_<base>` | `_Fig11_MethodComparison.png/.pdf` |
| Fig 12 | `Output_TrendV4_<base>` | `_Fig12_ACF_Diagnostics.png/.pdf` |
| Fig 13 | `Output_TrendV4_<base>` | `_Fig13_FieldSignificance.png/.pdf` |
| Fig 14 | `Output_TrendV4_<base>` | `_Fig14_SpatialMaps.png/.pdf` |
| Station map | `Output_TrendV4_<base>` | `_Fig_SpatialStation.png/.pdf` |
| All-methods map | `Output_TrendV4_<base>` | `_Fig_SpatialMethods.png/.pdf` |
| Field sig map | `Output_TrendV4_<base>` | `_Fig_SpatialFieldSig.png/.pdf` |
| Full overview | `Output_TrendV4_<base>` | `_Fig_SpatialFull.png/.pdf` |

Note: When `rainfall_trend_analysis_v3.py` invokes v4 figure modules (via `_RTA_AVAILABLE` path), those new figures also use the `Output_TrendV2_` prefix.

---

## rta_v5/ Package Modules

The `rta_v5` package is used exclusively by `rainfall_trend_analysis_v5.py`. It requires `geopandas`, `shapely`, and `scipy` (for interpolation/LOOCV).

| Module | Purpose | Key Functions | Reads | Produces |
|--------|---------|---------------|-------|---------|
| `rta_v5/spatial_publication_q1_v5.py` | Q1 figure rendering: 5-panel main maps, comparison panels, single-method panels, row layouts | `fig_q1_spatial_trend_v5()`, `fig_compare_v5()`, `fig_single_v5()`, `fig_4method_row_v5()`, `fig_senslope_row_v5()` | `comp4_df`, `coords_df`, boundary directory | Multi-format figure files (`.png`, `.tif`, `.pdf`, `.svg`) |
| `rta_v5/spatial_interpolation_v5.py` | Boundary loading, grid construction, IDW/RBF interpolation, LOOCV | `load_boundary()`, `build_grid()`, `idw_interpolate()`, `rbf_interpolate()`, `blend_interpolate()`, `loocv()`, `select_best()` | `boundaries/current_boundary/` shapefiles; station point data | Interpolated grids; LOOCV metrics |
| `rta_v5/spatial_validation_v5.py` | LOOCV across all scales, field significance loading | `run_loocv_all()`, `load_field_sig()`, `format_loocv_table()` | `comp4_df`, `coords_df`; `*_Results.xlsx` (for field sig) | LOOCV rows list; field_sig DataFrame |
| `rta_v5/spatial_export_v5.py` | Export utilities: multi-format save, metadata text, manuscript text, validation Excel | `save_formats()`, `write_fig_metadata()`, `write_boundary_config()`, `write_spatial_methods()`, `write_validation_excel()` | Figure objects; LOOCV rows; boundary config | `.txt` metadata; `manuscript/` Markdown files; LOOCV Excel |
| `rta_v5/spatial_layout_v5.py` | Figure layout, typography, map decorations | `apply_q1_typography()`, `build_axes()`, `build_axes_compare()`, `build_axes_single()`, `build_row_layout()`, `north_arrow()`, `scale_bar()`, `panel_letter()`, `format_map_axes()`, `apply_global_panel_style()` | — | Matplotlib axes objects |

---

## Data Files

| File | Format | Role | Discovered by |
|------|--------|------|---------------|
| `Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv` | CSV; columns YEAR, MONTH, DAY + station IDs | Primary daily rainfall input (12 stations, 1981–2014) | `rta.io.find_csv()` via glob; prefers "observed"/"rain" in name |
| `station_coordinates.csv` | CSV; columns Station, Lat, Lon, Altitude (128 stations) | Optional station coordinates for geographic figures | `rta.io.load_coords()` via `*coord*.csv` / `*station*.csv` glob |
| `30_amarea_prachuap_khiri_khan.shp/.dbf/.shx/.prj` | ESRI Shapefile | Province boundary for `generate_q1_maps.py` spatial interpolation | Hard-coded path in `generate_q1_maps.py` |
| `boundaries/current_boundary/boundary.shp/.dbf/.shx/.prj` | ESRI Shapefile | Province boundary for v5 pipeline | Hard-coded in `rainfall_trend_analysis_v5.py` |
| `data/stations.csv` | CSV; columns station_id, lat, lon, altitude | Station coordinates for v5 pipeline | Hard-coded in `rainfall_trend_analysis_v5.py` |
| `data/reference/ebc6aee6-Rainfall_2Trend_Results.xlsx` | Excel | Optional WB4 supplementary (Pettitt CP, significant lags, n_eff) | Hard-coded fallback; overridable via `WB4_PATH` env var |
| `results/final_N33/excel/*_Results.xlsx` | Excel (9 sheets) | Canonical v4 archive read by all post-processors | Glob in each post-processor script |
| `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/Trend_Method_Comparison_Master.xlsx` | Excel (sheet: Master_DB) | Intermediate database read by `generate_all_vs_mk_workbook.py`, `generate_tfpw_audit.py`, `generate_reviewer_summary.py`, `generate_final_validation.py` | Hard-coded paths in each script |

---

## Checkpoint Files

The v4 pipeline saves intermediate results as pickle files in `checkpoints/` (or the folder passed as the working directory). This allows the pipeline to resume from any completed step without recomputing upstream steps.

| File | Checkpoint name | Step | Data stored |
|------|----------------|------|-------------|
| `checkpoints/ckpt_01_qc.pkl` | `01_qc` | 1 | `df` (cleaned daily DataFrame), `qc_dict`, `stns_str`, `smap`, `period` |
| `checkpoints/ckpt_02_aggregation.pkl` | `02_aggregation` | 2 | `scales` dict (annual/wet/dry/monthly_all DataFrames), `desc_df`, `dry_validation` dict |
| `checkpoints/ckpt_03_acf.pkl` | `03_acf` | 3 | `any_sig_ac` (boolean) |
| `checkpoints/ckpt_04_trends.pkl` | `04_trends` | 4 | `trend_df` (all 4 methods × stations × scales, tidy DataFrame) |
| `checkpoints/ckpt_05_comparison.pkl` | `05_comparison` | 5 | `comp_df` (MK vs MMK), `comp4_df` (4-method comparison) |
| `checkpoints/ckpt_06_field_sig.pkl` | `06_field_sig` | 6 | `field_sig_df` (Walker + LC-MC results per scale) |

**Resume behaviour:** On startup, v4 scans for the latest completed checkpoint and prompts the user. Passing `--no-resume` skips this prompt and starts fresh. In non-interactive environments (no TTY), the resume prompt defaults to "no".

**Note:** `rta/checkpoint.py` and `rta/io.py` both implement the checkpoint API. `rta/io.py` is what v4 actually imports (`from rta.io import save_checkpoint, load_checkpoint, list_checkpoints`). `rta/checkpoint.py` is the standalone module that v3 imports via `from rta.checkpoint import save as _ckpt_save`.

---

## Execution Order

### Full Production Run (recommended sequence)

```
Step 1  [primary pipeline]
  python rainfall_trend_analysis_v4.py /path/to/data/folder
  → Writes Output_TrendV2_* (8 figs + 6-sheet Excel + MD)
  → Writes Output_TrendV4_* (14 figs + 9-sheet Excel + MD + DryValidation.txt)
  → Saves canonical Excel to results/final_N33/excel/  [manual copy step]

Step 2  [v5 spatial maps — requires geopandas]
  python rainfall_trend_analysis_v5.py
  → Requires: results/final_N33/excel/*_Results.xlsx
  → Writes:   results/final_N33_v5/publication_maps_v51/

Step 3  [trend comparison analysis — detailed method tables + figures]
  python generate_trend_comparison_analysis.py
  → Requires: results/final_N33/excel/*_Results.xlsx
  → Writes:   results/final_N33_v5/Trend_Method_Comparison/

Step 4  [Q1 single workbook — alternative compact output]
  python generate_trend_comparison.py
  → Requires: results/final_N33/excel/*_Results.xlsx
  → Writes:   results/final_N33_v5/Trend_Method_Comparison_Q1.xlsx

Step 5  [downstream of Step 3 — all require Master workbook]
  python generate_all_vs_mk_workbook.py   → Trend_Method_Comparison_All_vs_MK.xlsx
  python generate_tfpw_audit.py           → TFPW_Audit.xlsx
  python generate_reviewer_summary.py     → Reviewer_Summary.xlsx
  python generate_final_validation.py     → Disagreement_Stations.xlsx
                                            SenSlope_Comparison.xlsx
                                            Final_Methodological_Assessment.xlsx

Step 6  [Q1 maps with province shapefile — first-generation]
  python generate_q1_maps.py
  → Requires: results/final_N33/excel/*_Results.xlsx
              station_coordinates.csv
              30_amarea_prachuap_khiri_kan.shp (repo root)
  → Writes:   results/final_N33/publication_maps/
```

### Dependency Summary Table

| Script | Must run after |
|--------|---------------|
| `rainfall_trend_analysis_v4.py` | (none — entry point) |
| `rainfall_trend_analysis_v5.py` | `rainfall_trend_analysis_v4.py` |
| `generate_trend_comparison_analysis.py` | `rainfall_trend_analysis_v4.py` |
| `generate_trend_comparison.py` | `rainfall_trend_analysis_v4.py` |
| `generate_q1_maps.py` | `rainfall_trend_analysis_v4.py` |
| `generate_all_vs_mk_workbook.py` | `generate_trend_comparison_analysis.py` |
| `generate_tfpw_audit.py` | `generate_trend_comparison_analysis.py` |
| `generate_reviewer_summary.py` | `generate_trend_comparison_analysis.py` |
| `generate_final_validation.py` | `generate_trend_comparison_analysis.py` |
| `rainfall_trend_analysis_v3.py` | (none — standalone legacy) |
| `calval_split.py` | External model output (absent) |
| `Comparative_4MMK.py` | `statsmodels` install (absent) |

---

## Dependency Graph

```
Observed_Rain_daily_*.csv
station_coordinates.csv
        │
        ▼
rainfall_trend_analysis_v4.py  ──── rta/ package (all modules)
        │
        ├── Output_TrendV2_*_Fig1–8.png/.pdf
        ├── Output_TrendV2_*_Results.xlsx (6 sheets)
        ├── Output_TrendV2_*_Research_Summary.md
        ├── Output_TrendV4_*_Fig9–14 + Spatial*.png/.pdf
        ├── Output_TrendV4_*_Results.xlsx (9 sheets)  ◄── CANONICAL ARCHIVE
        ├── Output_TrendV4_*_Research_Summary.md
        ├── Output_TrendV4_*_DrySeasonValidation.txt
        └── checkpoints/ckpt_01–06_*.pkl
                              │
                              │  [copy to results/final_N33/excel/]
                              │
                 results/final_N33/excel/*_Results.xlsx
                              │
        ┌─────────────────────┼──────────────────────────┐
        │                     │                          │
        ▼                     ▼                          ▼
rainfall_trend_       generate_trend_            generate_q1_
analysis_v5.py        comparison_analysis.py     maps.py
        │                     │                          │
        │             Trend_Method_Comparison/           │
        │              ├── Master.xlsx  ◄──────────┐     │
        │              ├── Tables/                 │     │
        │              ├── Figures/                │     │
        │              └── Manuscript/             │     │
        │                     │                   │     │
publication_maps_v51/    ┌────┴──────┐            │  publication_maps/
  MK_vs_MMK/             │           │            │   Fig_Q1_SpatialTrend*
  PW_vs_TFPW/    generate_        generate_       │   validation/
  Individual_/   all_vs_mk.py     trend_          │
  comparison_row/      │          comparison.py   │
  senslope_row/        │                │         │
                 All_vs_MK.xlsx   Comparison_Q1.  │
                       │         xlsx             │
              ┌────────┤                          │
              │        │                          │
       generate_      generate_                   │
       tfpw_audit.py  reviewer_summary.py         │
              │        │                          │
       TFPW_Audit.xlsx Reviewer_Summary.xlsx      │
                                                  │
                   generate_final_validation.py   │
                              │                   │
                   Disagreement_Stations.xlsx      │
                   SenSlope_Comparison.xlsx        │
                   Final_Methodological_           │
                   Assessment.xlsx                 │
```

---

## Notes on Non-Standard Patterns

**Dual checkpoint implementations:** `rta/io.py` and `rta/checkpoint.py` both implement save/load/list functions with identical semantics. The v4 pipeline imports from `rta.io`; the v3 compatibility layer imports from `rta.checkpoint`. Both write to `ckpt_<name>.pkl` in the same directory, so they are interoperable.

**Dual field-significance modules:** `rta/field_sig.py` and `rta/field_significance.py` both implement `walker_test()`, `livezey_chen_mc()`, and `field_sig_summary()`. The v4 pipeline imports from `rta.field_sig`; the v3 compatibility fallback imports from `rta.field_significance`.

**Dual `pw_mk` / `tfpw_mk` implementations:** `rta/pw.py` and `rta/tfpw.py` are thin wrappers; the canonical implementations live in `rta/trend_tests.py`. Both sets produce identical result dicts. `rta/batch.py` uses the `rta.trend_tests` versions directly via `METHOD_FN`.

**Coordinate loading duplication:** `rta/io.py:load_coords()` and `rta/spatial.py:load_coords()` are near-identical implementations. v4 imports from `rta.io`; v3 imports from `rta.spatial` (via the graceful import block).

**Output prefix mismatch:** The v3-format outputs generated by v4 use the prefix `Output_TrendV2_` even though they are produced by the v4 pipeline. The v4-new outputs use `Output_TrendV4_`. This is intentional backward compatibility.

**WB4 optional dependency:** Several post-processors (`generate_trend_comparison_analysis.py`, `generate_trend_comparison.py`) accept an optional WB4 supplementary workbook (`data/reference/ebc6aee6-Rainfall_2Trend_Results.xlsx`). When absent, the scripts continue with NaN values for Pettitt change-point and significant-lag columns. Set the `WB4_PATH` environment variable to override the default path.
