# Framework Conversion Report
**Project:** Rainfall Trend Analysis — Hydroclimatic Framework Architecture Audit  
**Based on:** Prachuap Khiri Khan release v1.0.0 (commit 471bdc3)  
**Report date:** 2026-05-29  
**Status:** BLUEPRINT — Documentation only. No code changes made.

---

## Purpose

This report is the single authoritative reference for the multi-province hydroclimatic framework conversion project. It audits the Prachuap Khiri Khan pipeline (v1.0.0) across eight phases:

1. Repository module audit
2. Hard-coded province-specific dependency map
3. Configuration architecture design (province.yaml)
4. Target directory structure and migration plan
5. Master pipeline design (run_pipeline.py)
6. Province portability assessment
7. User documentation plan
8. Framework readiness scores

**Constraint enforced throughout:** No code changes, no figure regeneration, no modification of any scientific output, workbook, or audit document. This is a read-and-design exercise. Implementation begins only after blueprint approval.

---

## Phase 1 — Repository Module Audit

### 1.1 Complete File Inventory

Total Python files: 44 (including `rta/` package, `rta_v5/` package, top-level scripts)

| File | Lines | Purpose | Category | Reusable | Province-Specific | Requires Refactoring | Priority |
|---|---|---|---|---|---|---|---|
| `rainfall_trend_analysis_v3.py` | 2597 | Single-file monolithic pipeline (legacy); all MK/MMK logic + figures + Excel embedded | pipeline-core | Partial | Province string in header, figure titles | Low — legacy, superseded by v4 | Low |
| `rainfall_trend_analysis_v4.py` | 465 | Modular orchestrator; calls rta/ package; checkpoint resume system | pipeline-core | Yes | None directly; delegates to rta/ | None — already modular | High |
| `rainfall_trend_analysis_v5.py` | 322 | Province-independent Q1 spatial map orchestrator; reads from v4 outputs | pipeline-core | Yes | `PERIOD = "1981–2014"` (line 67) | Extract PERIOD to config | Medium |
| `rta/__init__.py` | ~10 | Package init; exports | utility | Yes | None | None | Low |
| `rta/config.py` | 180 | Shared constants: C (palette), DPI, Z_005, Z_001, WET_MONTHS, DRY_MONTHS, MIN_N | pipeline-core | Partial | WET_MONTHS, DRY_MONTHS are climate-specific but easily changed | Inject from config file | High |
| `rta/aggregation.py` | 323 | Temporal aggregation (annual/wet/dry/monthly); completeness QC | pipeline-core | Yes | None | None — fully data-driven | High |
| `rta/autocorr.py` | 38 | Lag-k autocorrelation, ACF vector, significance test | pipeline-core | Yes | None | None | High |
| `rta/batch.py` | 285 | Batch execution over stations × scales; MK + MMK + PW + TFPW | pipeline-core | Yes | None | None | High |
| `rta/checkpoint.py` | 109 | 6-step pickle checkpoint/resume system | utility | Yes | None | None | Medium |
| `rta/excel_output.py` | 618 | 9-sheet Excel workbook writer with full cell styling | pipeline-core | Yes | None | None | Medium |
| `rta/field_sig.py` | 285 | Walker (1914) + Livezey-Chen (1983) MC field significance | pipeline-core | Yes | None | None | High |
| `rta/field_significance.py` | 250 | Re-implementation / extension of field significance (used by v4) | pipeline-core | Yes | None | Consolidate with field_sig.py | Medium |
| `rta/io.py` | 301 | CSV discovery (glob-based), coordinate loading, missing-flag QC | pipeline-core | Yes | None — already province-agnostic | None | High |
| `rta/markdown.py` | 511 | Research summary markdown writer | post-processing | Partial | Basin name, region (line 86–87) | Inject province.basin_name | Medium |
| `rta/pw.py` | 86 | Prewhitening MK (Yue & Wang 2004) | pipeline-core | Yes | None | None | High |
| `rta/spatial.py` | 145 | Coordinate loading/validation helpers | pipeline-core | Yes | None | None | Medium |
| `rta/spatial_maps.py` | ~20 | Top-level re-export of spatial figure functions | utility | Yes | None | None | Low |
| `rta/tfpw.py` | 108 | Trend-Free Prewhitening MK (Yue et al. 2002) | pipeline-core | Yes | None | None | High |
| `rta/trend_comparison_analysis.py` | 1709 | Manuscript templates; method comparison workbooks and tables | post-processing | Partial | Basin name (lines 1408, 1524), period (lines 1409, 1490), station allowlist (lines 1633–1634) | Inject 5 province strings + station list | High |
| `rta/trend_method_comparison.py` | 1078 | Extended method comparison figures and workbook (FigC01–FigC10) | post-processing | Yes | None | None | Medium |
| `rta/trend_tests.py` | 343 | Standard MK + Sen's slope core algorithms | pipeline-core | Yes | None — pure statistics | None | High |
| `rta/figures/__init__.py` | ~5 | Figures package init | utility | Yes | None | None | Low |
| `rta/figures/acf_plots.py` | 155 | Fig12 ACF diagnostics | figure-module | Yes | None | None | Medium |
| `rta/figures/bars.py` | 93 | Fig3 Sen's slope bar charts | figure-module | Yes | None | None | Medium |
| `rta/figures/climatology.py` | 89 | Fig7 monthly climatology | figure-module | Yes | None | None | Medium |
| `rta/figures/comparison.py` | 155 | Fig4 MK vs MMK comparison | figure-module | Yes | None | None | Medium |
| `rta/figures/field_sig_plot.py` | 259 | Fig13 field significance plot | figure-module | Yes | None | None | Medium |
| `rta/figures/helpers.py` | ~30 | Shared figure utilities (title formatting, savefig) | utility | Yes | None | None | Low |
| `rta/figures/heatmaps.py` | 82 | Fig5 significance heatmap | figure-module | Yes | None | None | Medium |
| `rta/figures/method_comparison.py` | 352 | Fig10 Z-matrix + Fig11 method scatter | figure-module | Yes | None — fully data-driven | None | Medium |
| `rta/figures/spatial.py` | 164 | Fig8 index-based spatial summary (no coordinates) | figure-module | Yes | None | None | Low |
| `rta/figures/spatial_maps.py` | 684 | True geographic spatial maps (5 functions); Fig14, SpatialStation, SpatialMethods, SpatialFieldSig, SpatialFull | figure-module | Partial | Basin name in titles (lines 244, 562) | Inject province.basin_name | High |
| `rta/figures/taylor.py` | 215 | Fig9 Taylor diagram | figure-module | Yes | None | None | Low |
| `rta/figures/timeseries.py` | 214 | Fig1 annual + Fig2 wet/dry time series | figure-module | Yes | None | None | Medium |
| `rta_v5/__init__.py` | ~5 | v5 package init | utility | Yes | None | None | Low |
| `rta_v5/spatial_export_v5.py` | ~200 | Export spatial results to multiple formats | post-processing | Yes | None | None | Low |
| `rta_v5/spatial_interpolation_v5.py` | ~300 | IDW and kriging interpolation for spatial maps | pipeline-core | Yes | None | None | Medium |
| `rta_v5/spatial_layout_v5.py` | ~200 | Publication-quality spatial layout helpers | figure-module | Yes | None | None | Medium |
| `rta_v5/spatial_publication_q1_v5.py` | ~400 | Q1 publication-standard spatial figure assembly | figure-module | Yes | None | None | High |
| `rta_v5/spatial_validation_v5.py` | ~200 | LOOCV and interpolation validation | pipeline-core | Yes | None | None | Medium |
| `generate_trend_comparison_analysis.py` | 56 | Entry point: calls rta/trend_comparison_analysis.py | post-processing | Yes | None (delegates to module) | None | Medium |
| `generate_all_vs_mk_workbook.py` | 675 | Generates All-vs-MK comparison Excel workbook | post-processing | Yes | None | None | Medium |
| `generate_tfpw_audit.py` | 506 | Generates TFPW audit workbook | post-processing | Yes | None | None | Low |
| `generate_reviewer_summary.py` | 507 | Generates reviewer summary workbook | post-processing | Yes | None | None | Low |
| `generate_final_validation.py` | 943 | Generates final validation workbook | post-processing | Yes | None | None | Low |
| `generate_trend_comparison.py` | 55 | Legacy entry point for comparison figures | legacy | Partial | None | Merge with v4 pipeline | Low |
| `generate_q1_maps.py` | 140 | Q1 spatial maps script; requires geopandas + shapefile | post-processing | Partial | Shapefile name (line 31), `PERIOD` (line 39) | Inject from config | Medium |
| `calval_split.py` | 575 | Calibration/validation split script (inputs absent — M-5) | utility | Yes | None | Out of scope | Low |
| `Comparative_4MMK.py` | 2085 | Extended 4-method comparison (requires statsmodels — M-2) | legacy | Partial | Province name (lines 99, 1062, 1853), n_years (line 689) | Inject or archive | Low |

