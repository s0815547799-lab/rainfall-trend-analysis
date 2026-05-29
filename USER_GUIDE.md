# User Guide — Hydroclimatic Trend Analysis Framework

**Framework version:** 1.0

---

## 1. What This Framework Does

This framework detects and quantifies long-term trends in daily rainfall records from multiple gauging stations. It applies four Mann-Kendall trend detection methods in parallel:

| Method | Abbreviation | Reference |
|--------|-------------|-----------|
| Standard Mann-Kendall | MK | Mann (1945); Kendall (1975) |
| Modified Mann-Kendall (autocorrelation correction) | MMK / H&R98 | Hamed & Rao (1998) *J. Hydrol.* 204:182–196 |
| Prewhitening Mann-Kendall | PW-MK | Yue & Wang (2004) *Water Resour. Res.* 40:W08307 |
| Trend-Free Prewhitening Mann-Kendall | TFPW-MK | Yue et al. (2002) |

Each method is applied to three temporal scales — **annual**, **wet season** (May–October), and **dry season** (November–April hydrological year) — for every station in the input dataset. Sen's non-parametric slope estimator (with 95% CI) quantifies the magnitude of detected trends. Field significance across the station network is assessed using Walker's (1914) binomial test and the Livezey-Chen (1983) Monte Carlo procedure.

**Outputs** are publication-ready at 600 DPI: 14 PNG figures (+ PDF copies), a 9-sheet Excel workbook, and a Markdown manuscript template.

---

## 2. Quick Start (3 Steps)

**Step 1 — Prepare your data**

Place two files in a single folder:
- A daily rainfall CSV (column format: `YEAR`, `MONTH`, `DAY`, then one column per station).
- A station coordinates CSV (filename must match `*coord*.csv` or `*station*.csv`; required columns: `Station`, `Lat`, `Lon`).

**Step 2 — Run the pipeline**

```bash
python3 rainfall_trend_analysis_v4.py /path/to/data/
```

The script auto-discovers the rainfall CSV and coordinates file. No configuration file is needed.

**Step 3 — Collect outputs**

All outputs are written to the same folder as the input CSV:
- 14 PNG figures (18 when station coordinates are present — 4 additional spatial maps)
- 1 Excel workbook (9 sheets)
- 1 Markdown research summary

---

## 3. Execution Sequence

The pipeline runs 11 steps in order. Steps 1–6 are checkpointed; the script can resume after interruption (see Section 7).

| Step | Action | Details |
|------|--------|---------|
| 1 | CSV discovery and loading | Auto-detects the first CSV in the target folder not prefixed with `Output_`; loads into a `DatetimeIndex` DataFrame |
| 2 | Quality control | Replaces missing-value flags (`-99`, `-999`, `-9999`, `-9.99e+20`, `9.99e+20`, `1e+20`) with `NaN`; detects IQR outliers (> Q3 + 3×IQR per station); fills gaps of ≤ 5 consecutive days by linear interpolation |
| 3 | Temporal aggregation | Computes annual (≥80% completeness), wet-season May–Oct (≥80%), dry-season Nov–Apr hydrological year (≥80%), and monthly (≥60%) totals; dry-season Nov–Dec of year *Y* are assigned to year *Y+1* |
| 4 | Lag-1 autocorrelation assessment | Pearson lag-1 correlation per station × scale; significance threshold: \|r₁\| > Z₀.₀₂₅ / √n |
| 5 | Standard MK test | Vectorised S-statistic with tie correction; returns S, Var(S), Z, Kendall's τ, p-value, trend direction |
| 6 | Modified MK — Hamed & Rao (1998) | Autocorrelation correction on ranked series; effective sample size n* = n / [1 + (2/n) × Σ (n−k) ρ_k]; adjusted Var*(S) |
| 7 | PW-MK — Yue & Wang (2004) | Prewhitening: removes lag-1 autoregressive component before MK test |
| 8 | TFPW-MK — Yue et al. (2002) | Trend-free prewhitening: removes both trend and autocorrelation before MK test |
| 9 | Sen's slope estimation | Non-parametric slope β = median of all pairwise (yⱼ − yᵢ)/(tⱼ − tᵢ); 95% CI via Gilbert (1987) rank-based method |
| 10 | Field significance | Walker (1914) binomial test + Livezey-Chen (1983) Monte Carlo across the station network |
| 11 | Figure generation, Excel workbook, Markdown summary | 14 figures at 600 DPI, 9-sheet workbook, manuscript template |

