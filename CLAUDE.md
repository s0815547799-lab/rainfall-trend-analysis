# CLAUDE.md — Rainfall Trend Analysis

## Project Overview

**Title:** Rainfall Trend Analysis — Phetchaburi–Prachuap Khiri Khan River Basin, Western Thailand  
**Version:** v2.0 (script `rainfall_trend_analysis_v3.py`)  
**Period:** 1981–2014 (daily rainfall)  
**Purpose:** Publication-ready hydroclimatological trend analysis targeting Q1 journal standards.  
**Target Output:** 8 publication figures (PNG + TIFF 600 Dpi), 6-sheet Excel summary, Markdown research document.

---

## 1. Project Structure

```
rainfall-trend-analysis/
├── rainfall_trend_analysis_v3.py   # Single-file analysis pipeline (2,304 lines)
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

## 10. Missing Planned Methods (per specification)

The `prompt trend.pdf` specification references additional methods not yet implemented in `v3`. These are documented here for future development:

| Method | Status | Notes |
|--------|--------|-------|
| Prewhitening (PW) correction | Not implemented | Yue & Wang (2004) |
| TFPW (Trend-Free Prewhitening) correction | Not implemented | Yue et al. (2002) |
| Taylor diagram | Not implemented | Multi-station model comparison |
| Spatial trend maps | Not implemented | Requires coordinate data for stations |

---

## 11. Development Notes

- The script uses `matplotlib.use("Agg")` — no display is needed; all figures are saved to disk.
- `warnings.filterwarnings("ignore")` suppresses scipy/numpy runtime warnings globally.
- `SAVE_PDF = True` at the top of the script controls whether PDFs are generated alongside PNGs. Set to `False` to save disk space during development.
- The dry-season aggregation shifts November/December of year *Y* to year *Y+1* — this is intentional and implements the hydrological year convention for tropical monsoon systems.
- Autocorrelation correction in MMK uses only **statistically significant** lag-k correlations (not all lags), following Hamed & Rao (1998) strictly.
- Excel styling constants (`THIN`, `MED`, `XC`) and helper functions (`tb`, `xfill`, `xsc`, `mxsc`, `cw`, `rh`) are defined globally (lines 143–179) and used throughout `write_excel()`.
