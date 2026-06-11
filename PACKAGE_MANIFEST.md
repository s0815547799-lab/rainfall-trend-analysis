# Package Manifest

**Project:** Rainfall Trend Analysis — Phetchaburi–Prachuap Khiri Khan River Basin  
**Version:** v4.1  
**Date:** 2026-06-11

---

## Entry Points

| Script | Purpose |
|--------|---------|
| `rainfall_trend_analysis_v3.py` | Legacy single-file pipeline (Standard MK + MMK + 8 figures) |
| `rainfall_trend_analysis_v4.py` | Modular pipeline (4 methods + field significance + 28 figures + checkpoint) |
| `CMIP6_MME_v2/main.py` | CMIP6 multi-model ensemble projection pipeline (primary) |
| `CMIP6_package/main.py` | CMIP6 MME pipeline v1 (superseded by v2; retained for reference) |

---

## `rta/` — Rainfall Trend Analysis Package

### Core modules

| Module | Public API | Purpose |
|--------|-----------|---------|
| `rta/config.py` | `MIN_N`, `ALPHA_005`, `Z_005`, `C`, `DPI`, `savefig` | Shared constants and colour palette |
| `rta/io.py` | `find_csv`, `load_daily`, `quality_control`, `load_coords`, `save_checkpoint`, `load_checkpoint` | CSV discovery, QC, coordinate loading, checkpoint I/O |
| `rta/aggregation.py` | `aggregate_all`, `descriptive_stats`, `validate_dry_season` | Annual/wet/dry/monthly aggregation with 80% completeness gate |
| `rta/autocorr.py` | `lag_k_autocorr`, `all_lag_autocorr`, `is_sig_autocorr` | Lag-k ACF, Bartlett significance test |
| `rta/trend_tests.py` | `standard_mk`, `modified_mk`, `pw_mk`, `tfpw_mk`, `sens_slope` | All four MK variants and Sen's slope estimator |
| `rta/pw.py` | `pw_mk` | Prewhitening MK — v3 fallback path (duplicate of `trend_tests.pw_mk`) |
| `rta/tfpw.py` | `tfpw_mk` | TFPW-MK — v3 fallback path (duplicate of `trend_tests.tfpw_mk`) |
| `rta/batch.py` | `run_all`, `build_comparison`, `build_4method_comparison` | Station × scale batch execution; 4-method comparison table |
| `rta/field_sig.py` | `walker_test`, `livezey_chen_mc`, `field_sig_summary` | Field significance — v4 path (Walker + LC for MK and MMK) |
| `rta/field_significance.py` | `walker_test`, `livezey_chen_mc`, `field_sig_summary` | Field significance — v3 fallback path (duplicate of `field_sig.py`) |
| `rta/spatial.py` | `load_coords`, `validate_coords`, `coords_to_df` | WGS84 coordinate loading; station coverage validation |
| `rta/spatial_maps.py` | re-exports all `figures/spatial_maps.py` functions | Top-level re-export for v4 pipeline |
| `rta/checkpoint.py` | `save`, `load`, `list_steps`, `prompt_resume` | 6-step pickle checkpoint — v3 fallback (duplicate of `io.py` checkpoints) |
| `rta/excel_output.py` | `write_excel` | 9-sheet Excel workbook with full cell styling |
| `rta/markdown.py` | `write_summary_md` | Paper-ready Markdown research summary |

### Figure modules (`rta/figures/`)

