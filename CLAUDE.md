# CLAUDE.md — Rainfall Trend Analysis

## Project Overview

**Title:** Rainfall Trend Analysis — Phetchaburi–Prachuap Khiri Khan River Basin, Western Thailand  
**Version:** v2.0 / v4 (scripts `rainfall_trend_analysis_v3.py` and `rainfall_trend_analysis_v4.py`)  
**Period:** 1981–2014 (daily rainfall)  
**Purpose:** Publication-ready hydroclimatological trend analysis targeting Q1 journal standards.  
**Target Output:** 8+ publication figures (PNG + PDF 600 DPI), 6-sheet Excel summary, Markdown research document, geographic spatial maps.

---

## 1. Project Structure

```
rainfall-trend-analysis/
├── rainfall_trend_analysis_v3.py   # Single-file analysis pipeline (legacy)
├── rainfall_trend_analysis_v4.py   # Modular pipeline (rta/ package + PW/TFPW/spatial)
├── rta/                            # Python package — hydroclimatological analysis modules
│   ├── __init__.py
│   ├── config.py                   # Shared constants (C, DPI, SAVE_PDF, Z_005, savefig)
│   ├── spatial.py                  # Coordinate loading & validation (load_coords, validate_coords)
│   ├── spatial_maps.py             # Top-level re-export of all spatial figure functions
│   ├── figures/
│   │   ├── spatial.py              # fig8_spatial_summary (v3 Fig 8 — index-based)
│   │   ├── spatial_maps.py         # True geographic spatial maps (5 public functions)
│   │   ├── acf_plots.py            # fig12_acf_diagnostics
│   │   └── ...                     # Other figure modules
│   ├── trend_tests/                # MK, MMK, PW-MK, TFPW-MK, Sen's slope
│   ├── pw.py                       # Prewhitening (Yue & Wang 2004)
│   ├── tfpw.py                     # Trend-Free Prewhitening (Yue et al. 2002)
│   ├── field_significance.py       # Walker (1914) + Livezey-Chen (1983) MC
│   └── checkpoint.py               # 6-step pickle checkpoint/resume system
├── station_coordinates.csv         # WGS84 station coordinates (128 stations)
├── prompt trend.pdf                # Project specification document (40 pages)
├── README.md                       # Minimal title/version note
├── LICENSE                         # MIT License
├── .gitignore                      # Python/standard dev ignores
└── CLAUDE.md                       # This file
```

**Data and outputs are co-located with the input CSV at runtime** — no dedicated `data/` or `output/` directories exist in the repository. All outputs are written to the same folder as the input CSV file.

---

## 2. Existing Workflow

The entire pipeline lives in `rainfall_trend_analysis_v3.py`. It is a single-file, top-to-bottom orchestrated workflow with no external configuration files or secondary scripts.

### Execution

```bash
python rainfall_trend_analysis_v3.py
```

The script prompts for a folder path (or falls back to `Path.cwd()`). It auto-discovers the daily rainfall CSV within that folder and runs the full pipeline.

### Workflow Steps (in execution order)

| Step | Section | Function(s) | Description |
|------|---------|-------------|-------------|
| 1 | §1 | `find_csv()`, `load_daily()`, `quality_control()` | CSV discovery, loading, QC |
| 2 | §2 | `aggregate_all()`, `descriptive_stats()` | Temporal aggregation + descriptive stats |
| 3 | §3 | `lag_k_autocorr()`, `all_lag_autocorr()`, `is_sig_autocorr()` | Autocorrelation assessment |
| 4 | §4 | `standard_mk()` | Standard Mann-Kendall test |
| 5 | §5 | `modified_mk()` | Modified Mann-Kendall (Hamed & Rao 1998) |
| 6 | §6 | `sens_slope()` | Sen's slope + 95% CI |
| 7 | §7 | `run_all()`, `build_comparison()` | Batch run all stations × scales; MK vs MMK table |
| 8 | §8–§15 | `fig1_*` … `fig8_*` | Generate 8 publication figures |
| 9 | §16 | `write_excel()` | Write 6-sheet Excel workbook |
| 10 | §17 | `write_summary_md()` | Write Markdown research summary |
| 11 | §18 | `main()` | Master orchestration |

---

## 3. Dependencies

### Python Standard Library
```
os, sys, math, warnings, textwrap
pathlib.Path
datetime.datetime
```