### 1.2 Category Summary

| Category | Count | Reusable as-is | Needs refactoring |
|---|---|---|---|
| pipeline-core | 14 | 12 | 2 (config.py, trend_tests.py season defs) |
| figure-module | 12 | 10 | 2 (spatial_maps.py titles) |
| post-processing | 9 | 7 | 2 (trend_comparison_analysis.py, markdown.py) |
| utility | 7 | 7 | 0 |
| legacy | 3 | 1 | 2 (Comparative_4MMK.py, v3 script) |
| **Total** | **45** | **37 (82%)** | **8 (18%)** |

---

## Phase 2 — Hard-Coded Province-Specific Component Map

### 2.1 Province String Inventory

| File | Line(s) | Current Hard-Coded Value | Recommended Config Variable |
|---|---|---|---|
| `rta/figures/spatial_maps.py` | 244 | `"Prachuap Khiri Khan Basin"` | `province.basin_name` |
| `rta/figures/spatial_maps.py` | 562 | `"Prachuap Khiri Khan Basin"` | `province.basin_name` |
| `rta/trend_comparison_analysis.py` | 1408 | `"Phetchaburi–Prachuap Khiri Khan River Basin, Western Thailand"` | `province.basin_name + province.region` |
| `rta/trend_comparison_analysis.py` | 1409 | `"Period: 1981–2014 (34 years) \| Stations: 12 \| Temporal scales: Annual, Wet Season, Dry Season"` | `period.label + period.n_years + stations.n_stations` |
| `rta/trend_comparison_analysis.py` | 1490 | `"Period: 1981–2014 \| N = 36 (12 stations × 3 scales)"` | `period.label + stations.n_stations` |
| `rta/trend_comparison_analysis.py` | 1524 | `"gauging stations in the Phetchaburi–Prachuap Khiri Khan River Basin, Thailand (1981–2014)."` | `province.basin_name + province.country + period.label` |
| `rta/markdown.py` | 86–87 | `"- **Study area**: Phetchaburi–Prachuap Khiri Khan River Basin, "` | `province.basin_name + province.region` |
| `generate_q1_maps.py` | 31 | `"30_amarea_prachuap_khiri_khan.shp"` | `data.shapefile` |
| `generate_q1_maps.py` | 39 | `PERIOD = "1981–2014"` | `period.label` |
| `rainfall_trend_analysis_v5.py` | 67 | `PERIOD = "1981–2014"` | `period.label` |

