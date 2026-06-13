# Complete Reproducibility Guide
## Prachuap Khiri Khan Rainfall Trend Analysis — v1.0.0

**Repository:** `s0815547799-lab/rainfall-trend-analysis`  
**Branch:** `claude/hydroclimatology-claude-md-kudre`  
**Release:** v1.0.0 (figures commit `471bdc3`)  
**Verified date:** 2026-05-29  
**Verified result:** PASS — 18/18 PNG figures, 9-sheet Excel workbook, all statistics identical to published results

---

## 1. Software Requirements

### 1.1 Python Version

Python **3.11.15** (GCC 13.3.0) is the tested version. Python 3.7 or later is required
as a minimum, but numerical reproducibility is only guaranteed at 3.11.15.

### 1.2 Package Versions

| Package | Tested version | Minimum required |
|---|---|---|
| Python | **3.11.15** | >= 3.7 |
| numpy | **2.4.6** | >= 1.21 |
| pandas | **3.0.3** | >= 1.3 |
| scipy | **1.17.1** | >= 1.7 |
| matplotlib | **3.10.9** | >= 3.4 |
| openpyxl | **3.1.5** | >= 3.0 |

### 1.3 Optional Packages (not required for primary pipeline)

| Package | Tested version | Required by |
|---|---|---|
| statsmodels | not installed | `Comparative_4MMK.py` only (standalone; not primary pipeline) |
| pyproj | 3.7.2 | `rta_v5/` spatial interpolation (gracefully skipped if absent) |
| pyshp | 3.0.8 | `rta_v5/` spatial interpolation (gracefully skipped if absent) |

### 1.4 Operating System

| Attribute | Value |
|---|---|
| OS | Linux 6.18.5 |
| Architecture | x86-64 |
| Disk space required | ~500 MB (PNG/PDF figures; TIFF excluded from git, ~100 MB each) |
| RAM required | ~1 GB typical; 2 GB recommended |

### 1.5 Backend

The pipeline uses `matplotlib.use("Agg")` — no display server is required. All
figures are written directly to disk.

---

## 2. Repository Setup

### 2.1 Clone and Checkout

```bash
git clone https://github.com/s0815547799-lab/rainfall-trend-analysis.git
cd rainfall-trend-analysis
git checkout claude/hydroclimatology-claude-md-kudre
```

Verify the figures commit is present:

```bash
git log --oneline | grep 471bdc3
# Expected: 471bdc3 <commit message>
```

### 2.2 Create a Virtual Environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 2.3 Install Dependencies

```bash
pip install --upgrade pip
pip install numpy==2.4.6 pandas==3.0.3 scipy==1.17.1 matplotlib==3.10.9 openpyxl==3.1.5
```

To install using the pinned minimum requirements from `requirements.txt`:

```bash
pip install -r requirements.txt
```

Verify installations:

```bash
python3 -c "import numpy, pandas, scipy, matplotlib, openpyxl; \
  print('numpy', numpy.__version__); \
  print('pandas', pandas.__version__); \
  print('scipy', scipy.__version__); \
  print('matplotlib', matplotlib.__version__); \
  print('openpyxl', openpyxl.__version__)"
```

Expected output:

```
numpy 2.4.6
pandas 3.0.3
scipy 1.17.1
matplotlib 3.10.9
openpyxl 3.1.5
```

---

## 3. Input Data Verification

### 3.1 Required Input Files

Both files must be present in the working directory before running the pipeline.

| File | Description |
|---|---|
| `Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv` | Daily rainfall records, 12 stations, 1981–2014 |
| `station_coordinates.csv` | WGS84 station coordinates (128 stations) |

### 3.2 SHA256 Hashes

Verify file integrity before running:

```bash
sha256sum Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv
# Expected: f845a0248d3a2008e1d239fe04f63043f023445d077d5ee2c63e86203f498457

sha256sum station_coordinates.csv
# Expected: 051cf72a5e547d480a79186145ebb4e8ab02bc227f26a6e71db899c3e46ecf3e
```

