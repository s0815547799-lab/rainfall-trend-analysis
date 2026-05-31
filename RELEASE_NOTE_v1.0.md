# Release Notes — CMIP6 MME Rainfall Projection Framework v1.0

## Release Metadata

| Item | Value |
|------|-------|
| Version | **v1.0** |
| Release date | **2026-05-31** |
| Branch | `claude/code-review-q1-publication-5rdcE` |
| Commit | `09f73711367013a3e2e8208ae6512c3d73cd4ed7` |
| Package | `CMIP6_MME_v2_FINAL_RELEASE.zip` |
| Python | 3.11.15 |
| Platform | Linux x86-64 |

---

## Test Results

```
Platform : Linux / Python 3.11.15
pytest   : 9.0.3
Date     : 2026-05-31

tests/test_all_fixes.py        26 passed   0 failed   0 skipped
tests/test_pipeline_smoke.py    4 passed   0 failed   0 skipped
──────────────────────────────────────────────────────────────
TOTAL                          30 passed   0 failed   0 skipped
```

### Test Coverage by Fix

| Test class | Tests | Covers |
|------------|-------|--------|
| `TestSeasonal` | 5 | Bugs #1 (dry-season hydro-year), #2 (all-NaN → NaN), #9 (completeness gate) |
| `TestMetrics` | 5 | Bugs #3 (three-way year intersection), #4 (ΔKGE absolute) |
| `TestIO` | 6 | Bugs #5 (uppercase SSP codes), #6 (case-insensitive columns) |
| `TestFigureHelpers` | 2 | Bug #7 (empty concatenate guard; single computation) |
| `TestFigureQC` | 2 | Bug #8 (QC covers PNG + TIFF) |
| `TestTaylorDiagram` | 2 | Bug #10 (no `if False`; dynamic `rmax`) |
| `TestFreeCorner` | 1 | Geographic North = image row 0 convention |
| `TestImports` | 2 | Full import chain; no `_map_panel` dead stub |
| `TestPipelineSmoke` | 4 | End-to-end `generate_all`; 600 DPI PNG; QC gate |

---

## Package Contents

```
CMIP6_MME_v2/                       124,143 bytes uncompressed (49 KB zipped)
│
├── main.py                          Computation pipeline (no figures)
├── final_run.py                     Full pipeline + QC gate + versioned RELEASE dir
├── requirements.txt                 12 runtime dependencies
├── PACKAGE_MANIFEST.md              Detailed file inventory and release documentation
│
├── config/
│   └── config.yaml                  Province-agnostic configuration (10 fields to change)
│
├── src/
│   ├── utils/io.py                  Config, CSV discovery, metadata loading
│   ├── rainfall/seasonal.py         Daily → seasonal totals; hydrological-year dry season
│   ├── ensemble/mme.py              Multi-model ensemble (mean/median/P25/P75)
│   ├── validation/metrics.py        KGE, NSE, PBIAS; three-way year intersection; ΔKGE
│   ├── gis/interp.py                IDW + batch LU-factorised ordinary kriging; boundary
│   ├── figures/base.py              Q1 typography; save_dual; auto_color_range; free_corner
│   ├── figures/make.py              7 publication figures × single/double × 3 formats
│   └── tables/results.py            3-level results architecture; 7 publication tables
│
├── tests/
│   ├── test_all_fixes.py            26 unit tests (all 10 bugs)
│   └── test_pipeline_smoke.py       4 smoke tests (end-to-end pipeline)
│
├── data/                            Placeholder — user places input files here
│   ├── observed/
│   ├── cmip6_raw/
│   ├── station_metadata/
│   └── boundary/
│
└── outputs/                         Placeholder — pipeline writes results here
```

**41 entries total. Zero `__pycache__`, `.pyc`, or temporary files.**

---

## Required Input Datasets

Four input files must be placed in the `data/` subdirectories before running.

### 1. Observed daily rainfall — `data/observed/observed_daily.xlsx`

| Column | Type | Description |
|--------|------|-------------|
| `YEAR` | int | Calendar year |
| `MONTH` | int | Month (1–12) |
| `DAY` | int | Day (1–31) |
| `<station_id>` | float | Daily rainfall (mm); one column per station |

- Missing values: `NaN`, `-99`, `-999`, `-9999` (all accepted)
- Coverage: must span the `baseline` period defined in `config.yaml` (default 1981–2014)
- Formats accepted: `.xlsx`, `.xls`, `.csv`

### 2. CMIP6 model CSV files — `data/cmip6_raw/`

One CSV per model × scenario combination. Filename convention:

```
Raw:  pr_day_<MODEL>_<scenario>_<realization>[_<years>].csv
BC:   bc_pr_day_<MODEL>_<scenario>_<realization>[_<years>].csv
```

- Scenario codes: case-insensitive (`ssp245`, `SSP245`, `SSP5-8.5` all accepted)
- Column layout: same as observed daily (YEAR / MONTH / DAY / station columns)
- Historical files must cover the baseline period; SSP files must cover the near-future period

### 3. Station metadata — `data/station_metadata/station_metadata.xlsx`

| Column | Accepted names | Type |
|--------|---------------|------|
| Station ID | `station`, `Station`, `id`, `station_id` | str |
| Latitude | `latitude`, `Latitude`, `lat`, `Lat` | float |
| Longitude | `longitude`, `Longitude`, `lon`, `Lon`, `long` | float |
| Elevation | `altitude`, `Altitude`, `elevation`, `elev`, `dem`, `height` | float |