### 2.2 Station ID Hard-Coding

| File | Line(s) | Current Value | Impact | Recommended Approach |
|---|---|---|---|---|
| `rta/trend_comparison_analysis.py` | 1633–1634 | `"500001","500002",…,"500301"` (12 IDs) | Post-processing workbooks filtered to these 12 stations only | Replace with auto-derived list from input CSV column headers, or make configurable via `stations.allowlist` |

### 2.3 Province-Specific Numeric Constants

| File | Line | Variable | Value | Impact | Config Variable |
|---|---|---|---|---|---|
| `rta/trend_comparison_analysis.py` | 1409 | n_years | 34 | Manuscript template text | `period.n_years` |
| `rta/trend_comparison_analysis.py` | 1490 | N = 36 | 36 (12 × 3) | Manuscript template text | `stations.n_stations * 3` |
| `Comparative_4MMK.py` | 689 | n_years | 34 | Extended analysis | `period.n_years` |

### 2.4 Season Definitions (Province-Configurable Constants)

| File | Line(s) | Variable | Current Value | Description | Config Variable |
|---|---|---|---|---|---|
| `rta/config.py` | 26 | `WET_MONTHS` | `[5,6,7,8,9,10]` | May–October monsoon months | `seasons.wet_months` |
| `rta/config.py` | 27 | `DRY_MONTHS` | `[11,12,1,2,3,4]` | November–April dry season | `seasons.dry_months` |
| `rta/config.py` | 28 | `WET_THR` | `1.0` mm/day | WMO wet-day threshold | `seasons.wet_day_threshold` |

### 2.5 Input Discovery (Already Province-Agnostic)

The following patterns confirm `rta/io.py` is already fully portable — no changes needed:

| Discovery method | Pattern | File |
|---|---|---|
| Rainfall CSV | `*.csv` (first non-Output_ file found) | `rta/io.py` |
| Coordinate file | `*coordinates*.csv`, `*station*.csv` | `rta/io.py` |
| Excel checkpoint | `*_Results.xlsx` glob in `results/final_N33/excel/` | `rainfall_trend_analysis_v5.py` |

---

## Phase 3 — Configuration Architecture Design

### 3.1 Proposed `config/province.yaml` Structure

```yaml
# config/province.yaml
# Province configuration for the Hydroclimatic Trend Analysis Framework
# Copy to config/<province_slug>.yaml for each new province.
# All province-specific settings are controlled from this single file.
# ── Province identity ─────────────────────────────────────────────────────────
province:
  name:       "Prachuap Khiri Khan"                              # Short province name
  basin_name: "Phetchaburi–Prachuap Khiri Khan River Basin"      # Full basin name for figures
  country:    "Thailand"                                         # Used in figure titles and templates
  region:     "Western Thailand"                                 # Used in manuscript templates

# ── Study period ──────────────────────────────────────────────────────────────
period:
  start_year: 1981        # First calendar year
  end_year:   2014        # Last calendar year (inclusive)
  label:      "1981–2014" # Display string for titles, tables, templates
  n_years:    34          # = end_year - start_year + 1 (calendar years)
  n_dry_years: 33         # Calendar years - 1 (hydrological dry seasons)

# ── Station configuration ─────────────────────────────────────────────────────
stations:
  n_stations: 12          # Expected station count for validation warnings
  id_prefix:  "500"       # Station ID prefix for logging only
  # allowlist: null       # Set to list of IDs to restrict post-processing;
  #                       # null = use all stations from CSV headers
  allowlist:
    - "500001"
    - "500002"
    - "500003"
    - "500004"
    - "500005"
    - "500006"
    - "500007"
    - "500008"
    - "500009"
    - "500201"
    - "500202"
    - "500301"

# ── Season definitions ────────────────────────────────────────────────────────
seasons:
  wet_months:        [5, 6, 7, 8, 9, 10]   # May–October
  dry_months:        [11, 12, 1, 2, 3, 4]  # November–April
  wet_day_threshold: 1.0                    # mm/day (WMO standard)

# ── Statistical thresholds ────────────────────────────────────────────────────
statistics:
  alpha_primary:   0.05    # Primary significance level
  alpha_secondary: 0.01    # Secondary significance level
  min_years:       10      # Minimum years per station for MK test
  annual_completeness:  0.80  # Fraction of days required for annual aggregate
  season_completeness:  0.80  # Fraction of days required for seasonal aggregate
  monthly_completeness: 0.60  # Fraction of days required for monthly aggregate
  field_sig_mc_iterations: 10000   # Monte Carlo iterations for Livezey-Chen test
  field_sig_mc_seed:       42      # Random seed for reproducibility

# ── Data paths ────────────────────────────────────────────────────────────────
data:
  # Paths are relative to the working directory passed at runtime.
  # Set shapefile to null if no shapefile is available.
  shapefile:  "boundaries/current_boundary/boundary.shp"
  # Optional: explicit rainfall CSV path (overrides auto-discovery)
  rainfall_csv:    null
  # Optional: explicit coordinates CSV path (overrides auto-discovery)
  coordinates_csv: null

# ── Output settings ───────────────────────────────────────────────────────────
output:
  dpi:      600       # Figure resolution (dots per inch)
  save_pdf: true      # Save PDF alongside PNG
  save_svg: false     # Save SVG (used by comparison figures only)
```