On macOS, replace `sha256sum` with `shasum -a 256`.

### 3.3 Rainfall CSV Properties

| Property | Value |
|---|---|
| Filename | `Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv` |
| SHA256 | `f845a0248d3a2008e1d239fe04f63043f023445d077d5ee2c63e86203f498457` |
| Rows | 12,418 (daily records) |
| Columns | 15 (`YEAR`, `MONTH`, `DAY`, plus 12 station columns) |
| Date range | 1981-01-01 to 2014-12-31 |
| Missing data | 0 missing days (all 12,418 records complete) |

Station column names (in order):

```
500001  500002  500003  500004  500005  500006
500007  500008  500009  500201  500202  500301
```

Missing value flags recognized by the pipeline (converted to `NaN`):
`-99`, `-999`, `-9999`, `-9.99e+20`, `9.99e+20`, `1e+20`

### 3.4 Coordinates CSV Properties

| Property | Value |
|---|---|
| Filename | `station_coordinates.csv` |
| SHA256 | `051cf72a5e547d480a79186145ebb4e8ab02bc227f26a6e71db899c3e46ecf3e` |
| Columns | `Station`, `Lat`, `Lon`, `Altitude` |
| CRS | WGS84 (EPSG:4326) |
| Total stations | 128 |
| Rainfall stations covered | 12 (all of 500001–500301) |
| Coordinate range | Lat 11.18–12.59°N, Lon 99.55–99.96°E |

### 3.5 Verification Commands

```bash
# Check row and column counts
python3 -c "
import pandas as pd
df = pd.read_csv('Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv')
print('Rows:', len(df))
print('Columns:', len(df.columns))
print('Station columns:', list(df.columns[3:]))
"
# Expected: Rows: 12418, Columns: 15, Station columns: ['500001', ..., '500301']
```

---

## 4. Execution Order

All commands assume the working directory is the repository root and the virtual
environment is activated. The input CSV and `station_coordinates.csv` must be
present in the repository root (`.`).

### Step 1 — Primary Pipeline (required)

```bash
python3 rainfall_trend_analysis_v4.py . --no-resume
```

Use `--no-resume` to force a complete fresh run, bypassing any existing checkpoint
files. This is required for a clean reproducibility run.

To suppress PDF generation during development (saves disk space and time):

```bash
python3 rainfall_trend_analysis_v4.py . --no-resume --no-pdf
```

Expected exit code: `0`  
Expected output files: 21 (18 PNG + 1 XLSX + 1 MD + 1 TXT)  
Expected runtime: several minutes depending on hardware

**Runtime warning (non-fatal):** Six occurrences of `Ignoring fixed y limits to
fulfill fixed data aspect with adjustable data limits.` are emitted during
`Fig9_TaylorDiagram.png` generation. This is a cosmetic matplotlib layout
message; the figure is generated correctly.

### Step 2 — Trend Comparison Analysis

```bash
python3 generate_trend_comparison_analysis.py
```

Reads the primary Results.xlsx from `results/final_N33/excel/` and produces the
Master DB and per-method workbooks under
`results/final_N33_v5/Trend_Method_Comparison/`.

### Step 3 — All-vs-MK Workbook

```bash
python3 generate_all_vs_mk_workbook.py
```

Produces `Trend_Method_Comparison_All_vs_MK.xlsx` (9 sheets) in
`results/final_N33_v5/Trend_Method_Comparison/Excel/Master/`.

### Steps 4–6 — Supplementary Workbooks (independent; any order after Step 2)

```bash
python3 generate_tfpw_audit.py
python3 generate_reviewer_summary.py
python3 generate_final_validation.py
```

These three scripts are independent of each other and may be run in any order
after Step 2 completes. Each reads from the Master DB written in Step 2.

### Optional — Q1 Geographic Maps

```bash
python3 generate_q1_maps.py
```

Requires the provincial shapefile `30_amarea_prachuap_khiri_khan.shp` (and
sidecar files `.dbf`, `.prj`, `.shx`) to be present in the repository root.
These files are present in the current branch. Also requires `geopandas` and
`contextily` (not in `requirements.txt`). The script exits cleanly with an error
message if the shapefile or optional dependencies are absent.