- Formats accepted: `.xlsx`, `.xls`, `.csv`
- Column names are normalised automatically (case-insensitive, whitespace-stripped)

### 4. Study-area boundary — `data/boundary/boundary.shp`

- ESRI Shapefile (`.shp` + `.dbf` + `.shx` + `.prj` required)
- Any coordinate reference system accepted (auto-reprojected to EPSG:4326)
- Defines the domain for spatial maps (Figures 4–7)

---

## Known Limitations

### Statistical / Scientific

1. **Spatial interpolation uses station values directly.** Figures 4–7 use station-point symbols rather than gridded interpolation. For networks with N < ~20 stations, kriging or IDW surfaces can be misleading; station-symbol maps are the statistically honest choice. Grid-based surfaces (`idw()` / `ordinary_kriging()` in `src/gis/interp.py`) are available but not called by default figures.

2. **Validation covers historical period only.** KGE / NSE / PBIAS are computed on the observed baseline (1981–2014). Future-period skill cannot be assessed without independent verification data.

3. **BC quality not assessed.** The framework treats bias-corrected (BC) files as provided. It does not perform or validate the bias correction method itself — that is assumed to have been done upstream.

4. **Dry-season completeness depends on both years.** The Nov(Y)–Apr(Y+1) hydrological dry season requires valid data from two calendar years. If either year is outside the loaded date range the block is silently dropped (not a bug — this is the correct boundary behaviour).

5. **Leap days stripped.** February 29 is removed before computing expected-day counts to ensure stable completeness denominators across all years. This reduces expected annual days by 1 in 75% of years but is consistent and reproducible.

### Software / Engineering

6. **geopandas ≥ 1.0 required (pyogrio backend).** This release uses `pyogrio` as the geopandas I/O backend. The older `fiona` backend is **not** required and should not be installed alongside; version conflicts can cause silent read errors.

7. **No parallel / distributed execution.** The pipeline is single-threaded. For large multi-model ensembles (> 20 models, > 50 stations) the validation and figure generation steps can take 10–30 minutes on a standard laptop.

8. **Parquet intermediate files require pyarrow.** If `pyarrow` is not installed, `main.py` will fail at the `.to_parquet()` / `.read_parquet()` steps. Install with `pip install pyarrow`.

9. **PDF font embedding requires matplotlib ≥ 3.7.** Earlier versions do not reliably set `pdf.fonttype = 42`; submitted PDFs may fail journal font checks.

10. **No checkpoint / resume for partial runs.** If `final_run.py` is interrupted mid-execution, the incomplete RELEASE directory must be deleted manually before re-running. There is no incremental resume mechanism.

---

## Reproduction Instructions

### Prerequisites

```bash
# Python 3.10 or later required
python --version

# Install all dependencies
pip install -r requirements.txt
```

### Verify tests pass

```bash
cd CMIP6_MME_v2
python -m pytest tests/ -v
# Expected: 30 passed, 0 failed, 0 skipped
```

### Configure for your study area

Edit `config/config.yaml` — change the 10 fields marked below:

```yaml
study_area:
  name: "Your Province Name"        # ← change
  province_code: "your_province"    # ← change (ASCII slug, no spaces)

paths:
  observed:         "data/observed/observed_daily.xlsx"         # ← change path
  cmip6_csv:        "data/cmip6_raw"                            # ← change path
  station_metadata: "data/station_metadata/station_metadata.xlsx" # ← change path
  boundary:         "data/boundary/boundary.shp"                # ← change path
  outputs:          "outputs"                                   # ← change if needed

periods:
  baseline:     [1981, 2014]   # ← change to your observed record period
  near_future:  [2021, 2050]   # ← change to your projection window

scenarios: ["ssp245", "ssp585"]  # ← change to match your CMIP6 files
```

### Run the full pipeline

```bash
# Option A — full publication pipeline (recommended)
python final_run.py

# Option B — computation only, no figures
python main.py

# Option C — custom config path
python final_run.py --cfg config/config_chiang_mai.yaml
```

### Outputs

On success, `final_run.py` creates:

```
outputs/
├── CURRENT_RELEASE → RELEASE_<province>_<YYYYMMDD_HHMMSS>/
└── RELEASE_<province>_<YYYYMMDD_HHMMSS>/
    ├── publication_figures/   42 files (7 figs × single/double × PNG+TIFF+PDF)
    ├── publication_tables/    7 Excel tables (Tables 01–05, S1, S2)
    ├── station_model/         Per-station × per-model Excel files
    ├── station_mme/           Station_MME_Results.xlsx
    ├── area_summary/          Area_Summary.xlsx
    ├── release/               FIGURE_QC.xlsx + RUNTIME_SUMMARY.xlsx
    └── FIGURE_QC_REPORT.md    QC pass/fail report (journal readiness check)
```

`CURRENT_RELEASE` symlink is updated **only if the QC gate passes** (all PNG/TIFF at 600 DPI, at least one PDF present). A failed run leaves a dated directory for inspection but does not overwrite the last known-good release.

### Expected runtime

| Stage | Approximate time |
|-------|-----------------|
| Data loading + validation | 10–60 s (depends on CSV count) |
| MME build + metrics | 5–30 s |
| Figure generation (7 figures × 2 widths × 3 formats) | 3–15 min |
| Table generation | < 5 s |
| **Total** | **5–20 min** |

---

*Generated by Claude Code — session `01PEkygBt6Zo117L6qMmxmyJ`*