| Module | Figures produced |
|--------|-----------------|
| `timeseries.py` | Fig 1 (annual time series), Fig 2 (wet/dry time series) |
| `bars.py` | Fig 3 (Sen's slope bar chart, all scales) |
| `comparison.py` | Fig 4 (MK vs MMK 4-panel comparison) |
| `heatmaps.py` | Fig 5 (significance heatmap) |
| `acf_plots.py` | Fig 6 (autocorrelation), Fig 12 (ACF diagnostics) |
| `climatology.py` | Fig 7 (monthly climatology) |
| `spatial.py` | Fig 8 (index-based spatial summary — legacy) |
| `taylor.py` | Fig 9 (Taylor diagram) |
| `method_comparison.py` | Fig 10, Fig 11 (4-method slope / Z comparison) |
| `field_sig_plot.py` | Fig 13 (field significance panel) |
| `spatial_maps.py` | Fig 14, SpatialStation, SpatialMethods, SpatialFieldSig, SpatialFull (WGS84 geographic maps) |
| `helpers.py` | Shared rendering helpers (axis styling, label placement) |

---

## `CMIP6_MME_v2/` — CMIP6 Multi-Model Ensemble Pipeline (primary)

| Module | Public API | Purpose |
|--------|-----------|---------|
| `src/utils/io.py` | `discover_csv`, `load_metadata`, `load_cmip6_csvs` | CSV discovery (regex), metadata loading (.xlsx/.csv), CMIP6 ingestion |
| `src/rainfall/seasonal.py` | `observed_yearly`, `model_yearly` | Annual/wet/dry aggregation with 80% gate; leap-day stripping |
| `src/ensemble/mme.py` | `build_mme` | MME statistics (mean, median, P25, P75, n_models) — NaN-safe |
| `src/validation/metrics.py` | `kge`, `nse`, `pbias`, `validation_metrics` | KGE/NSE/PBIAS per station, Raw vs BC on common-year sample |
| `src/gis/interp.py` | `idw_interp`, `kriging_interp`, `load_boundary` | IDW/kriging interpolation; shapefile boundary loader |
| `src/tables/results.py` | `build_results_table`, `write_excel` | 3-level publication table; Excel output |
| `src/figures/base.py` | `save_dual`, `panel_tag`, `auto_color_range` | Shared figure helpers (dual-column save, panel labels) |
| `src/figures/make.py` | `fig1_taylor` … `fig7_change`, `generate_all` | Figures 1–7 (Taylor, validation, anomaly time series, spatial maps, change maps) |
| `config/config.yaml` | — | Study area, paths, periods, seasons, scenarios, GIS, figure settings |
| `main.py` | — | Pipeline entry point; orchestrates all steps |

---

## `CMIP6_package/` — CMIP6 MME Pipeline v1 (superseded)

Structurally identical to `CMIP6_MME_v2/` with the following differences:

| Item | v1 (`CMIP6_package`) | v2 (`CMIP6_MME_v2`) |
|------|----------------------|----------------------|
| Scenario support | Hardcoded `["ssp245","ssp585"]` | Dynamic from `cfg["scenarios"]` |
| Percentile NaN guard | Absent — **bug (CC-03)** | Present — NaN-safe |
| Metadata loading | `.xlsx` only | `.xlsx` and `.csv` |
| Publication table format | Flat | 3-level column headers |
| Anomaly baseline | Fixed (CM-05 patched) | Fixed (CM-05 patched) |

---

## Configuration Files

| File | Used by | Key settings |
|------|---------|-------------|
| `CMIP6_MME_v2/config/config.yaml` | CMIP6 v2 pipeline | Study area, paths, periods [1981–2014, 2021–2050], seasons, scenarios, GIS, figures |
| `CMIP6_package/config/config.yaml` | CMIP6 v1 pipeline | Same structure |

---

## Data Files

| File | Description |
|------|-------------|
| `station_coordinates.csv` | WGS84 coordinates for 128 stations (Lat, Lon, Altitude); all 12 rainfall stations present |
| `30_amarea_prachuap_khiri_khan.*` | Basin boundary shapefiles (.shp/.dbf/.shx/.prj) |

---

## Documentation

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project instructions, statistical workflow, mandatory scientific standards (§12) |
| `CHANGELOG.md` | Version history and per-fix change log |
| `README.md` | Title, version, installation note |
| `AUDIT_REPORT.md` | Full codebase audit — methods, architecture, Q1 readiness |
| `DEFECT_LOG.md` | Structured defect log — all findings with IDs, severity, evidence |
| `PRIORITY_FIX_LIST.md` | Ordered fix list with code-level guidance |
| `CMIP6_REVIEW_REPORT.md` | Dedicated CMIP6 scientific review |
| `CRITICAL_VALIDATION_REPORT.md` | Scientific validity assessment for all 8 critical defects |
| `EXECUTIVE_SUMMARY.md` | 2-page synthesis — top 5 issues, fix order, publication risk |
| `FINAL_RELEASE_REPORT.md` | Completed fixes and remaining known issues |
| `VALIDATION_REPORT.md` | Before/after quantification for C-01, C-03, CM-05 |
| `PACKAGE_MANIFEST.md` | This file |

---

## Dependencies

### Rainfall Pipeline (`rta/`)

| Package | Version (README) | Purpose |
|---------|-----------------|---------|
| Python | 3.11.15 | Runtime |
| numpy | pinned in README | Array operations, statistics |
| pandas | pinned in README | DataFrames, time series |
| scipy | pinned in README | `stats.norm`, `stats.binom`, `stats.rankdata` |
| matplotlib | pinned in README | All figures (backend: Agg) |
| openpyxl | pinned in README | Excel output with cell styling |

`requirements.txt` absent — must be created before Q1 submission.

### CMIP6 Pipelines

| Package | Purpose |
|---------|---------|
| All above | Same |
| `geopandas` / `shapely` | Boundary shapefile loading and polygon rendering |
| `pyyaml` | `config.yaml` parsing |

`Comparative_4MMK.py` additionally imports `statsmodels`, `seaborn`, `geopandas`, `pymannkendall` — none listed in any requirements file.

---

## Known Duplicate Modules (C-02)

The following pairs implement the same functionality. The v4 pipeline uses the left column; the v3 fallback uses the right. Bugs fixed in one copy do not propagate to the other.

| v4 path (active) | v3 fallback | Material difference |
|-----------------|-------------|---------------------|
| `rta/trend_tests.py::pw_mk` | `rta/pw.py::pw_mk` | `pw.py` checks MIN_N after prewhitening; `trend_tests.py` does not |
| `rta/trend_tests.py::tfpw_mk` | `rta/tfpw.py::tfpw_mk` | Essentially identical |
| `rta/field_sig.py` | `rta/field_significance.py` | `field_sig.py` has MMK Walker/LC (fixed); `field_significance.py` always had it |
| `rta/io.py` (checkpoints) | `rta/checkpoint.py` | Different function names; same pickle format |
