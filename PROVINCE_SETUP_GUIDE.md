# Province Setup Guide — Hydroclimatic Trend Analysis Framework

**Framework version:** 1.0

---

## Overview

This guide provides step-by-step instructions for configuring and running the pipeline for a new Thai province, or any monsoon-climate region. The Prachuap Khiri Khan dataset (1981–2014, 12 stations) is the validated reference configuration. New provinces follow the same process.

**Primary pipeline:** `rainfall_trend_analysis_v4.py`  
**Post-processing (optional):** `generate_trend_comparison_analysis.py`, `generate_q1_maps.py`

---

## Step 1: Prepare Rainfall Data

### Required format

The rainfall CSV must follow this column layout:

| Column | Type | Notes |
|--------|------|-------|
| `YEAR` | Integer (4-digit) | Calendar year |
| `MONTH` | Integer (1–12) | Calendar month |
| `DAY` | Integer (1–31) | Calendar day |
| `[Station_1]` … `[Station_N]` | Float | Daily rainfall in mm; missing = sentinel value |

One row per day. All station columns must appear to the right of `DAY`. Column headers become the station names used in all figures, tables, and filenames.

**Example header row:**

```
YEAR,MONTH,DAY,500001,500002,500003,500004,500005,500006
```

### Missing value handling

The pipeline automatically replaces these sentinel values with `NaN` during quality control:

| Sentinel | Decimal equivalent |
|----------|--------------------|
| `-99` | −99 |
| `-999` | −999 |
| `-9999` | −9 999 |
| `-9.99e+20` | −9.99 × 10²⁰ |
| `9.99e+20` | +9.99 × 10²⁰ |
| `1e+20` | +1 × 10²⁰ |

If your data uses different missing value codes, add them to the `MISS_FLAGS` constant in `rta/config.py` (line 38) until the configuration file is implemented.

### Minimum data requirements

| Requirement | Value | Reason |
|-------------|-------|--------|
| Minimum complete years per station | 10 (`MIN_N`) | Mann-Kendall test is unreliable below this threshold |
| Day-completeness per year (annual) | ≥ 80% | Annual aggregate computed only if met |
| Day-completeness per season (wet/dry) | ≥ 80% | Seasonal aggregate computed only if met |
| Day-completeness per month (monthly) | ≥ 60% | Monthly aggregate computed only if met |
| Minimum station count | 2 | Field significance requires at least 2 stations |

### Recommended practices

- Use at least 20 years of data for meaningful trend detection. Power of the Mann-Kendall test at α = 0.05 is low for N < 20.
- Maintain a consistent station network throughout the analysis period. Adding or removing stations mid-period inflates spatial variance.
- Apply institutional quality control (duplicate checks, physical-plausibility screening) to the raw data before running the pipeline. The built-in QC (IQR outlier flagging, short-gap interpolation) is a supplementary safeguard, not a substitute.
- Store the raw CSV with a descriptive filename that encodes the province and period, e.g. `Observed_Rain_daily_198001_202012_ChiangMai.csv`. The output filenames inherit the CSV basename.

---

## Step 2: Prepare Station Coordinates

### Required format

A CSV file with the following columns:

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| `Station` | String | Yes | Must match column headers in rainfall CSV **exactly** |
| `Lat` | Float | Yes | Decimal degrees, WGS84 |
| `Lon` | Float | Yes | Decimal degrees, WGS84 |
| `Altitude` | Float | No | Metres above sea level; used for terrain colouring in `fig_station_distribution` |

### File naming

Name the file `station_coordinates.csv` or any name matching `*coord*.csv` or `*station*.csv`. The coordinate loader (`rta/spatial.py: load_coords()`) auto-discovers the file by glob pattern within the input folder. Only the first match is used; if multiple matches exist, name the file explicitly.

### Column name tolerance

The coordinate loader accepts common variations:

| Accepted names | Canonical column |
|----------------|-----------------|
| `Lat`, `lat`, `Latitude`, `latitude` | Latitude |
| `Lon`, `lon`, `Long`, `long`, `Longitude`, `longitude` | Longitude |