### Scientific Stack
| Package | Purpose |
|---------|---------|
| `numpy` | Array operations, statistical utilities |
| `pandas` | DataFrame handling, DatetimeIndex, groupby aggregation |
| `scipy.stats` | Statistical distributions (`norm`), descriptive stats |

### Visualization
| Package | Purpose |
|---------|---------|
| `matplotlib` | All figure generation (backend: `Agg`) |
| `matplotlib.gridspec` | Multi-panel figure layouts |
| `matplotlib.ticker` | Axis formatting |
| `matplotlib.patches`, `matplotlib.lines` | Legend handles |
| `matplotlib.colors`, `matplotlib.cm` | Colormaps for heatmaps |

### Excel Output
| Package | Purpose |
|---------|---------|
| `openpyxl` | Excel workbook creation with full cell styling |
| `openpyxl.styles` | `PatternFill`, `Font`, `Alignment`, `Border`, `Side` |
| `openpyxl.utils` | `get_column_letter` |

### No requirements.txt exists. Install via:
```bash
pip install numpy pandas scipy matplotlib openpyxl
```

---

## 4. Input / Output Files

### Input

| File | Format | Discovery |
|------|--------|-----------|
| Daily rainfall CSV | `.csv` | Auto-discovered: first CSV in target folder not prefixed with `Output_` |

#### CSV Format
- **Columns:** `YEAR`, `MONTH`, `DAY`, then one column per rain gauge station
- **Missing value flags:** `-99`, `-999`, `-9999`, `-9.99e+20`, `9.99e+20`, `1e+20` → converted to `NaN`
- **Station names** are taken directly from CSV column headers (beyond `YEAR`, `MONTH`, `DAY`)

### Output Files

All outputs are written to the **same folder as the input CSV**. The `<basename>` is the CSV filename without extension.

#### Figures (PNG + PDF)
```
Output_TrendV2_<basename>_Fig1_AnnualTimeSeries.png/.pdf
Output_TrendV2_<basename>_Fig2_WetDryTimeSeries.png/.pdf
Output_TrendV2_<basename>_Fig3_SenSlope_AllScales.png/.pdf
Output_TrendV2_<basename>_Fig4_MK_vs_MMK_Comparison.png/.pdf
Output_TrendV2_<basename>_Fig5_Significance_Heatmap.png/.pdf
Output_TrendV2_<basename>_Fig6_Autocorrelation.png/.pdf
Output_TrendV2_<basename>_Fig7_MonthlyClimatology.png/.pdf
Output_TrendV2_<basename>_Fig8_SpatialTrend_Summary.png/.pdf
```

#### Tables and Documents
```
Output_TrendV2_<basename>_Results.xlsx       # 6-sheet workbook
Output_TrendV2_<basename>_Research_Summary.md  # Paper-ready Markdown
```

---

## 5. Figure Pipeline

### Resolution and Format
- **DPI:** 600 (publication standard)
- **Formats:** PNG (primary) + PDF (when `SAVE_PDF = True`, default)
- **Font:** Times New Roman / DejaVu Serif (serif), 12pt base
- **Style:** No top/right spines; grid on (dashed, α=0.40); colorblind-safe palette

### Color Palette
```python
C = {
    'annual':   "#37474F",   'annual_lt': "#B0BEC5",   # Dark/light slate
    'wet':      "#1565C0",   'wet_lt':    "#90CAF9",   # Dark/light blue
    'dry':      "#E65100",   'dry_lt':    "#FFCC80",   # Dark/light orange
    'inc':      "#1B5E20",   'inc_lt':    "#A5D6A7",   # Dark/light green (increasing)
    'dec':      "#B71C1C",   'dec_lt':    "#EF9A9A",   # Dark/light red (decreasing)
    'ns_col':   "#78909C",   'ns_lt':     "#CFD8DC",   # Grey (not significant)
    'mk_std':   "#6A1B9A",                              # Purple (Standard MK)
    'mk_mod':   "#0277BD",                              # Blue (Modified MK)
    'gold':     "#F9A825",   'grey':      "#546E7A",
}
```

### Figure Inventory