---

## 4. Input File Requirements

### Daily Rainfall CSV

- **Column order:** `YEAR`, `MONTH`, `DAY`, followed by one column per rain gauge station.
- **Station names** are taken directly from the column headers.
- **Missing value flags** handled automatically: `-99`, `-999`, `-9999`, `-9.99e+20`, `9.99e+20`, `1e+20` are all converted to `NaN` on load.
- **Minimum record length:** Stations with fewer than 10 valid years at a given temporal scale are skipped for MK testing (`MIN_N = 10`).
- **No header row is required beyond the column names** — the script does not expect any metadata rows above the column header.

Example fragment:

```
YEAR,MONTH,DAY,500001,500101,500201
1981,1,1,0.0,0.0,-99
1981,1,2,2.5,0.0,1.2
```

### Station Coordinates CSV

- **Auto-detected** by filename glob: `*coord*.csv` or `*station*.csv` in the data folder.
- **Required columns:** `Station`, `Lat`, `Lon`
- **Optional column:** `Altitude` (used for terrain-coloured station maps if present)
- **Coordinate reference system:** WGS84 (EPSG:4326) — no explicit CRS field is stored in the file; WGS84 is assumed.
- **Station column type:** Values must match the station column headers in the rainfall CSV exactly (string comparison). The file is read with `dtype=str` to prevent integer IDs such as `500001` from being silently cast to `500001.0`.

If the coordinates file is absent, all non-spatial figures and workbook sheets are generated normally; spatial figures (Fig_SpatialStation, Fig_SpatialMethods, Fig_SpatialFieldSig, Fig_SpatialFull) are silently skipped.

---

## 5. Interpreting Outputs

### 5.1 Figures

All figures use a consistent colour scheme: green tones for increasing trends, red tones for decreasing trends, grey for non-significant results. Significance markers: `**` = p < 0.01, `*` = p < 0.05, `ns` = not significant.