### Important: station ID format

Station IDs in the coordinates file are read as **strings** (`pd.read_csv(..., dtype=str)`) to prevent pandas from converting integer IDs (e.g., `500001`) to float64 (`500001.0`), which would cause key mismatches during coordinate lookup. Ensure there are no leading/trailing spaces in station name columns.

---

## Step 3: Optional — Prepare Province Shapefile

### When is it needed?

The province shapefile is only required for `generate_q1_maps.py` (Q1-quality geographic publication maps). The primary pipeline (`rainfall_trend_analysis_v4.py`) generates spatial figures using a fallback index-based layout if no shapefile is found; all other figures and outputs are unaffected.

### Format

| Requirement | Detail |
|-------------|--------|
| Format | ESRI Shapefile (`.shp` + `.dbf` + `.shx` + `.prj` must all be present) |
| Geometry type | Polygon or MultiPolygon |
| CRS | WGS84 (EPSG:4326) recommended; projected CRS is also accepted |
| Coordinate precision | At least 4 decimal places for a 10 km positional accuracy |

### Sources for Thai province boundaries

| Source | URL / Notes |
|--------|-------------|
| Department of Provincial Administration (DOPA) | Official Thai government boundaries |
| GADM | `gadm.org` — download Thailand ADM1 layer; select the desired province polygon |
| OpenStreetMap / Geofabrik | `download.geofabrik.de/asia/thailand.html` — extract province boundary from the admin boundary layer |

The reference shapefile for Prachuap Khiri Khan is included in the repository: `30_amarea_prachuap_khiri_khan.shp` (with accompanying `.dbf`, `.prj`, `.shx`).

---

## Step 4: Organise Your Input Folder

Place all input files in a single directory. The pipeline writes all outputs to the same directory.

**Recommended folder structure:**

```
/data/chiang_mai/
├── Observed_Rain_daily_198001_202012_ChiangMai.csv   # Rainfall data (required)
├── station_coordinates_cm.csv                         # Coordinates (optional, enables spatial figures)
└── 50_chiang_mai_province.shp                        # Shapefile (optional, enables Q1 maps)
    50_chiang_mai_province.dbf
    50_chiang_mai_province.shx
    50_chiang_mai_province.prj
```

No subdirectory structure is required or expected. The pipeline will create a `checkpoints/` subdirectory automatically for the v4 checkpoint/resume system.

---

## Step 5: Run the Primary Pipeline

```bash
python3 rainfall_trend_analysis_v4.py /data/chiang_mai/
```

If no path is supplied, the pipeline prompts for one interactively, or falls back to the current working directory.

### What happens at each step

The pipeline executes the following steps in order, printing progress to stdout:

| Step | Action | Console section |
|------|--------|-----------------|
| 1 | Locate rainfall CSV by glob | `[Step 1] Loading data` |
| 2 | Load daily data into DatetimeIndex DataFrame | |
| 3 | Quality control: replace missing flags, flag IQR outliers, interpolate gaps ≤ 5 days | `[Step 1] QC report` |
| 4 | Temporal aggregation: annual / wet / dry / monthly totals | `[Step 2] Aggregation` |
| 5 | Descriptive statistics per station | |
| 6 | Autocorrelation assessment (lag-1 significance) | `[Step 3] Autocorrelation` |
| 7 | Batch Mann-Kendall and Modified MK (Hamed & Rao 1998) for all stations × scales | `[Step 4] MK tests` |
| 8 | Prewhitening (PW) and Trend-Free Prewhitening (TFPW) MK | `[Step 5] PW/TFPW` |
| 9 | Field significance: Walker (1914) and Livezey-Chen (1983) Monte Carlo | `[Step 6] Field significance` |
| 10 | Generate all figures (Fig01–Fig14 + spatial figures) | `[Figures]` |
| 11 | Write Excel workbook (9 sheets) | `[Excel]` |
| 12 | Write Markdown research summary | `[Markdown]` |

### Expected console output (abbreviated)