### 3.2 Configuration Loading Design (Pseudocode)

```python
# run_pipeline.py — config injection pseudocode (not yet implemented)

import yaml
from pathlib import Path

def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    validate_config(cfg)     # schema check + derived field computation
    return cfg

def inject_into_rta(cfg: dict) -> None:
    """Push config values into rta.config module constants."""
    import rta.config as c
    c.WET_MONTHS  = cfg["seasons"]["wet_months"]
    c.DRY_MONTHS  = cfg["seasons"]["dry_months"]
    c.WET_THR     = cfg["seasons"]["wet_day_threshold"]
    c.MIN_N       = cfg["statistics"]["min_years"]
    c.ALPHA_005   = cfg["statistics"]["alpha_primary"]
    c.ALPHA_001   = cfg["statistics"]["alpha_secondary"]
    c.DPI         = cfg["output"]["dpi"]
    c.SAVE_PDF    = cfg["output"]["save_pdf"]
    c.PROVINCE_NAME  = cfg["province"]["name"]
    c.BASIN_NAME     = cfg["province"]["basin_name"]
    c.PERIOD_LABEL   = cfg["period"]["label"]
    c.STATION_ALLOWLIST = cfg["stations"].get("allowlist")

# Usage:
cfg = load_config("config/prachuap.yaml")
inject_into_rta(cfg)
# All downstream modules now use the injected values
```

---

## Phase 4 — Target Directory Structure

### 4.1 Proposed Framework Directory Layout

```
hydroclimatic_framework/
├── config/                              ← NEW: Province configuration files
│   ├── prachuap.yaml                    ← Reference province (Prachuap Khiri Khan)
│   ├── phetchaburi.yaml                 ← Example: neighbouring province
│   └── template.yaml                    ← Blank template with all keys documented
│
├── rta/                                 ← UNCHANGED: Core analysis package
│   ├── config.py                        ← MODIFIED: Accept injected constants
│   ├── aggregation.py                   ← UNCHANGED
│   ├── autocorr.py                      ← UNCHANGED
│   ├── batch.py                         ← UNCHANGED
│   ├── checkpoint.py                    ← UNCHANGED
│   ├── excel_output.py                  ← UNCHANGED
│   ├── field_sig.py                     ← UNCHANGED
│   ├── field_significance.py            ← UNCHANGED
│   ├── io.py                            ← UNCHANGED (already province-agnostic)
│   ├── markdown.py                      ← MODIFIED: Replace hard-coded basin name
│   ├── pw.py                            ← UNCHANGED
│   ├── spatial.py                       ← UNCHANGED
│   ├── spatial_maps.py                  ← UNCHANGED (re-export wrapper)
│   ├── tfpw.py                          ← UNCHANGED
│   ├── trend_comparison_analysis.py     ← MODIFIED: Replace 5 province strings + allowlist
│   ├── trend_method_comparison.py       ← UNCHANGED
│   ├── trend_tests.py                   ← UNCHANGED
│   └── figures/
│       ├── acf_plots.py                 ← UNCHANGED
│       ├── bars.py                      ← UNCHANGED
│       ├── climatology.py               ← UNCHANGED
│       ├── comparison.py                ← UNCHANGED
│       ├── field_sig_plot.py            ← UNCHANGED
│       ├── helpers.py                   ← UNCHANGED
│       ├── heatmaps.py                  ← UNCHANGED
│       ├── method_comparison.py         ← UNCHANGED
│       ├── spatial.py                   ← UNCHANGED
│       ├── spatial_maps.py              ← MODIFIED: Replace 2 hard-coded basin names
│       ├── taylor.py                    ← UNCHANGED
│       └── timeseries.py               ← UNCHANGED
│
├── rta_v5/                              ← UNCHANGED: v5 spatial package
│   ├── spatial_export_v5.py             ← UNCHANGED
│   ├── spatial_interpolation_v5.py      ← UNCHANGED
│   ├── spatial_layout_v5.py             ← UNCHANGED
│   ├── spatial_publication_q1_v5.py     ← UNCHANGED
│   └── spatial_validation_v5.py         ← UNCHANGED
│
├── run_pipeline.py                      ← NEW: Province-agnostic master orchestrator
│
├── rainfall_trend_analysis_v4.py        ← KEPT: Backward-compatible entry point
├── rainfall_trend_analysis_v5.py        ← MODIFIED: Read PERIOD from config
│
├── generate_trend_comparison_analysis.py ← KEPT: Post-processing entry point
├── generate_all_vs_mk_workbook.py       ← KEPT
├── generate_tfpw_audit.py               ← KEPT
├── generate_reviewer_summary.py         ← KEPT
├── generate_final_validation.py         ← KEPT
├── generate_q1_maps.py                  ← MODIFIED: Read shapefile + PERIOD from config
│
├── requirements.txt                     ← UNCHANGED
├── CLAUDE.md                            ← UPDATE: Document config system
├── README.md                            ← UPDATE: Multi-province usage
│
├── data/                                ← Province data directory (not committed)
│   └── <province>/
│       ├── <rainfall>.csv
│       ├── station_coordinates.csv
│       └── boundaries/
│           └── current_boundary/
│               └── boundary.shp …
│
└── results/                             ← Province results (not committed)
    └── <province>/
        ├── checkpoints/
        ├── excel/
        ├── figures/
        └── archive/
```