| Figure | Function | Line | Type | Key Content |
|--------|----------|------|------|-------------|
| Fig 1 | `fig1_annual_ts()` | 662 | Time series grid | Annual rainfall per station with MMK trend line and 95% CI shading |
| Fig 2 | `fig2_wetdry_ts()` | 745 | 4-panel time series | (a) Regional wet-season, (b) Regional dry-season, (c–d) Per-station wet/dry slopes |
| Fig 3 | `fig3_sens_all()` | 875 | Bar chart (3 rows) | Sen's slope (mm/yr) for Annual / Wet / Dry; error bars = 95% CI; color = trend direction |
| Fig 4 | `fig4_mk_vs_mmk()` | 959 | 4-panel comparison | (a) Z-statistic scatter MK vs MMK, (b) p-value scatter, (c) ΔZ bar chart, (d) Agreement heatmap |
| Fig 5 | `fig5_significance_heatmap()` | 1105 | Dual heatmap | Z-statistic matrix (stations × temporal scales) for Standard MK and Modified MK side-by-side |
| Fig 6 | `fig6_autocorrelation()` | 1180 | Bars + ACF line | (a) Lag-1 autocorrelation per station with significance threshold; (b) ACF of regional mean |
| Fig 7 | `fig7_monthly_climatology()` | 1268 | Bar charts | Monthly mean rainfall per station + regional mean climatology |
| Fig 8 | `fig8_spatial_summary()` | 1349 | 4-panel summary | (a) Sen's slope vs Z bubble plot, (b) Trend count summary, (c) ΔSlope (MK vs MMK), (d) Slope heatmap |

---

## 6. Statistical Workflow

### 6.1 Quality Control (`quality_control()`, line 218)
- Replaces all missing-value flags with `NaN`
- Detects extreme outliers: values > Q3 + 3×IQR per station
- Fills gaps ≤ 5 consecutive days via linear interpolation
- Reports: % missing, outlier count, filled count per station

### 6.2 Temporal Aggregation (`aggregate_all()`, line 251)
| Scale | Period | Completeness Threshold |
|-------|--------|------------------------|
| Annual | Jan–Dec (calendar year) | ≥ 80% of days |
| Wet Season | May–Oct | ≥ 80% of days |
| Dry Season | Nov–Apr (hydrological year) | ≥ 80% of days |
| Monthly | Each calendar month | ≥ 60% of days |

**Dry-season hydrological year handling:** November and December of year *Y* are shifted to year *Y+1* so that the Nov–Apr block is labeled as a single hydrological year.

### 6.3 Autocorrelation Assessment (`§3`, line 315)
- `lag_k_autocorr(series, k)` — Pearson lag-k correlation
- `all_lag_autocorr(series, max_lag)` — ACF vector for lags 1 … max_lag
- `is_sig_autocorr(r1, n)` — two-tailed test: |r₁| > Z₀.₀₂₅ / √n