```
=== Hydroclimatic Trend Analysis v4.0 ===
Input folder : /data/chiang_mai/
CSV found    : Observed_Rain_daily_198001_202012_ChiangMai.csv
Stations     : 20
Period       : 1980–2020 (41 years)

[Step 1] Loading and QC ...
    Missing: 0.3%   Outliers: 12   Filled: 8
[Step 2] Aggregation ...
[Step 3] Autocorrelation ...
[Step 4] MK / MMK tests ...
[Step 5] PW / TFPW tests ...
[Step 6] Field significance (10 000 permutations) ...
[Figures] Generating 18 figures ...
    ✓  Output_TrendV4_..._Fig01_AnnualTimeSeries.png + .pdf
    ...
[Excel] Writing workbook ...
[Markdown] Writing research summary ...

=== Complete. Outputs in /data/chiang_mai/ ===
```

---

## Step 6: Run Post-Processing (Optional)

### Trend comparison analysis

```bash
python3 generate_trend_comparison_analysis.py
```

This script generates a structured manuscript-ready comparison document covering all four trend methods (MK, MMK, PW-MK, TFPW-MK). It reads from `results/final_N33/` by default — this path is hard-coded in the script and **must be updated** to match the actual output path for the new province before running.

### Q1 spatial maps

```bash
python3 generate_q1_maps.py /data/chiang_mai/
```

Generates publication-quality geographic trend maps using the province shapefile. Requires the shapefile to be present in the input folder (Step 3).

---

## Step 7: Verify Outputs

After the pipeline completes, verify the following checklist. All output files are written to the same directory as the input CSV.

- [ ] 18 PNG figures generated (prefixed `Output_TrendV4_<basename>_`)
- [ ] Corresponding 18 PDF files generated (if `SAVE_PDF = True`)
- [ ] Excel workbook generated (`_Results.xlsx`, 9 sheets)
- [ ] Research summary Markdown generated (`_Research_Summary.md`)
- [ ] No `ERROR` or `FAILED` lines in console output
- [ ] Station count printed in summary matches expected N
- [ ] Study period printed in summary matches expected start and end years
- [ ] `checkpoints/` subdirectory present (confirms checkpoint system ran)

---

## Step 8: Validate Scientific Results

After verifying file outputs, check the following sanity criteria. Violations do not necessarily indicate code errors — they may reflect genuine data characteristics — but they warrant investigation before publication.

### 1. MK–MMK agreement rate

The agreement rate between Standard MK and Modified MK (column `Agreement` in the Excel `MK vs MMK Comparison` sheet) should be **≥ 85%** for typical hydroclimatological datasets. A very low agreement rate (< 70%) indicates either:

- Strong positive autocorrelation inflating MK Z-statistics (Modified MK then shows fewer significant trends — expected and correct), or
- Data quality problems such as artificial persistence introduced by missing-value interpolation.

### 2. MMK correction factor (CF)

The inflation factor `CF = Var*(S) / Var(S)` is reported in the `Modified MK` Excel sheet. Expected range for daily-aggregated annual series: 1.0–3.0.

- **CF > 5.0** for multiple stations: extremely strong autocorrelation. Verify that the series are truly annual (not multi-year rolling totals) and that missing-value interpolation has not introduced artificial persistence.
- **CF = 1.0** for all stations: no autocorrelation detected at any lag. This is unusual for annual rainfall series and may indicate a short record (N < 15) where no lag-k correlation reaches significance.

### 3. All p-values = 1.0 (no trends detected)

If every station shows Z ≈ 0 and p = 1.0 at all scales, the date range likely did not parse correctly. Check that:

- `YEAR`, `MONTH`, `DAY` columns parsed as integers (not strings).
- The date range in the console output matches the input data.
- No systematic block of years was dropped by the 80% completeness threshold.

### 4. Field significance p-value distribution

Field significance p-values (Walker and LC-MC) should span the [0, 1] range for a dataset with a mix of significant and non-significant stations. If all p-values are 0.0 or 1.0, the Monte Carlo permutation count (`field_sig_permutations = 10000` in `rta/config.py`) may be too low relative to the observed significance fraction, or there is a genuine near-uniform trend signal across all stations.