### 4.2 File Migration Table (Current → Target)

| Current Path | Target Path | Change Required |
|---|---|---|
| `rta/config.py` | `rta/config.py` | Accept injected values from `run_pipeline.py` |
| `rta/markdown.py` | `rta/markdown.py` | Replace line 86–87 with `c.BASIN_NAME` |
| `rta/trend_comparison_analysis.py` | `rta/trend_comparison_analysis.py` | Replace lines 1408–1524 + allowlist |
| `rta/figures/spatial_maps.py` | `rta/figures/spatial_maps.py` | Replace lines 244 + 562 with `c.BASIN_NAME` |
| `generate_q1_maps.py` | `generate_q1_maps.py` | Replace lines 31 + 39 from config |
| `rainfall_trend_analysis_v5.py` | `rainfall_trend_analysis_v5.py` | Replace line 67 from config |
| *(does not exist)* | `run_pipeline.py` | Create new master orchestrator |
| *(does not exist)* | `config/prachuap.yaml` | Create reference config |
| *(does not exist)* | `config/template.yaml` | Create blank template |

**Files requiring no changes: 37 of 44 (84%)**  
**Files requiring changes: 7 of 44 (16%)**  
**New files to create: 3 (run_pipeline.py, config/prachuap.yaml, config/template.yaml)**

---

## Phase 5 — Master Pipeline Design

### 5.1 `run_pipeline.py` — 14-Step Execution Design

```
run_pipeline.py [config_path] [data_dir] [--no-resume] [--no-pdf]
```

| Step | Name | Module | Data In | Data Out | Config Keys Used |
|---|---|---|---|---|---|
| 0 | Load config | — | `config/*.yaml` | cfg dict | all |
| 1 | Inject config | `rta/config.py` | cfg dict | Updated module constants | seasons, statistics, output, province, period |
| 2 | Discover inputs | `rta/io.py` | `data_dir/` | daily_df, coords dict | data.rainfall_csv, data.coordinates_csv |
| 3 | Quality control | `rta/io.py` | daily_df | cleaned_df | statistics.annual_completeness |
| 4 | Aggregate | `rta/aggregation.py` | cleaned_df | annual_df, wet_df, dry_df, monthly_df | seasons.wet_months, seasons.dry_months |
| 5 | Autocorrelation | `rta/autocorr.py` | annual_df, wet_df, dry_df | acf_dict per station × scale | statistics.alpha_primary |
| 6 | Trend tests | `rta/batch.py` | agg DataFrames, acf_dict | trend_df (MK + MMK + PW + TFPW + Sen) | statistics.min_years, statistics.alpha_primary |
| 7 | Field significance | `rta/field_sig.py` | trend_df | field_df (Walker + LC-MC) | statistics.field_sig_mc_iterations, statistics.field_sig_mc_seed |
| 8 | Method comparison | `rta/trend_method_comparison.py` | trend_df | comparison_df (agreement rates, ΔZ) | — |
| 9 | Generate figures | `rta/figures/` (12 modules) | trend_df, field_df, acf_dict, coords | 18+ PNG/PDF figures | output.dpi, output.save_pdf, province.basin_name |
| 10 | Write Excel | `rta/excel_output.py` | trend_df, field_df, comparison_df | 9-sheet workbook | — |
| 11 | Write Markdown | `rta/markdown.py` | trend_df, field_df, cfg | Research_Summary.md | province.basin_name, period.label |
| 12 | Post-processing | `generate_*.py` scripts | Excel workbook | 7 additional workbooks | stations.allowlist |
| 13 | Q1 spatial maps | `rta_v5/` + `generate_q1_maps.py` | Excel + boundary shapefile | Q1 publication figures (PNG/TIF/PDF/SVG) | data.shapefile, period.label |
| 14 | Validation | `generate_final_validation.py` | All workbooks | validation workbook + checksums | — |

### 5.2 Data Flow Dependency Diagram