### Optional — v5 Spatial Interpolation

```bash
python3 rainfall_trend_analysis_v5.py . --no-resume
```

Requires `pyproj` and `pyshp`. These are imported conditionally; the script
degrades gracefully if they are absent. This script is not part of the primary
pipeline and is not required to reproduce the v1.0.0 published results.

---

## 5. Expected Outputs

All outputs are written to the same directory as the input CSV (the repository
root when the pipeline is invoked as `python3 rainfall_trend_analysis_v4.py .`).

The `<BASENAME>` token in all filenames expands to:
`Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan`

### 5.1 After Step 1 — v3-Compatible Figures (8 PNG @ 600 DPI)

```
Output_TrendV2_<BASENAME>_Fig1_AnnualTimeSeries.png
Output_TrendV2_<BASENAME>_Fig2_WetDryTimeSeries.png
Output_TrendV2_<BASENAME>_Fig3_SenSlope_AllScales.png
Output_TrendV2_<BASENAME>_Fig4_MK_vs_MMK_Comparison.png
Output_TrendV2_<BASENAME>_Fig5_Significance_Heatmap.png
Output_TrendV2_<BASENAME>_Fig6_Autocorrelation.png
Output_TrendV2_<BASENAME>_Fig7_MonthlyClimatology.png
Output_TrendV2_<BASENAME>_Fig8_SpatialTrend_Summary.png
```

### 5.2 After Step 1 — v4 Publication Figures (10 PNG @ 600 DPI)

```
Output_TrendV4_<BASENAME>_Fig9_TaylorDiagram.png
Output_TrendV4_<BASENAME>_Fig10_ZComparisonMatrix.png
Output_TrendV4_<BASENAME>_Fig11_MethodComparison.png
Output_TrendV4_<BASENAME>_Fig12_ACF_Diagnostics.png
Output_TrendV4_<BASENAME>_Fig13_FieldSignificance.png
Output_TrendV4_<BASENAME>_Fig14_SpatialMaps.png
Output_TrendV4_<BASENAME>_Fig_SpatialStation.png
Output_TrendV4_<BASENAME>_Fig_SpatialMethods.png
Output_TrendV4_<BASENAME>_Fig_SpatialFieldSig.png
Output_TrendV4_<BASENAME>_Fig_SpatialFull.png
```

**Total: 18 PNG figures** (8 v3-compatible + 10 v4 publication).

PDFs are generated alongside each PNG when `--no-pdf` is not passed.

### 5.3 After Step 1 — Tabular Outputs

```
Output_TrendV4_<BASENAME>_Results.xlsx          (9-sheet workbook)
Output_TrendV4_<BASENAME>_Research_Summary.md   (13 KB Markdown)
Output_TrendV4_<BASENAME>_DrySeasonValidation.txt
```

**Excel workbook sheet names (9 sheets):**

| Sheet | Content |
|---|---|
| S1 Standard MK | MK: S, Var(S), Z, tau, p, Trend, rho_1 per station x scale |
| S2 Modified MK | MMK: adds Var*(S), n*, correction factor (CF) |
| S3 MK vs MMK Comparison | Side-by-side: delta-Z, delta-p, Agreement flag |
| S4 Sen's Slope | beta, CI_lo, CI_hi, Z, p, Trend per station x scale x method |
| S5 Descriptive Statistics | N, Mean, Median, Max, Min, Std, CV, Wet-days, Skewness |
| S6 PW-MK Results | Prewhitening (Yue & Wang 2004) trend results |
| S7 4-Method Comparison | All 4 methods side-by-side; agreement rates |
| S8 Field Significance | Walker and LC-MC p-values per scale |
| S9 Methods & References | Citation table |

### 5.4 After Steps 2–6 — Additional Workbooks (7 files)