| Figure ID | Filename pattern | What it shows | How to read it |
|-----------|-----------------|---------------|----------------|
| Fig 1 | `*_Fig1_AnnualTimeSeries.png` | Annual rainfall time series per station with MMK trend line and 95% CI shading | Each panel is one station. Shaded band is the Sen's slope 95% CI. Trend direction colour (green/red/grey) reflects MMK significance. |
| Fig 2 | `*_Fig2_WetDryTimeSeries.png` | 4-panel: (a) regional wet-season, (b) regional dry-season time series; (c–d) per-station wet/dry Sen's slopes | Panels (a–b) show the basin-wide mean. Panels (c–d) show individual station slopes as bar charts — positive = wetting trend, negative = drying trend. |
| Fig 3 | `*_Fig3_SenSlope_AllScales.png` | Sen's slope (mm/yr) for Annual / Wet / Dry in three rows; error bars = 95% CI | Bars coloured by trend direction. Stations with overlapping CI that includes zero should be treated as uncertain regardless of p-value. |
| Fig 4 | `*_Fig4_MK_vs_MMK_Comparison.png` | 4-panel: (a) Z-statistic scatter MK vs MMK, (b) p-value scatter, (c) ΔZ bar chart, (d) agreement heatmap | Points above the 1:1 line in (a) indicate MMK inflates Z relative to MK; below indicates deflation. Panel (d) shows the proportion of stations where both methods reach the same significance conclusion. |
| Fig 5 | `*_Fig5_Significance_Heatmap.png` | Dual heatmap: Z-statistic matrix (stations × temporal scales) for Standard MK and Modified MK side-by-side | Warm colours = positive Z (increasing trend); cool colours = negative Z (decreasing trend). Cells with \|Z\| > 1.96 are significant at p < 0.05. |
| Fig 6 | `*_Fig6_Autocorrelation.png` | (a) Lag-1 autocorrelation per station with significance threshold; (b) ACF of regional mean | Bars exceeding the dashed threshold line have statistically significant lag-1 autocorrelation — these stations benefit most from the MMK or PW/TFPW correction. |
| Fig 7 | `*_Fig7_MonthlyClimatology.png` | Monthly mean rainfall per station + regional mean climatology | The regional panel (bottom-right or overlaid) summarises the monsoon seasonality. High July–September values are typical for the western Gulf of Thailand basin. |
| Fig 8 | `*_Fig8_SpatialTrend_Summary.png` | 4-panel index-based summary: (a) Sen's slope vs Z bubble plot, (b) trend count bar chart, (c) ΔSlope (MK vs MMK), (d) slope heatmap | Panel (a): bubble size = \|slope\|; colour = direction. Panel (b): stacked count of increasing/decreasing/ns stations per scale. This figure uses station index order, not geographic coordinates. |
| Fig 9 | `*_Fig9_TaylorDiagram.png` | Taylor diagram comparing station annual series to the regional mean | Radial distance from the reference point = RMSE. Angular position = correlation. Stations clustering near the reference point are well-represented by the regional mean. |
| Fig 10 | `*_Fig10_ZComparisonMatrix.png` | Z-statistic comparison matrix across all 4 methods × stations × scales | Use this figure to identify stations where method choice substantially changes the significance conclusion. |
| Fig 11 | `*_Fig11_MethodComparison.png` | Scatter plots comparing Z-statistics and p-values between all method pairs | Six pair-wise panels. The diagonal reference line is the 1:1 agreement line. |
| Fig 12 | `*_Fig12_ACF_Diagnostics.png` | Extended ACF diagnostic panels for all stations | Shows autocorrelation structure used as input to the MMK variance correction. |
| Fig 13 | `*_Fig13_FieldSignificance.png` | Field significance results: Walker binomial test and Livezey-Chen MC p-values per scale | A result significant at field level means that the count of locally significant stations exceeds what would be expected by chance across the network. |
| Fig 14 | `*_Fig14_SpatialMaps.png` | 3-panel geographic bubble map (Annual / Wet / Dry, MMK method) | Bubble size proportional to \|Sen's slope\|. Green = significant increasing, red = significant decreasing, grey = not significant. Requires station coordinates file. |
| Fig_SpatialStation | `*_Fig_SpatialStation.png` | Single-panel station location map with compass, scale bar, and station labels | Coloured by altitude if the `Altitude` column is present in the coordinates file. |
| Fig_SpatialMethods | `*_Fig_SpatialMethods.png` | 4×3 geographic bubble grid: 4 methods × 3 scales | Use to compare spatial patterns of significance across methods. |
| Fig_SpatialFieldSig | `*_Fig_SpatialFieldSig.png` | 3 geographic \|Z\| magnitude panels (MMK) + Walker/LC p-value bar chart | The bar chart summarises network-level significance; the map panels show where in the basin the strongest signals are located. |
| Fig_SpatialFull | `*_Fig_SpatialFull.png` | 7-panel comprehensive overview: station map, annual 4-method maps, slope colour map, field significance | The primary publication-ready spatial synthesis figure. |

### 5.2 Excel Workbook (9 sheets)

| Sheet | Tab name | Contents |
|-------|----------|----------|
| S1 | Standard MK | S-statistic, Var(S), Z, Kendall's τ, p-value, trend direction, lag-1 ρ₁ for every station × temporal scale |
| S2 | Modified MK (H&R98) | All S1 fields plus Var*(S), effective sample size n*, inflation factor n/n* |
| S3 | MK vs MMK Comparison | Side-by-side MK and MMK Z and p-values, ΔZ = Z_MMK − Z_MK, agreement flag |
| S4 | Sen's Slope | β (mm/yr), CI_lo, CI_hi, Z, p-value, trend direction for each station × scale × method |
| S5 | Descriptive Statistics | N (years), mean, median, maximum, minimum, standard deviation, CV, wet-day count, skewness per station |
| S6 | Methods & References | Three-column reference table: method name, citation, description |
| S7 | 4-Method Comparison | Z-statistics and p-values for all four methods (MK, MMK, PW-MK, TFPW-MK) side by side |
| S8 | Field Significance | Walker binomial test and Livezey-Chen MC results per temporal scale and method |
| S9 | Dry Season Validation | Hydrological year assignment verification — confirms Nov–Dec of year *Y* are correctly attributed to year *Y+1* |