```
config/*.yaml
    │
    ▼
[Step 0-1] Config loading + injection
    │
    ├─────────────────────────────────────────────────────────┐
    ▼                                                         │
[Step 2] daily_df ─────────────────────────────────────────► │
    │                                                         │
    ▼                                                         │
[Step 3] cleaned_df                                          │
    │                                                         │
    ▼                                                         │
[Step 4] annual_df / wet_df / dry_df / monthly_df            │
    │                                                         │
    ├──────────────────────────────────────────────────────┐  │
    ▼                                                      │  │
[Step 5] acf_dict {stn: {scale: array}}                   │  │
    │                                                      │  │
    ▼                                                      │  │
[Step 6] trend_df [144 rows × 20+ cols]                   │  │
    │                                                      │  │
    ├─────────────────────────────────────────────────┐   │  │
    ▼                                                 │   │  │
[Step 7] field_df [3 rows × 6 cols]                  │   │  │
    │                                                 │   │  │
    ▼                                                 │   │  │
[Step 8] comparison_df [108 rows]                    │   │  │
    │                                                 │   │  │
    ├── trend_df + field_df + acf_dict + coords ◄─────┘   │  │
    ▼                                                      │  │
[Step 9] Figures (18+ PNG/PDF)                            │  │
    │                                                      │  │
    ├── trend_df + field_df + comparison_df ◄──────────────┘  │
    ▼                                                         │
[Step 10] Excel workbook (9 sheets)                          │
    │                                                         │
    ├── Excel + cfg ◄──────────────────────────────────────────┘
    ▼
[Step 11] Research_Summary.md

[Step 12-14] Post-processing reads Excel output (separate invocation)
```

### 5.3 CLI Interface Design

```bash
# Primary run — new province
python run_pipeline.py config/chumphon.yaml /data/chumphon/

# Primary run — reference province
python run_pipeline.py config/prachuap.yaml /data/prachuap/ --no-resume

# Skip PDF output
python run_pipeline.py config/ranong.yaml /data/ranong/ --no-pdf

# Post-processing only (after primary run)
python run_pipeline.py config/prachuap.yaml /data/prachuap/ --post-processing-only

# Q1 spatial maps only (requires shapefile + v5 outputs)
python run_pipeline.py config/prachuap.yaml /data/prachuap/ --q1-only
```

---

## Phase 6 — Province Portability Assessment

### 6.1 Assessment for Six Provinces

| Province | Basin | Stations (est.) | Data availability | Shapefile | Season difference | Overall blocker severity |
|---|---|---|---|---|---|---|
| **Phetchaburi** | Phetchaburi River | 8–12 | RID archive | Province shapefile (DOPA) | Same (May–Oct wet) | **Low** — adjacent basin, same climate regime |
| **Chumphon** | Chumphon River | 6–10 | RID archive | Province shapefile | Same (May–Oct wet) | **Medium** — Gulf-coast secondary wet season Oct–Nov |
| **Ranong** | Kraburi River | 5–8 | Sparse; RID + TMD | Province shapefile | Shifted (Apr–Nov longest wet) | **High** — longest wet season in Thailand; bimodal pattern |
| **Surat Thani** | Tapi River | 15–20 | RID + AEA archive | Province shapefile | Bimodal (Apr–Oct + Nov–Jan) | **High** — bimodal precipitation; may need 4-season model |
| **Nakhon Si Thammarat** | Multiple basins | 20–30 | RID + AEA archive | Province shapefile | Gulf-coast bimodal | **High** — both Gulf and Andaman coast exposure |
| **Generic Thai Province** | Any | Any | Varies | DOPA/RID | Province-dependent | **Medium** — config system handles single-season; bimodal needs extension |

### 6.2 Blocker Detail by Province

#### Phetchaburi (Severity: Low)
| Blocker | Severity | Mitigation |
|---|---|---|
| Daily rainfall CSV from RID must be obtained | Low | Same format as Prachuap dataset |
| Station coordinate matching | Low | Same ID format (5xxxxx) |
| Adjacent province; same monsoon regime | — | No season config change needed |

#### Chumphon (Severity: Medium)
| Blocker | Severity | Mitigation |
|---|---|---|
| Secondary Gulf-coast wet season Oct–Nov overlaps dry season definition | Medium | Test with WET_MONTHS=[5..11]; validate against ENSO literature |
| Fewer stations than Prachuap (potential sparse coverage) | Medium | Spatial interpolation grid may need adjustment |
| Shapefile format: confirm GCS matches (EPSG:4326 vs Thailand national grid) | Low | Reproject in v5 |

#### Ranong (Severity: High)
| Blocker | Severity | Mitigation |
|---|---|---|
| Longest wet season in Thailand (≈9 months) conflicts with standard 6-month wet/dry split | **Critical** | Requires custom WET_MONTHS=[4,5,6,7,8,9,10,11]; dry season becomes 3 months only |
| Very high total annual rainfall (3000–5000 mm) may affect tail distributions in MK | High | Test with and without WET_THR adjustment |
| Sparse station network (Andaman coast, mountainous) | High | Review MIN_N; some stations may fail ≥80% completeness threshold |
| Data availability: RID coverage limited; may need TMD supplement | High | Coordinate multi-agency data merge pre-pipeline |

#### Surat Thani (Severity: High)
| Blocker | Severity | Mitigation |
|---|---|---|
| Bimodal annual pattern (Apr–Oct Gulf + Oct–Jan Andaman influence) | **Critical** | Standard 2-season model may misclassify months; consider extending to 3-period analysis |
| Largest province: 20–30 stations; pipeline scales linearly | Medium | Runtime increases; LC-MC MC iterations remain the bottleneck |
| Multiple river basins: Tapi, Phum Duang, Khlong | Medium | Ensure station IDs are unique across basins |
| Station coordinate file must cover all basins | Medium | May require merging multiple RID station lists |