```
results/final_N33_v5/Trend_Method_Comparison/Excel/Master/
    Trend_Method_Comparison_Master.xlsx
    Trend_Method_Comparison_Tables.xlsx
    Trend_Method_Comparison_All_vs_MK.xlsx
    TFPW_Audit.xlsx
    Reviewer_Summary.xlsx
    Disagreement_Stations.xlsx
    SenSlope_Comparison.xlsx
    Final_Methodological_Assessment.xlsx
```

---

## 6. Validation Procedure

### 6.1 Figure Count Check

After Step 1 completes, confirm 18 PNG files are present:

```bash
ls Output_TrendV*.png | wc -l
# Expected: 18
```

List all 18 figures individually:

```bash
ls Output_TrendV2_*_Fig*.png Output_TrendV4_*_Fig*.png Output_TrendV4_*_Fig_Spatial*.png
```

### 6.2 Statistical Validation Table

Extract the following values from the generated Excel workbook
(`Output_TrendV4_<BASENAME>_Results.xlsx`) and confirm they match exactly.
Any discrepancy indicates a software version mismatch or data corruption.

| Metric | Expected value | Source sheet |
|---|---|---|
| Standard MK significant (p<0.05) | **6 of 36 tests** | S7 |
| Standard MK significant (p<0.01) | **2 of 36 tests** | S7 |
| Modified MK significant (p<0.05) | **4 of 36 tests** | S7 |
| Modified MK significant (p<0.01) | **1 of 36 tests** | S7 |
| PW-MK significant (p<0.05) | **3 of 36 tests** | S7 |
| PW-MK significant (p<0.01) | **0 of 36 tests** | S7 |
| TFPW-MK significant (p<0.05) | **7 of 36 tests** | S7 |
| TFPW-MK significant (p<0.01) | **3 of 36 tests** | S7 |
| MMK vs MK agreement rate | **94.4% (34/36)** | S3 |
| PW-MK vs MK agreement rate | **91.7% (33/36)** | S7 |
| TFPW-MK vs MK agreement rate | **97.2% (35/36)** | S7 |
| Max lag-1 autocorrelation | **0.583 (S3, Wet Season)** | S7 |
| Max correction factor (CF) | **2.7251 (S3, Wet Season)** | S2 |
| Min effective sample size (n_eff) | **12.48 years** | S2 |
| CF range | **1.0000 – 2.7251** | S2 |
| CF entries > 1 (count) | **5** | S2 |
| Annual field significance — Walker p | **0.460 (not significant)** | S8 |
| Annual field significance — LC-MC p | **0.436 (not significant)** | S8 |
| Wet Season field significance — Walker p | **0.118 (not significant)** | S8 |
| Wet Season field significance — LC-MC p | **0.099 (not significant)** | S8 |
| Dry Season field significance — Walker p | **0.020 (SIGNIFICANT, p<0.05)** | S8 |
| Dry Season field significance — LC-MC p | **0.016 (SIGNIFICANT, p<0.05)** | S8 |

**Field significance MC seed:** The LC-MC computation uses `seed=42`. Any change
to the seed will produce different p-values. Do not modify `rta/field_significance.py`.

### 6.3 QC Verification

The pipeline should report zero missing days and zero filled gaps for all 12 stations:

```
Station   Missing   Outliers   Filled
S1        0 (0.0%)  79         0
S2        0 (0.0%)  176        0
S3        0 (0.0%)  61         0
S4        0 (0.0%)  57         0
S5        0 (0.0%)  43         0
S6        0 (0.0%)  49         0
S7        0 (0.0%)  61         0
S8        0 (0.0%)  32         0
S9        0 (0.0%)  40         0
S10       0 (0.0%)  62         0
S11       0 (0.0%)  32         0
S12       0 (0.0%)  48         0
```

Outliers are flagged by the IQR method (Q3 + 3×IQR) but are not removed. The
counts above are informational only and do not affect trend results.

### 6.4 SHA256 Verification of Input Files

```bash
sha256sum Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv station_coordinates.csv
```

Expected output (exact):

```
f845a0248d3a2008e1d239fe04f63043f023445d077d5ee2c63e86203f498457  Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv
051cf72a5e547d480a79186145ebb4e8ab02bc227f26a6e71db899c3e46ecf3e  station_coordinates.csv
```