---

## Common Errors

| Error message | Cause | Fix |
|---------------|-------|-----|
| `find_csv: no CSV found in /path/to/folder` | No `.csv` file in the target folder, or all CSVs start with `Output_` | Check the folder path; ensure the rainfall CSV is present and not prefixed with `Output_` |
| `load_coords: required columns missing — need Station, Lat, Lon` | Coordinates CSV has different column names | Rename columns to `Station`, `Lat`, `Lon` or add aliases supported by `load_coords()` |
| `No data after quality control` | All values are missing-value sentinels, or the sentinel list does not match the data format | Check `MISS_FLAGS` in `rta/config.py`; verify the CSV encodes missing data as one of the listed sentinels |
| `All series have fewer than MIN_N years` | Study period is shorter than `MIN_N = 10` years, or completeness thresholds are too strict | Verify the date range in the CSV; consider lowering completeness thresholds if data has many short gaps |
| `Province shapefile not found` | The `.shp` file path specified for `generate_q1_maps.py` does not exist | Verify the shapefile path and ensure all four shapefile components (`.shp`, `.dbf`, `.shx`, `.prj`) are present |
| `KeyError: '500001.0'` during coordinate lookup | Station IDs in the coordinates CSV were read as float64 by pandas | Ensure the coordinates CSV is loaded with `pd.read_csv(..., dtype=str)` — this is handled automatically by `load_coords()` in `rta/spatial.py` |
| `ValueError: wet_months and dry_months overlap` | Season month lists share one or more months | Check `WET_MONTHS` and `DRY_MONTHS` in `rta/config.py` for duplicates |

---

## Province-Specific Customisation Points (Pre-Config-File)

Until the configuration file described in `CONFIGURATION_GUIDE.md` is implemented, the following lines must be edited manually in the source code when porting to a new province. Only files listed here need to change; no other source files contain province-specific content.

| File | Line(s) | Current hard-coded value | What to change |
|------|---------|--------------------------|----------------|
| `rta/figures/spatial_maps.py` | 244 | `"Prachuap Khiri Khan Basin \| {period} \| N={n} stations"` | Replace `"Prachuap Khiri Khan Basin"` with new basin name |
| `rta/figures/spatial_maps.py` | 562 | `"Comprehensive Spatial Trend Overview \| Prachuap Khiri Khan Basin \| {period}"` | Replace `"Prachuap Khiri Khan Basin"` with new basin name |
| `rta/markdown.py` | 86–87 | `"Phetchaburi–Prachuap Khiri Khan River Basin, …"` | Replace with new basin and province name |
| `rta/trend_comparison_analysis.py` | 1408 | `"Phetchaburi–Prachuap Khiri Khan River Basin, Western Thailand"` | Replace with new basin name and region |
| `rta/trend_comparison_analysis.py` | 1524 | `"gauging stations in the Phetchaburi–Prachuap Khiri Khan River Basin, Thailand (1981–2014)"` | Replace province name and period |
| `rta/trend_comparison_analysis.py` | 1633–1634 | `"500001","500002", … ,"500301"` (station ID allowlist) | Replace with the station IDs of the new province, or remove the allowlist filter entirely |
| `rta/config.py` | 26–27 | `WET_MONTHS = [5,6,7,8,9,10]`, `DRY_MONTHS = [11,12,1,2,3,4]` | Update if the new province has a different monsoon calendar |

### Minimal change set for a new Thai province with the same season definition

If the new province uses the Southwest Monsoon calendar (May–October wet, November–April dry — appropriate for all Thai provinces), only four changes are required:

1. `rta/figures/spatial_maps.py` lines 244 and 562 — basin name in two suptitles
2. `rta/markdown.py` lines 86–87 — basin name in research summary
3. `rta/trend_comparison_analysis.py` lines 1408 and 1524 — province name in manuscript templates
4. `rta/trend_comparison_analysis.py` lines 1633–1634 — station ID allowlist

No changes are needed to `rta/config.py`, `rta/spatial.py`, `rta/aggregation.py`, or any figure module other than `rta/figures/spatial_maps.py`.