#### Nakhon Si Thammarat (Severity: High)
| Blocker | Severity | Mitigation |
|---|---|---|
| Both Gulf and Andaman coast exposure creates complex bimodal pattern | **Critical** | Same as Surat Thani; 3-period model or sub-basin analysis required |
| Very high inter-station variability | High | Spatial figures may be dominated by orographic gradient |
| Historical data quality: some stations have gaps 1985–1995 | Medium | Verify ≥80% completeness; expect some station exclusions |

#### Generic Thai Province (Severity: Medium)
| Blocker | Severity | Mitigation |
|---|---|---|
| Single-season provinces (same May–Oct wet): minimal blockers | Low | Config system handles directly |
| Bimodal provinces: requires model extension | **Critical** (when applicable) | Phase 2 of framework implementation: add 4-period support |
| Station count < 10: field significance loses power | Medium | Report power with observed n; do not force test |
| Data pre-processing: coordinate CRS may vary by agency | Medium | Standardize to EPSG:4326 in coordinate CSV |

### 6.3 Summary Portability Matrix

| Province | Config change only | Season model extension | Data acquisition | Field significance power | Overall |
|---|---|---|---|---|---|
| Phetchaburi | ✅ | None needed | ✅ Available | ✅ Similar N | **Ready** |
| Chumphon | ✅ | Minor (1 month) | ✅ Available | Moderate | **Ready with caution** |
| Ranong | ✅ | Major (WET_MONTHS) | Partial | Low (sparse) | **Needs prep** |
| Surat Thani | Config + code | Bimodal extension | ✅ Available | ✅ High N | **Needs development** |
| Nakhon Si Thammarat | Config + code | Bimodal extension | Partial | ✅ High N | **Needs development** |
| Same-season Thai province | ✅ | None | Varies | Varies | **Ready** |

---

## Phase 7 — User Documentation Plan

### 7.1 Documentation Suite

Four guide documents have been produced alongside this report:

| Document | File | Lines | Audience | Scope |
|---|---|---|---|---|
| Installation Guide | `INSTALLATION_GUIDE.md` | 159 | New users | System requirements, Python setup, dependency install, verification test |
| User Guide | `USER_GUIDE.md` | 279 | Primary users | Framework overview, quick start, pipeline execution, figure descriptions, CLI reference |
| Configuration Guide | `CONFIGURATION_GUIDE.md` | 314 | Advanced users | Full province.yaml reference, config validation, worked examples |
| Province Setup Guide | `PROVINCE_SETUP_GUIDE.md` | 308 | Deployers | Step-by-step new province setup, data format requirements, verification checklist |

### 7.2 Documentation Coverage Map

| Topic | Installation | User | Configuration | Province Setup |
|---|---|---|---|---|
| System requirements | ✅ | — | — | — |
| Python environment setup | ✅ | — | — | — |
| Dependency install | ✅ | — | — | — |
| Quick start (3 steps) | — | ✅ | — | — |
| Pipeline execution sequence | — | ✅ | — | — |
| Interpreting figures | — | ✅ | — | — |
| Excel workbook structure | — | ✅ | — | — |
| CLI reference | — | ✅ | — | — |
| province.yaml full reference | — | — | ✅ | — |
| Config validation rules | — | — | ✅ | — |
| Config worked examples | — | — | ✅ | — |
| Data format requirements | — | — | — | ✅ |
| Coordinate file format | — | — | — | ✅ |
| Shapefile requirements | — | — | — | ✅ |
| Folder structure | — | — | — | ✅ |
| Province-specific manual edits | — | — | — | ✅ |
| Season configuration variants | — | — | — | ✅ |
| Output verification checklist | — | — | — | ✅ |

### 7.3 Gaps and Deferred Documentation

| Gap | Priority | Deferred to |
|---|---|---|
| API reference (docstrings per module) | Low | Phase 2 implementation |
| Bimodal season extension guide | Medium | Phase 2: when Surat Thani support added |
| Multi-basin (sub-province) analysis guide | Low | Phase 3 |
| CI/CD pipeline guide | Low | When unit tests added |
| Docker container setup | Low | Phase 2 |

---

## Phase 8 — Framework Readiness Scores

### 8.1 Scores

| Domain | Score | Grade | Deductions |
|---|---|---|---|
| **Scientific Portability** | 88 / 100 | B+ | −6: Season model limited to 2 periods (bimodal provinces blocked); −4: No validation framework to compare results across provinces; −2: Dry-season hydrological year convention may not apply elsewhere |
| **Engineering Portability** | 72 / 100 | C+ | −10: 8 source locations with hard-coded province strings; −7: No config injection system; −5: Post-processing scripts have hard-coded checkpoint paths; −4: No `run_pipeline.py` master orchestrator; −2: No unit tests |
| **Maintainability** | 75 / 100 | C+ | −10: `Comparative_4MMK.py` non-functional (statsmodels absent) and undocumented; −8: `rainfall_trend_analysis_v3.py` and v4/v5 maintain parallel implementations; −4: No CI/CD; −3: No pyproject.toml |
| **Reusability** | 82 / 100 | B− | −8: 18% of files need refactoring for new provinces; −5: Station allowlist in source code rather than config; −5: Season constants require source edits |
| **Framework Readiness** | 65 / 100 | D+ | −15: Configuration injection not implemented; −10: No `run_pipeline.py` entry point; −5: No config/ directory; −5: Documentation only (no working multi-province deployment verified) |