### 6.4 Standard Mann-Kendall Test (`standard_mk()`, line 382)
- Computes S statistic via vectorized sign comparison (`_mk_s_fast()`, line 362)
- Applies tie correction to Var(S) (`mk_variance_ties()`, line 376)
- Returns: S, Var(S), Z, τ (Kendall's tau), p-value, trend direction, Sen's slope β, 95% CI

### 6.5 Modified Mann-Kendall — Hamed & Rao 1998 (`modified_mk()`, line 430)
- Computes autocorrelation on **ranked** series
- Retains only statistically significant ρ_k values
- Effective sample size: n\* = n / [1 + (2/n) × Σ (n−k) ρ_k]
- Adjusted variance: Var\*(S) = Var(S) × (n / n\*)
- Returns all MK fields plus Var\*(S), n\*, inflation factor

### 6.6 Sen's Slope Estimator (`sens_slope()`, line 505)
- Non-parametric slope: median of all pairwise (y_j − y_i)/(t_j − t_i)
- 95% CI via Gilbert (1987) rank-based method
- Intercept anchored at series median
- Returns: β (slope mm/yr), CI_lo, CI_hi, intercept

### 6.7 Batch Execution (`run_all()`, line 549)
- Loops over all stations × {Annual, Wet, Dry}
- Runs both MK and MMK for each combination
- Skips series with N < `MIN_N` (= 10 years)
- Returns consolidated results DataFrame

### 6.8 MK vs MMK Comparison (`build_comparison()`, line 602)
- Side-by-side table: MK Z, MMK Z, MK p, MMK p, ΔZ = Z_MMK − Z_MK, agreement flag
- Agreement defined as identical trend direction AND shared significance category

### 6.9 Field Significance
- Significance markers: `**` (p < 0.01), `*` (p < 0.05), `ns` (not significant)
- Critical Z values: Z₀.₀₅ = 1.9600, Z₀.₀₁ = 2.5758 (two-tailed)
- Both methods reported in all tables to allow method comparison

### 6.10 Statistical References
| Method | Reference |
|--------|-----------|
| Standard Mann-Kendall | Mann (1945) *Econometrica* 13:245–259; Kendall (1975) *Rank Correlation Methods* |
| Modified MK (autocorr. correction) | Hamed & Rao (1998) *J. Hydrol.* 204:182–196 |
| Sen's slope estimator | Sen (1968) *JASA* 63:1379–1389; Gilbert (1987) |
| Prewhitening approach | Yue & Wang (2004) *Water Resour. Res.* 40:W08307 |
| MK vs PW comparison | Önöz & Bayazit (2003) *Hydrol. Sci. J.* 48:25–34 |

---

## 7. Naming Conventions

### Script Sections
Sections are delimited with banner comments `# ╔══╗ / ║ §N TITLE ║ / ╚══╝`.

### Functions
- Snake_case: `load_daily`, `quality_control`, `standard_mk`, `modified_mk`, `sens_slope`
- Private helpers prefixed with `_`: `_mk_s_fast`, `_sens_line`, `_sig_label`, `_col_trend`
- Figure functions: `fig{N}_{description}()` (e.g., `fig1_annual_ts`, `fig5_significance_heatmap`)
- Excel helpers: short lowercase (`tb`, `xfill`, `xsc`, `mxsc`, `cw`, `rh`)

### Output Files
Pattern: `Output_TrendV2_<csv_basename>_<descriptor>.<ext>`

| Token | Example | Meaning |
|-------|---------|---------|
| `Output_TrendV2_` | fixed prefix | Version identifier |
| `<csv_basename>` | `rainfall_data` | Input CSV filename without extension |
| `Fig1_AnnualTimeSeries` | figure descriptor | Figure number + content tag |
| `.png` / `.pdf` | extension | PNG always; PDF when `SAVE_PDF=True` |
| `_Results.xlsx` | Excel workbook | 6-sheet results file |
| `_Research_Summary.md` | Markdown | Paper-ready summary document |

### Station Labels
- Full names from CSV column headers
- Short codes generated as `S1`, `S2`, … `SN` via `short_labels()` (line 2101) for compact plot axes

### Temporal Scale Labels
| Code | Period |
|------|--------|
| `annual` | January–December |
| `wet` | May–October |
| `dry` | November–April (hydrological year) |
| `monthly` | Calendar month aggregates |

### Constants
- ALL_CAPS: `VERSION`, `WET_THR`, `WET_MONTHS`, `DRY_MONTHS`, `MIN_N`, `ALPHA_005`, `ALPHA_001`, `Z_005`, `Z_001`, `DPI`, `SAVE_PDF`
- Color dict: `C` (single letter, accessed as `C['annual']`, `C['inc']`, etc.)
- Excel color dict: `XC` (short keys like `'title'`, `'hdr'`, `'sig05'`)

---

## 8. Execution Order

### Full Pipeline (invoked by `main()`, line 2105)

```
python rainfall_trend_analysis_v3.py
│
├── 1. Prompt for input folder
├── 2. find_csv()            — locate daily rainfall CSV
├── 3. load_daily()          — load CSV → DatetimeIndex DataFrame
├── 4. quality_control()     — missing flags → NaN, IQR outliers, interpolation
│
├── 5. aggregate_all()       — annual / wet / dry / monthly totals
├── 6. descriptive_stats()   — mean, std, CV, skewness, wet-days
│
├── 7. all_lag_autocorr()    — ACF for each station × scale
├── 8. is_sig_autocorr()     — lag-1 significance flags
│
├── 9. run_all()             — loops stations × {annual, wet, dry}:
│       ├── standard_mk()   — MK test (no AC correction)
│       ├── modified_mk()   — MMK Hamed & Rao 1998
│       └── sens_slope()    — non-parametric slope + 95% CI
│
├── 10. build_comparison()   — MK vs MMK side-by-side table
│
├── 11. fig1_annual_ts()     → Fig1_AnnualTimeSeries.png/.pdf
├── 12. fig2_wetdry_ts()     → Fig2_WetDryTimeSeries.png/.pdf
├── 13. fig3_sens_all()      → Fig3_SenSlope_AllScales.png/.pdf
├── 14. fig4_mk_vs_mmk()     → Fig4_MK_vs_MMK_Comparison.png/.pdf
├── 15. fig5_significance_heatmap() → Fig5_Significance_Heatmap.png/.pdf
├── 16. fig6_autocorrelation()      → Fig6_Autocorrelation.png/.pdf
├── 17. fig7_monthly_climatology()  → Fig7_MonthlyClimatology.png/.pdf
├── 18. fig8_spatial_summary()      → Fig8_SpatialTrend_Summary.png/.pdf
│
├── 19. write_excel()        → Results.xlsx (6 sheets)
└── 20. write_summary_md()   → Research_Summary.md
```

### Excel Sheet Order
| Sheet | Name | Content |
|-------|------|---------|
| 1 | Standard MK | MK baseline: S, Var(S), Z, τ, p, Trend, ρ₁ per station × scale |
| 2 | Modified MK (H&R98) | MMK: adds Var\*(S), n\*, inflation factor |
| 3 | MK vs MMK Comparison | Side-by-side: ΔZ, Δp, Agreement flag |
| 4 | Sen's Slope | β, CI_lo, CI_hi, Z, p, Trend per station × scale × method |
| 5 | Descriptive Statistics | N, Mean, Median, Max, Min, Std, CV, Wet-days, Skewness per station |
| 6 | Methods & References | Method name, citation, description (3-column reference table) |

---

## 9. Key Constants Reference

| Constant | Value | Purpose |
|----------|-------|---------|
| `VERSION` | `"2.0"` | Script version tag |
| `WET_THR` | `1.0` mm/day | WMO wet-day threshold |
| `WET_MONTHS` | `[5,6,7,8,9,10]` | Wet season months (May–Oct) |
| `DRY_MONTHS` | `[11,12,1,2,3,4]` | Dry season months (Nov–Apr) |
| `MIN_N` | `10` | Minimum years for MK test |
| `ALPHA_005` | `0.05` | Primary significance level |
| `ALPHA_001` | `0.01` | Secondary significance level |
| `Z_005` | `1.9600` | Two-tailed critical Z at α=0.05 |
| `Z_001` | `2.5758` | Two-tailed critical Z at α=0.01 |
| `DPI` | `600` | Figure output resolution |
| `SAVE_PDF` | `True` | Also save PDF alongside PNG |
| `MISS_FLAGS` | `[-99,-999,-9999,…]` | Missing-value sentinel values |

---

## 10. Spatial Analysis Modules

### 10.1 Coordinate File

| File | Format | Discovery |
|------|--------|-----------|
| `station_coordinates.csv` | `.csv` | Auto-detected by `load_coords()` via `*coordinates*.csv` glob |

**Columns:** `Station`, `Lat`, `Lon`, `Altitude`  
**CRS:** WGS84 assumed (EPSG:4326) — no explicit CRS stored in file  
**Coverage:** 128 stations total; all 12 rainfall stations (500001–500301) present  
**Coordinate range:** Lat 11.18–12.59°N, Lon 99.55–99.96°E (Prachuap Khiri Khan basin)

### 10.2 `rta/spatial.py` — Coordinate Loading

| Function | Description |
|----------|-------------|
| `load_coords(folder)` | Auto-detect and load station coordinates CSV; returns `{station_id: (lat, lon)}` |
| `validate_coords(coords, stns)` | Report matched/missing/extra stations; returns coverage fraction |
| `coords_to_df(coords)` | Convert coords dict to tidy DataFrame with columns (Station, Lat, Lon) |

**Key implementation detail:** `pd.read_csv(..., dtype=str)` is used to prevent pandas from reading integer station IDs as float64, which would cause key mismatches (e.g., `'500001.0'` vs `'500001'`).

### 10.3 `rta/figures/spatial_maps.py` — Geographic Figure Functions

| Function | Output Figure | Description |
|----------|--------------|-------------|
| `fig_station_distribution(coords, stns, smap, period, out_dir, prefix, alt_dict=None)` | `{prefix}_Fig_SpatialStation.png` | Single-panel geographic station map with compass, scale bar, station labels; optional altitude colouring via `cm.terrain` |
| `fig_spatial_methods(trend_df, stns, smap, coords, period, out_dir, prefix)` | `{prefix}_Fig_SpatialMethods.png` | 4×3 grid: 4 methods (MK/MMK/PW/TFPW) × 3 scales (Annual/Wet/Dry); geographic bubble maps; size ∝ \|Sen's slope\| |
| `fig_spatial_field_sig(trend_df, field_sig_df, stns, smap, coords, period, out_dir, prefix)` | `{prefix}_Fig_SpatialFieldSig.png` | 3 geographic \|Z\| magnitude panels (MMK, per scale) + Walker/LC-MC p-value bar chart |
| `fig_spatial_full(trend_df, stns, smap, coords, field_sig_df, period, out_dir, prefix, alt_dict=None)` | `{prefix}_Fig_SpatialFull.png` | Comprehensive 7-panel overview: (a) stations, (b–e) annual 4 methods, (f) Sen's slope heatcolour, (g) field significance |
| `fig14_spatial_maps(trend_df, stns, smap, coords, period, out_dir, prefix)` | `{prefix}_Fig14_SpatialMaps.png` | Backward-compatible 3-panel MMK map (Annual/Wet/Dry); uses real coords when available, index-based fallback otherwise |

**Bubble encoding:** Size ∝ \|Sen's slope\|; colour = trend direction (green = increasing p<0.05, red = decreasing p<0.05, grey = not significant).

**Fallback behaviour:** All functions silently skip or fall back to index-based layout when `coords=None` or no stations match the coordinate dictionary.

### 10.4 Previously Missing Methods — Now Implemented

| Method | Status | Module | Reference |
|--------|--------|--------|-----------|
| Prewhitening (PW) correction | **Implemented** | `rta/pw.py` | Yue & Wang (2004) |
| TFPW (Trend-Free Prewhitening) | **Implemented** | `rta/tfpw.py` | Yue et al. (2002) |
| Field significance (Walker + LC-MC) | **Implemented** | `rta/field_significance.py` | Walker (1914); Livezey & Chen (1983) |
| Geographic spatial trend maps | **Implemented** | `rta/figures/spatial_maps.py` | — |
| Taylor diagram | Not implemented | — | Multi-station model comparison |

---

## 11. Development Notes

- The script uses `matplotlib.use("Agg")` — no display is needed; all figures are saved to disk.
- `warnings.filterwarnings("ignore")` suppresses scipy/numpy runtime warnings globally.
- `SAVE_PDF = True` at the top of the script controls whether PDFs are generated alongside PNGs. Set to `False` to save disk space during development.
- The dry-season aggregation shifts November/December of year *Y* to year *Y+1* — this is intentional and implements the hydrological year convention for tropical monsoon systems.
- Autocorrelation correction in MMK uses only **statistically significant** lag-k correlations (not all lags), following Hamed & Rao (1998) strictly.
- Excel styling constants (`THIN`, `MED`, `XC`) and helper functions (`tb`, `xfill`, `xsc`, `mxsc`, `cw`, `rh`) are defined globally (lines 143–179) and used throughout `write_excel()`.
- **Spatial coordinate loading:** `load_coords()` uses `pd.read_csv(..., dtype=str)` to prevent pandas from interpreting integer station IDs (e.g., `500001`) as `float64`, which would produce `'500001.0'` keys that fail dictionary lookups against string station names.
- **`v4` checkpoint system:** 6 steps saved as pickle files in `checkpoints/` subdirectory. On resume, the pipeline detects the highest completed step and jumps directly to figures, skipping all statistical computation.
- **Spatial figures are only generated when coordinate data is available** (`if coords:` guard in both v3 and v4 scripts). If `station_coordinates.csv` is absent from the input folder, spatial figures are silently skipped; all other figures and outputs are unaffected.

---

## 12. Mandatory Scientific Standards

Rules derived from full-codebase audit (2026-06-11). These apply to all future code generation, extensions, and new repositories built on this project. Rules that duplicate §6–§10 are omitted; only additions and corrections are listed.

---

### 12.1 Mann-Kendall Family

| Test | Mandatory rule |
|------|---------------|
| MMK (H&R98) | Inflation factor must be floored: `n/n* = max(1.0, 1+(2/n)Σ(n−k)ρ_k)`. Negative ρ_k values must never reduce Var*(S) below Var(S). |
| PW-MK | Z/p/tau from prewhitened series `y = x[t+1] − ρ₁x[t]` only. Sen's slope **must** come from original series `x`. After `res = standard_mk(y)`, replace `res["slope_Q/lo/hi"]` with `sens_slope(x)` before returning. |
| TFPW-MK | Slope from trend-restored `z` is acceptable (bias is one removed observation). Do not replace with `sens_slope(x)` for TFPW. |
| All prewhitening | After constructing residual/restored series (length n−1), re-check `len >= MIN_N`. Return null result if below threshold; do not proceed with n < 10. |
| Four-method output | Any table comparing MK methods must include all four: Standard MK, MMK, PW-MK, TFPW-MK, with slope and ΔSlope columns. |

### 12.2 Sen's Slope

- CI bounds (Gilbert 1987): `lo_r = int((N − C_α) / 2)`, `hi_r = int((N + C_α) / 2)` — use `int()` (floor), not `round()`.
- For PW-MK: the slope override `sens_slope(x)` applies to `slope_Q`, `slope_lo`, and `slope_hi` — all three, not slope_Q alone.
- Intercept: anchored at `median(x) − slope_Q × median(t)`. Never compute intercept from prewhitened series.

### 12.3 Serial Autocorrelation

- Significance threshold for field significance station eligibility: `len(series) >= MIN_N` (= 10). Using `len >= 4` inflates the Walker test denominator and biases the test toward non-significance.
- Livezey-Chen MC for MMK: the null distribution (permuted `standard_mk` fractions) is reusable for both MK and MMK because permutation destroys autocorrelation. The **observed fraction** for MMK must be `n_sig_mmk / n_stn` — do not recompute it inside the LC function using `standard_mk`.
- MMK ranked-series ACF: use `scipy.stats.rankdata` before computing autocorrelations. Raw series AC must not be substituted.

### 12.4 Completeness and Data Quality

- 80% gate applies uniformly to annual, wet, and dry scales. Do not use 60% for seasonal scales.
- Wet-days/yr: numerator (wet-day count) and denominator (valid years) must use the same year-filtered record. Counting wet days from all daily records against a valid-year annual count produces a mismatched ratio.
- Extreme outliers (> Q3 + 3×IQR): must be either removed with justification, or retained with explicit justification in the methods section. Flagging without action is not acceptable for Q1 publication.
- Report minimum valid-year count per station per scale in the descriptive statistics table.

### 12.5 Future-Period Validation (CMIP6)

- Validate that each CMIP6 model's loaded time series covers the full configured period. Warn and exclude models with partial coverage; do not silently include them.
- For projected windows (e.g. 2021–2050, 2071–2100): run Mann-Kendall and Sen's slope within each window per model and report Sen's slope (mm/yr/decade). Period-mean change% alone is insufficient for Q1 hydroclimatology.
- Change% must be computed per-model first, then aggregated to MME statistics (mean, P25, P75 of per-model values). Computing change% on the MME mean conflates inter-model spread with the change signal.

### 12.6 CMIP6 Calendar Handling

| Calendar | Days/yr | Required action |
|----------|---------|-----------------|
| `standard` / `proleptic_gregorian` | 365.25 | None |
| `noleap` / `365_day` | 365 | Drop Feb 29 from observed series before comparison |
| `360_day` | 360 | Do not use `pd.to_datetime()` on raw dates; use `xarray`/`cftime` or convert before CSV generation |

Manuscript §2 Data Pre-Processing must list every model, its calendar type, and the exact harmonisation step applied. This is a standard CMIP6 protocol requirement (Eyring et al. 2016) and a journal reproducibility requirement.

### 12.7 Bias Correction Documentation

No CMIP6 impact analysis is publishable without all of the following in the manuscript:

| Required element | Notes |
|-----------------|-------|
| Method name + citation | e.g. QDM (Cannon et al. 2015 *J. Climate* 28:6938) |
| Reference period | Must match observed baseline (e.g. 1981–2014) |
| Software + version | e.g. `xclim` v0.45 |
| Archived corrected data | DOI repository or deterministic generation script in the repo |

KGE/NSE/PBIAS captions must state whether the metrics assess raw or bias-corrected model skill — these are different quantities and must not be conflated.

### 12.8 Ensemble Methodology

- Equal model weighting: state this explicitly in the methods section. Acknowledge model family redundancy (e.g. multiple ACCESS or CESM variants) is not corrected. Cite Knutti et al. (2017) if relevant.
- NaN-safe percentiles: always use `float(np.percentile(s.dropna(), q)) if s.notna().any() else np.nan` in `groupby().agg()`. Bare `np.percentile(s, q)` on a pandas Series with NaN is NumPy-version-dependent.
- MME statistics to report per station × season × year: mean, median, P25, P75, n_models. All five must be NaN-safe.

### 12.9 GIS Figure Standards

- Every geographic map must include: north arrow, scale bar, coordinate tick labels or graticule lines.
- Anomaly time-series figures: compute baseline climatology exclusively over the configured baseline period (e.g. 1981–2014). Do not include future projection data in the baseline mean computation.
- Bubble maps: size ∝ |Sen's slope|; colour = green (increasing, p < 0.05), red (decreasing, p < 0.05), grey (not significant). This encoding must be consistent across all spatial figures in a study.
- CRS: WGS84 (EPSG:4326) throughout. Station IDs: always load with `dtype=str` to prevent `int → float64` cast.

### 12.10 Publication-Ready Tables

**Field significance table — mandatory columns:**

| Column | Derives from |
|--------|-------------|
| `Walker_p_MK`, `Walker_sig_MK` | Standard MK |
| `Walker_p_MMK`, `Walker_sig_MMK` | Modified MK |
| `LC_p_MK`, `LC_sig_MK` | Standard MK |
| `LC_p_MMK`, `LC_sig_MMK` | Modified MK |

Omitting any MMK field significance column is a silent output gap. Reviewers will query it.

**Validation metrics table:**
- KGE/NSE/PBIAS reported for Raw MME and BC-MME on identical common-year samples (three-way intersection: obs ∩ raw ∩ bc).
- KGE uses sample std (ddof=1) per Gupta et al. (2009). If population std (ddof=0) is used instead, state this explicitly in the caption.
- Do not report std = 0.0 for stations with n = 1 valid year; use NaN.

### 12.11 Reproducibility Requirements

| Requirement | Mandatory for Q1 |
|-------------|-----------------|
| `requirements.txt` with pinned versions | Yes — create before submission |
| Random seed documented | Yes — `seed=42` for LC Monte Carlo |
| CMIP6 calendar handling documented in §2 | Yes |
| Bias correction method, period, software in §2 | Yes |
| Bias-corrected input data archived (DOI) or generation script committed | Yes |
| `run_id` or `config_version` field in `config.yaml` | Yes — log to every output file |
| Python version pinned in README | ✓ already present |
| Checkpoint/resume system | ✓ already present |

### 12.12 Final Release Checklist

Before any submission or public release, all boxes must be checked:

**Statistical correctness**
- [ ] PW-MK: `slope_Q/lo/hi` computed from original series `x`, not prewhitened `y`
- [ ] MMK: inflation factor floored at `n/n* ≥ 1.0`
- [ ] Field significance table: all eight columns present (Walker + LC × MK + MMK)
- [ ] Field significance station filter: `len >= MIN_N` (= 10), not 4
- [ ] Post-prewhitening MIN_N re-check in `pw_mk()` before calling `standard_mk(y)`
- [ ] Sen's slope CI: `int()` (floor) for `hi_r`, not `round()`

**Data quality**
- [ ] 80% completeness gate applied uniformly to annual, wet, dry scales
- [ ] Outlier treatment explicitly justified in methods (not just flagged)
- [ ] Wet-days/yr numerator and denominator from same year-filtered record

**CMIP6 (if applicable)**
- [ ] Calendar type documented for every model in §2
- [ ] 360_day models handled before `pd.to_datetime()`
- [ ] Bias correction: method, period, software, and data archive all cited in §2
- [ ] Change% computed per-model before MME aggregation
- [ ] NaN-safe percentile functions in `build_mme()`
- [ ] Each model's series validated to cover full configured period

**Figures**
- [ ] 600 DPI, serif font, no top/right spines
- [ ] All maps: north arrow, scale bar, WGS84, coordinate labels
- [ ] Anomaly baseline computed over baseline period only (not full series)

**Reproducibility**
- [ ] `requirements.txt` with pinned versions present
- [ ] `run_id` or `config_version` in `config.yaml` and logged to outputs
- [ ] Random seed (42) documented
- [ ] Bias-corrected input data archived or generation script committed