Sheets S7–S9 are written only when the corresponding data is successfully computed. They are absent from the workbook if the pipeline is interrupted before the relevant step.

### 5.3 Significance Notation

| Marker | Threshold | Two-tailed critical Z |
|--------|-----------|-----------------------|
| `**` | p < 0.01 | \|Z\| > 2.5758 |
| `*` | p < 0.05 | \|Z\| > 1.9600 |
| `ns` | p ≥ 0.05 | \|Z\| ≤ 1.9600 |

Both Standard MK and Modified MK results are reported in all tables. Always refer to the MMK or TFPW-MK result for stations with statistically significant lag-1 autocorrelation (see Fig 6).

---

## 6. Command-Line Options

```
python3 rainfall_trend_analysis_v4.py [data_dir] [--no-resume] [--no-pdf]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `data_dir` | positional | Script's own directory | Path to the folder containing the input CSV and coordinates file. Can be `.` for the current directory or an absolute path. |
| `--no-resume` | flag | off | Ignore existing checkpoint files and run the full pipeline from Step 1. Use this when you have changed input data or want to verify reproducibility. |
| `--no-pdf` | flag | off | Skip PDF output. Only PNG figures are saved. Useful during development to reduce disk I/O; PDF saving is re-enabled automatically on the next run if the flag is omitted. |

**Examples:**

```bash
# Run on the current directory, resuming from the last checkpoint
python3 rainfall_trend_analysis_v4.py .

# Run on an explicit data path, force full re-run, skip PDFs
python3 rainfall_trend_analysis_v4.py /data/my_basin --no-resume --no-pdf

# Run with coordinate-less data (spatial figures will be skipped)
python3 rainfall_trend_analysis_v4.py /data/no_coords/
```

---

## 7. The Checkpoint System

The pipeline saves a checkpoint file after each of the first six computational steps. Checkpoints are stored as pickle files in a `checkpoints/` subdirectory within the output folder.

| Checkpoint file | Saved after step | Contents |
|-----------------|-----------------|----------|
| `01_qc.pkl` | Step 1 (Load + QC) | Cleaned daily DataFrame, station list, QC report |
| `02_aggregation.pkl` | Step 3 (Aggregation) | Annual/wet/dry/monthly aggregates, descriptive statistics |
| `03_acf.pkl` | Step 4 (ACF) | Autocorrelation flags (`any_sig_ac`) |
| `04_trends.pkl` | Steps 5–8 (All 4 methods) | Full `trend_df` with results for all stations × scales × methods |
| `05_comparison.pkl` | Step 9 (Comparison tables) | `comp_df` (MK vs MMK), `comp4_df` (4-method) |
| `06_field_sig.pkl` | Step 10 (Field significance) | `field_sig_df` |

**Resuming after interruption:** On the next run (without `--no-resume`), the script detects the highest completed checkpoint, reports it, and prompts:

```
  ⚡ Checkpoint found: step 4 (04_trends)
     Resume from step 5? [Y/n]:
```

Answering `Y` (or pressing Enter) skips directly to figure generation. Answering `n` re-runs from that step.

**When to use `--no-resume`:**
- After changing the input CSV or replacing missing data.
- After upgrading the `rta/` package with statistical corrections.
- For final reproducibility verification before manuscript submission.

---

## 8. Running Post-Processing Scripts

After the primary pipeline completes, a suite of post-processing scripts can generate additional outputs for the 4-method comparative analysis:

### Step 1 — Primary pipeline (produces `Output_TrendV4_*_Results.xlsx`)

```bash
python3 rainfall_trend_analysis_v4.py /path/to/data/ --no-resume
```

### Step 2 — 4-Method comparison master database

```bash
python3 generate_trend_comparison_analysis.py
```

This script reads the Excel workbook produced in Step 1 and generates a full comparison database under `results/final_N33_v5/Trend_Method_Comparison/`, including:
- Master comparison workbook (`Trend_Method_Comparison_Master.xlsx`) and per-method workbooks
- 7 supplementary data tables (`.xlsx` + `.csv`)
- 10 additional figures (PNG + TIFF + PDF + SVG)
- 9 Markdown manuscript template files

The script resolves the workbook path automatically from `results/final_N33/excel/`. If the path cannot be resolved, it falls back to `data/reference/ebc6aee6-Rainfall_2Trend_Results.xlsx` or the `WB4_PATH` environment variable.

**Do not run `generate_trend_comparison_analysis.py` before the primary pipeline** — it depends on the `Output_TrendV4_*_Results.xlsx` workbook produced in Step 1.

---

## 9. Output Naming Convention

All output files follow the pattern:

```
Output_Trend{version}_{csv_basename}_{descriptor}.{ext}
```

| Token | Example | Meaning |
|-------|---------|---------|
| `Output_TrendV2_` | `Output_TrendV2_` | v3-compatible outputs (Figs 1–8); generated by both v3 and v4 scripts |
| `Output_TrendV4_` | `Output_TrendV4_` | v4 new outputs (Figs 9–14, spatial figures, 9-sheet Excel, Research Summary) |
| `{csv_basename}` | `Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan` | Input CSV filename without the `.csv` extension |
| `{descriptor}` | `Fig1_AnnualTimeSeries` | Figure number and content label, or `Results` (Excel), `Research_Summary` (Markdown) |
| `.png` | `.png` | Primary raster output; always generated |
| `.pdf` | `.pdf` | Vector copy; generated when `SAVE_PDF = True` (default) or `--no-pdf` is not set |
| `.xlsx` | `.xlsx` | Excel workbook |
| `.md` | `.md` | Markdown research summary |

**Examples:**

```
Output_TrendV2_rainfall_data_Fig1_AnnualTimeSeries.png
Output_TrendV4_rainfall_data_Fig14_SpatialMaps.pdf
Output_TrendV4_rainfall_data_Results.xlsx
Output_TrendV4_rainfall_data_Research_Summary.md
```

---

## 10. Troubleshooting

| Issue | Likely cause | Fix |
|-------|-------------|-----|
| "No CSV found in `<folder>`" | The target folder contains no qualifying CSV, or all CSVs are prefixed with `Output_` | Confirm the input CSV is present in the folder. Ensure the raw data filename does not begin with `Output_`. |
| "No significant trends found" | This is often a genuine result for the dataset and region, not an error | Inspect the Z-statistic columns in S1/S2 of the Excel workbook. Values with \|Z\| < 1.96 are non-significant; this is a valid scientific outcome for many river basins. |
| Spatial figures are blank or not produced | `station_coordinates.csv` (or matching `*coord*.csv`) not present in the data folder | Place the coordinates CSV in the same folder as the rainfall CSV. The primary pipeline continues without it; only spatial figures are skipped. |
| "Taylor diagram warnings" (cosmetic) | Matplotlib geometry edge cases when station scatter is very low | These are cosmetic warnings only. The figure is computed and saved correctly. Suppress with `PYTHONWARNINGS=ignore` if needed. |
| Fig 10 panel blank (one panel is empty) | Known issue in early builds — fixed in commit `471bdc3` | Pull the latest code (`git pull`) and re-run with `--no-resume`. |
| Pipeline hangs at Step 4 on large datasets | Step 4 runs all 4 MK methods × all stations × all scales and can be slow for N > 100 stations | Allow it to complete; the checkpoint saved at the end of Step 4 means subsequent runs skip directly to figures. Estimated runtime for 12 stations is under 3 minutes; 100 stations may take 20–30 minutes. |
| `KeyError: '500001.0'` in spatial matching | Station IDs in the coordinates CSV were read as float64 by pandas, producing keys like `'500001.0'` that do not match string headers | This is fixed in the current `rta/spatial.py` via `pd.read_csv(..., dtype=str)`. Pull the latest code if you see this error. |
| `ModuleNotFoundError: No module named 'statsmodels'` | `Comparative_4MMK.py` requires `statsmodels`, which is not in `requirements.txt` | Install it: `pip install statsmodels>=0.13`. This package is not needed for the primary pipeline. |