---

## 7. Checkpoint System

### 7.1 Overview

`rainfall_trend_analysis_v4.py` uses a 6-step pickle-based checkpoint system
implemented in `rta/checkpoint.py`. After each major computation step, results
are serialized to a `.pkl` file in the `checkpoints/` subdirectory. On the next
run, the pipeline detects the highest completed step and offers to resume from
that point, skipping all prior computation.

### 7.2 Checkpoint Files

| File | Step | Content saved |
|---|---|---|
| `checkpoints/ckpt_01_qc.pkl` | 01_qc | Cleaned daily DataFrame after QC |
| `checkpoints/ckpt_02_aggregation.pkl` | 02_aggregation | Annual/wet/dry/monthly aggregates + descriptive stats |
| `checkpoints/ckpt_03_acf.pkl` | 03_acf | Autocorrelation results for all stations × scales |
| `checkpoints/ckpt_04_trends.pkl` | 04_trends | Trend test results (MK, MMK, PW-MK, TFPW-MK, Sen's slope) |
| `checkpoints/ckpt_05_comparison.pkl` | 05_comparison | MK vs MMK comparison table |
| `checkpoints/ckpt_06_field_sig.pkl` | 06_field_sig | Field significance results (Walker + LC-MC) |

### 7.3 Step Mapping

```
Step  Name             Content
  1   01_qc            QC-cleaned daily data
  2   02_aggregation   Temporal aggregates + descriptive stats
  3   03_acf           Autocorrelation vectors and lag-1 significance flags
  4   04_trends        All 4 trend methods x 36 station-scale combinations
  5   05_comparison    MK vs MMK side-by-side table with agreement flags
  6   06_field_sig     Walker (1914) + Livezey-Chen (1983) MC field significance
```

### 7.4 Resume Logic

When `--no-resume` is not passed, the pipeline:

1. Scans `checkpoints/` for `ckpt_*.pkl` files
2. Identifies the highest completed step by name
3. Prompts interactively: `Resume from step N+1? [Y/n]:`
4. If confirmed, loads all prior step outputs from pickle and jumps to step N+1
5. In non-interactive environments (e.g., CI, piped input), `EOFError` is caught
   and the run defaults to a fresh start

### 7.5 When to Use `--no-resume`

Always pass `--no-resume` for:

- Reproducibility verification runs (ensures no stale checkpoint state)
- After modifying any `rta/` source file
- After updating package versions
- When checkpoint files exist from a different input dataset

```bash
# Guaranteed clean run:
python3 rainfall_trend_analysis_v4.py . --no-resume
```

To manually clear checkpoints before running:

```bash
rm -f checkpoints/ckpt_*.pkl
python3 rainfall_trend_analysis_v4.py .
```

---

## 8. Known Issues and Workarounds

### 8.1 Fig10 Panel (b) — Blank Panel Bug (Fixed in commit 471bdc3)

**Symptom:** In `Fig10_ZComparisonMatrix.png`, panel (b) renders blank (no data
plotted) when the figure is generated from a branch prior to commit `471bdc3`.

**Root cause:** The `_METHOD_KEYS` list in `rta/figures/method_comparison.py`
(line 33) contained `"Modified MK (H&R98)"` as the second element. The trend
DataFrame produced by the v4 pipeline stores the modified MK results under the
key `"Modified MK"` (without the parenthetical). The mismatch caused the
DataFrame filter `trend_df[trend_df["Method"] == "Modified MK (H&R98)"]` to
return an empty result, producing a blank panel.

**Fix applied in commit 471bdc3:**

```python
# Before (broken):
_METHOD_KEYS = ["Standard MK", "Modified MK (H&R98)", "PW-MK", "TFPW-MK"]

# After (correct):
_METHOD_KEYS = ["Standard MK", "Modified MK", "PW-MK", "TFPW-MK"]
```

**Verification:** Confirm the fix is present:

```bash
grep "_METHOD_KEYS" rta/figures/method_comparison.py
# Expected: _METHOD_KEYS  = ["Standard MK", "Modified MK", "PW-MK", "TFPW-MK"]
```

Confirm `"H&R98"` does not appear in the list:

```bash
grep -n "H&R98" rta/figures/method_comparison.py
# Expected: no output (zero matches in the _METHOD_KEYS definition)
```

The human-readable label `"MMK"` is provided by `_METHOD_SHORT["Modified MK"]`
on the following line, which is unaffected.

### 8.2 Spatial Figures Skipped — Station ID Matching

**Symptom:** Spatial figures (`Fig_SpatialStation`, `Fig_SpatialMethods`,
`Fig_SpatialFieldSig`, `Fig_SpatialFull`, `Fig14_SpatialMaps`) are silently
skipped and not generated.

**Cause:** `rta/spatial.py` reads `station_coordinates.csv` using
`pd.read_csv(..., dtype=str)`. If a version of this module is used that does not
force string dtype, pandas reads integer station IDs (e.g., `500001`) as
`float64`, producing keys like `'500001.0'`. These keys do not match the string
station names from the rainfall CSV (`'500001'`), so `validate_coords()` reports
zero matched stations and spatial figures are skipped.

**Workaround:** Ensure the repository is on the correct branch and commit. The
`dtype=str` fix is present in all commits on `claude/hydroclimatology-claude-md-kudre`.
If spatial figures are still not generated, verify that `station_coordinates.csv`
is present in the same directory as the input CSV.

**Verification:** If spatial figures are generated, the following files will be
present:

```bash
ls Output_TrendV4_*_Fig_Spatial*.png | wc -l
# Expected: 4
```

### 8.3 Q1 Maps — Optional Shapefile Dependency

**Symptom:** `generate_q1_maps.py` exits with a file-not-found error.

**Cause:** The script requires a provincial boundary shapefile
(`30_amarea_prachuap_khiri_khan.shp` and sidecar files `.dbf`, `.prj`, `.shx`).
These files are present in the repository root on the current branch.

If the shapefile is present but the script still fails, the likely cause is that
`geopandas` or `contextily` are not installed. These packages are not listed in
`requirements.txt` and are not required for any primary pipeline output.

**Impact:** The Q1 geographic maps are supplementary outputs. Their absence does
not affect any of the 18 primary figures, the Excel workbook, or any statistical
result.

### 8.4 Taylor Diagram Y-Limit Warning

**Symptom:** During `Fig9_TaylorDiagram.png` generation, matplotlib emits 6
occurrences of:

```
UserWarning: Ignoring fixed y limits to fulfill fixed data aspect
with adjustable data limits.
```

**Cause:** Interaction between `set_aspect("equal")` and fixed axis limits in a
polar-projection Taylor diagram layout.

**Impact:** None. The figure is generated correctly with all data plotted. This
is a cosmetic warning from the matplotlib layout engine.

**Status:** Known, non-fatal. No action required for publication.

### 8.5 `Comparative_4MMK.py` — Requires statsmodels

**Symptom:** `Comparative_4MMK.py` fails with `ModuleNotFoundError: No module
named 'statsmodels'`.

**Cause:** This standalone extended-analysis script requires `statsmodels`, which
is not installed by the primary `requirements.txt`.

**Impact:** None on the primary pipeline. `Comparative_4MMK.py` is an independent
extended analysis utility, not part of the v1.0.0 release pipeline.

**Workaround:** `pip install statsmodels>=0.13` if the extended analysis is needed.

### 8.6 TIFF Figures Excluded from Repository

TIFF versions of all 18 figures are generated locally during execution (~100 MB
each) but are excluded from version control by `.gitignore`. To regenerate TIFF
outputs, run the primary pipeline; no additional flags are needed as TIFF
generation is part of the standard output.

---

*This guide reflects the verified reproducibility run performed on 2026-05-29
in an isolated environment containing only the two raw input files. All 18 PNG
figures and all 22 key statistical values were reproduced exactly from raw inputs
using only the packages listed in Section 1.*