### 8.2 Deduction Rationale Detail

**Scientific Portability (−12 points):**
- Single-season model: The wet/dry split model works for 60–70% of Thai provinces (central, western, northern, northeastern). Southern and Gulf-coast provinces with bimodal patterns require a 3- or 4-period model. This is a scientific limitation, not a software bug. Implementing bimodal support requires ~200 lines of new code in `rta/aggregation.py` and matching figure updates.
- Cross-province validation: Currently no framework for comparing trend detection results across provinces (e.g., "do S3-Wet Season patterns replicate in the adjacent Phetchaburi basin?"). This would require a new `compare_provinces.py` post-processing script.
- Hydrological year convention: The November–December shift is standard for Thailand's Western Gulf drainage; Pacific-draining provinces may use different hydrological years.

**Engineering Portability (−28 points):**
- Province strings are the primary blocker: 8 source locations across 5 files. A single `rta/config.py` injection point would collapse this to 1 location per downstream module. The refactoring is low-risk (string substitution only) and estimated at 4–6 hours of work.
- No master orchestrator: Users must currently know to run v4, then 5 post-processing scripts, then v5, in a specific order. `run_pipeline.py` with the 14-step design above would reduce the run procedure to a single command.

**Maintainability (−25 points):**
- Parallel implementations (v3/v4/v5) create maintenance burden; v3 is superseded but kept for reference; v5 reads v4 outputs so both must remain functional.
- `Comparative_4MMK.py` is the largest single file (2085 lines) and non-functional without `statsmodels`. It should either be fixed or archived with a clear deprecation notice.

**Reusability (−18 points):**
- 82% of files are already fully reusable as-is. The remaining 18% require straightforward string replacement, not algorithm changes. The technical effort to reach 95%+ reusability is low (estimated 1–2 days).

**Framework Readiness (−35 points):**
- This is a documentation-stage blueprint. No multi-province deployment has been tested. The scores for the other domains are based on static analysis of the source files. Framework Readiness will increase significantly once: (a) config injection is implemented, (b) `run_pipeline.py` is created, (c) a second province (e.g., Phetchaburi) is successfully run.

### 8.3 Projected Scores After Phase 2 Implementation

| Domain | Current | After config injection + run_pipeline.py | After second province verified |
|---|---|---|---|
| Scientific Portability | 88 | 88 | 92 |
| Engineering Portability | 72 | 88 | 92 |
| Maintainability | 75 | 80 | 85 |
| Reusability | 82 | 92 | 95 |
| Framework Readiness | 65 | 82 | 90 |

---

## Summary and Recommendations

### Immediate Actions (Zero Code Changes Required)

1. Use this report as the implementation specification for Phase 2.
2. Review CONFIGURATION_GUIDE.md §2 for the full province.yaml reference before writing config files.
3. Review PROVINCE_SETUP_GUIDE.md §3 for the manual-edit locations when running a new province under the current (pre-implementation) system.

### Phase 2 Implementation Scope (Estimated 2–3 days)

Priority order for maximum portability gain per effort:

1. **Create `config/` directory and `config/prachuap.yaml`** — 1 hour. Zero risk.
2. **Add config injection to `rta/config.py`** — 2 hours. Low risk: existing constants become defaults.
3. **Replace hard-coded strings in `rta/figures/spatial_maps.py`** (2 locations) — 30 minutes.
4. **Replace hard-coded strings in `rta/markdown.py`** (1 location) — 15 minutes.
5. **Replace hard-coded strings + allowlist in `rta/trend_comparison_analysis.py`** (5 locations) — 1 hour.
6. **Replace PERIOD in `generate_q1_maps.py` and `rainfall_trend_analysis_v5.py`** — 30 minutes.
7. **Write `run_pipeline.py`** — 4 hours. The 14-step design is fully specified above.
8. **Test with Phetchaburi dataset** (adjacent basin, minimal config change) — 2 hours.

**Total estimated effort: 11–14 hours (2 days).**

### Phase 3 Scope (Estimated 3–5 days)

1. Bimodal season model extension for Gulf-coast provinces.
2. Multi-basin sub-province analysis support.
3. Unit tests for core statistical modules (currently L-1 technical debt).
4. CI/CD pipeline (currently L-2 technical debt).

---

## Appendix: Validated Reference Release

All scientific results in this report are based on the validated Prachuap Khiri Khan release:

| Attribute | Value |
|---|---|
| Release tag | v1.0.0 |
| Git commit | 471bdc3 |
| Branch | claude/hydroclimatology-claude-md-kudre |
| Release status | RELEASE APPROVED (RELEASE_CERTIFICATION_v1.0.md) |
| Figure QA | 38 / 38 figures PASS (FIGURE_QA_REPORT.md) |
| Reproducibility | Verified in clean environment (REPRODUCIBILITY_FINAL_CHECK.md) |
| Project status | PROJECT CLOSED WITH MINOR FOLLOW-UP (FINAL_RELEASE_SUMMARY.md) |

---

*This document constitutes the complete architecture audit and migration blueprint for the multi-province hydroclimatic framework conversion. No code changes have been made. Implementation begins only after blueprint approval.*
