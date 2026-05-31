# PACKAGE MANIFEST — CMIP6 MME Rainfall Projection Framework v2.0
**FINAL RELEASE**

| Item | Value |
|------|-------|
| Package | `CMIP6_MME_v2` |
| Version | 2.0.0 |
| Release date | 2026-05-31 |
| Python | ≥ 3.10 |
| Test status | **30 / 30 PASS** |
| End-to-end status | **PASS** |
| Journal target | Q1 hydrology (J. Hydrol., WRR, HESS) |

---

## Bug Fixes vs Original Submission

| # | Module | Issue | Fix |
|---|--------|-------|-----|
| 1 | `seasonal.py` | Dry-season hydrological year wrong (Nov–Apr same calendar year) | Two-mask concatenation: `yr==y` Nov/Dec + `yr==(y+1)` Jan–Apr → labelled `y+1` |
| 2 | `seasonal.py` | All-NaN years returned `0.0` (nansum of empty = 0) | `_safe_sum()`: returns NaN if `n_valid == 0` |
| 3 | `metrics.py` | KGE_Raw and KGE_BC computed on different year sets | Three-way intersection `obs ∩ raw ∩ bc` before all metric calculations |
| 4 | `metrics.py` | `KGE_Improvement_%` divides by `|KGE_Raw|` — undefined when Raw < 0 | Replaced with `ΔKGE = KGE_BC − KGE_Raw` (absolute, bounded) |
| 5 | `io.py` | Regex rejected uppercase scenario codes (`SSP245`, `SSP5-8.5`) | `re.IGNORECASE` flag + `.lower()` normalisation on match |
| 6 | `io.py` | Column names case-sensitive (`Station` vs `station` crash) | `str.lower()` on all columns before rename; explicit `KeyError` for missing |
| 7 | `make.py` | `np.concatenate([])` crash when no stations match; double computation | `_collect_panel_data()` computes each panel exactly once; empty-list guard |
| 8 | `final_run.py` | QC gate only checked `.png`; `.tiff` figures silently ignored | Loop over `("*.png", "*.tiff", "*.tif")` + separate PDF count |
| 9 | `seasonal.py` | No completeness gate — partial years (1 rainy day) counted as valid | `_safe_sum()` returns NaN if `n_valid / expected < min_completeness` (default 0.80) |
| 10 | `make.py` | Taylor diagram: dead `if False` branch; hardcoded `set_rmax(2.0)` | Removed dead branch; `rmax = max(max(all_r) × 1.10, 1.6)` from data |

---

## File Inventory

### Entry Points

| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | 219 | Computation pipeline only (no figures) — fast iteration |
| `final_run.py` | 205 | Full pipeline + figures + QC gate + versioned RELEASE directory |

### Source Modules (`src/`)

| File | Lines | Exports | Description |
|------|-------|---------|-------------|
| `src/utils/io.py` | 145 | `load_config`, `discover_csv`, `parse_csv`, `load_metadata` | Config YAML, CSV discovery (Raw/BC), metadata loader (case-insensitive) |
| `src/rainfall/seasonal.py` | 160 | `observed_yearly`, `cmip6_yearly`, `_wide_to_yearly` | Daily → yearly seasonal totals; dry-season hydrological year; completeness gate |
| `src/ensemble/mme.py` | 46 | `build_mme` | Per-model data → MME (mean/median/P25/P75) per station×year×season×scenario |
| `src/validation/metrics.py` | 143 | `kge`, `nse`, `pbias`, `validation_metrics` | KGE/NSE/PBIAS on three-way common year index; ΔKGE column |
| `src/gis/interp.py` | 130 | `load_boundary`, `idw`, `ordinary_kriging`, `surface` | Boundary loading; IDW and batch LU-factorised ordinary kriging |
| `src/figures/base.py` | 186 | `save_dual`, `auto_color_range`, `free_corner`, `panel_tag`, `add_panel_label` | Q1 typography; dual-column save; robust colour range; geographic corner detection |
| `src/figures/make.py` | 516 | `generate_all`, `fig1_taylor`…`fig7_change`, `_collect_panel_data` | 7 publication figures × single/double × 3 formats |
| `src/tables/results.py` | 175 | `level1_station_model`, `level2_station_mme`, `level3_area_summary`, `publication_tables` | 3-level results architecture; 7 publication Excel tables |

### Configuration

| File | Lines | Purpose |
|------|-------|---------|
| `config/config.yaml` | 69 | Province-agnostic config — change 10 fields to run a new study area |
| `requirements.txt` | 35 | Pinned runtime dependencies |

### Tests (`tests/`)

| File | Lines | Tests | Coverage |
|------|-------|-------|---------|
| `tests/test_all_fixes.py` | 426 | 26 | All 10 bug fixes; `free_corner` geographic convention; import chain |
| `tests/test_pipeline_smoke.py` | 235 | 4 | `generate_all` end-to-end; figure count; 600 DPI PNG; QC gate |

**Total: 30 tests — 30 PASS / 0 FAIL / 0 SKIP**

### Package Initialisation

| File | Purpose |
|------|---------|
| `src/__init__.py` | Package root marker |
| `src/{ensemble,figures,gis,rainfall,tables,utils,validation}/__init__.py` | Sub-package markers |
| `tests/__init__.py` | Test package marker |

---

## Figure Inventory (generate_all output)

| Figure | ID | Content | Panels |
|--------|----|---------|--------|
| Taylor diagram | `Figure1_Taylor` | σ_ratio vs correlation, Raw MME & BC-MME vs Observed | 1 |
| Validation | `Figure2_Validation` | KGE / NSE / PBIAS Cleveland dot plot, Raw vs BC | 3 (a–c) |
| Time series | `Figure3_TimeSeries` | Anomaly 1981–2050; Observed + BC-historical + SSP scenarios; P25–P75 shaded | 3 (a–c) |
| Annual spatial | `Figure4_Annual_Spatial` | Station-value maps: Observed / Hist-BC / SSP245 / SSP585 | 4 (a–d) |
| Wet spatial | `Figure5_Wet_Spatial` | Wet-season station maps | 4 (a–d) |
| Dry spatial | `Figure6_Dry_Spatial` | Dry-season station maps | 4 (a–d) |
| Change maps | `Figure7_Change` | Proportional-symbol ΔP% maps; size ∝ \|ΔP%\|; RdBu diverging | 6 (a–f) |

Each figure saved as: `{fid}_single.{ext}` + `{fid}_double.{ext}` × `{png, tiff, pdf}` = **6 files per figure = 42 total**

---

## Publication Table Inventory

| Table | Filename | Sheet(s) | Content |
|-------|----------|----------|---------|
| 01 | `Table_01_Station_Metadata.xlsx` | 1 | Station ID, lat, lon, elevation |
| 02 | `Table_02_Validation_Metrics.xlsx` | 1 | KGE/NSE/PBIAS Raw & BC; ΔKGE; n_years |
| 03 | `Table_03_Annual_Change.xlsx` | per_station + summary | ΔP% annual per station; scenario statistics |
| 04 | `Table_04_Wet_Change.xlsx` | per_station + summary | ΔP% wet season |
| 05 | `Table_05_Dry_Change.xlsx` | per_station + summary | ΔP% dry season |
| S1 | `Table_S1_Model_Performance.xlsx` | 1 | Per-model historical statistics (Supplementary) |
| S2 | `Table_S2_Station_Model_Results.xlsx` | 1 | Full MME results all stations (Supplementary) |

---

## Q1 Publication Standards Implemented

| Standard | Implementation |
|----------|---------------|
| Font | Times New Roman → Liberation Serif → DejaVu Serif (fallback chain) |
| Font embedding | `pdf.fonttype = 42`, `ps.fonttype = 42` (Type 1 → TrueType; journal requirement) |
| Resolution | 600 DPI (PNG + TIFF + PDF) |
| Column widths | Single: 3.5 in, Double: 7.2 in (standard journal grid) |
| Colour palette | Wong (2011) colorblind-safe; RdBu diverging for change; YlGnBu sequential for absolute |
| Axes | No top/right spines; dashed grid α = 0.45 |
| Panel labels | `(a)(b)(c)` — consistent position and size across all figures |
| No title/footnote | Figures self-contained per journal submission guidelines |
| QC gate | Automated DPI + minimum width check on all PNG/TIFF; PDF presence check |

---

## Province Adaptation Checklist

To run on a **new study area**, edit only `config/config.yaml`:

```
☐  study_area.name          ← province / basin name (used in logs and output filenames)
☐  study_area.province_code ← short ASCII slug (e.g., "chiang_mai")
☐  paths.observed           ← path to observed daily rainfall Excel
☐  paths.cmip6_csv          ← folder containing Raw and BC model CSV files
☐  paths.station_metadata   ← path to station metadata Excel/CSV
☐  paths.boundary           ← path to study-area boundary .shp
☐  paths.outputs            ← output root folder
☐  periods.baseline         ← [start_year, end_year] of observed record
☐  periods.near_future      ← [start_year, end_year] of future projection window
☐  scenarios                ← list of SSP codes present in your CMIP6 data
```

Optional (only if seasons differ from Thai monsoon default):
```
☐  seasons.wet_months       ← list of wet-season month numbers
☐  seasons.dry_months       ← list of dry-season month numbers
```

**No source code changes required.**

---

## Runtime Output Structure

```
outputs/
├── CURRENT_RELEASE → RELEASE_<code>_<YYYYMMDD_HHMMSS>/   ← updated only on QC PASS
└── RELEASE_<code>_<YYYYMMDD_HHMMSS>/
    ├── station_model/              Level 1: one Excel per station × model × scenario × season
    ├── station_mme/                Level 2: MME statistics + ΔKGE + validation per station
    ├── area_summary/               Level 3: spatial mean obs / BC-historical / SSP× per season
    ├── publication_tables/         Tables 01–05 + S1, S2 (ready to submit)
    ├── publication_figures/        42 figure files (ready to submit)
    ├── release/
    │   ├── FIGURE_QC.xlsx          Per-file DPI / width / format check
    │   └── RUNTIME_SUMMARY.xlsx    Timing, counts, QC pass/fail
    └── FIGURE_QC_REPORT.md         Human-readable QC report
```

---

## Test Certificate

```
Platform : Linux / Python 3.11.15
pytest   : 9.0.3
Date     : 2026-05-31

tests/test_all_fixes.py       26 passed
tests/test_pipeline_smoke.py   4 passed
─────────────────────────────────────────
TOTAL                         30 passed   0 failed   0 skipped
```
