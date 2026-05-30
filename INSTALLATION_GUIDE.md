# Installation Guide — Hydroclimatic Trend Analysis Framework

**Framework version:** 1.0 (based on Prachuap Khiri Khan release v1.0.0)
**Python:** 3.9+
**OS:** Linux / macOS / Windows (WSL recommended for Windows)

---

## 1. System Requirements

| Item | Minimum | Recommended |
|------|---------|-------------|
| Python | 3.9 | 3.11 |
| pip | 21.0 | latest |
| Disk space | 500 MB | 2 GB (TIFF figures are 60–150 MB each) |
| RAM | 2 GB | 4 GB (spatial interpolation steps) |
| OS | Linux / macOS | Linux; Windows via WSL2 |

> **Windows users:** The pipeline runs correctly under WSL2 (Ubuntu 20.04 or later). Native Windows is not tested. All path examples in this guide use POSIX notation.

---

## 2. Getting the Repository

```bash
git clone https://github.com/your-org/rainfall-trend-analysis.git
cd rainfall-trend-analysis
git checkout v1.0.0
```

Replace `your-org` with the actual organisation or user name hosting the repository. To use the latest development state instead of the tagged release, omit the `git checkout` line.

---

## 3. Python Environment Setup

Creating an isolated virtual environment is strongly recommended to avoid dependency conflicts with other projects.

```bash
# Create the environment (run once)
python3 -m venv .venv

# Activate — Linux / macOS
source .venv/bin/activate

# Activate — Windows (WSL)
source .venv/bin/activate

# Activate — Windows (PowerShell, if not using WSL)
.venv\Scripts\Activate.ps1
```

Your shell prompt will be prefixed with `(.venv)` when the environment is active. All subsequent commands in this guide assume the environment is active.

---

## 4. Installing Dependencies

### 4.1 Primary Pipeline

```bash
pip install -r requirements.txt
```

The `requirements.txt` in this repository pins the following packages for the primary pipeline:

| Package | Version constraint | Tested version | Role in pipeline |
|---------|--------------------|----------------|------------------|
| `numpy` | `>=1.21` | 2.4.6 | Array operations, vectorised Mann-Kendall S-statistic, Sen's slope pairwise differences |
| `pandas` | `>=1.3` | 3.0.3 | CSV loading, DatetimeIndex, temporal aggregation (`groupby`), results DataFrames |
| `scipy` | `>=1.7` | 1.17.1 | Normal distribution (`scipy.stats.norm`), descriptive statistics |
| `matplotlib` | `>=3.4` | 3.10.9 | All 14 publication figures (Agg backend, 600 DPI PNG + PDF output) |
| `openpyxl` | `>=3.0` | 3.1.5 | 9-sheet Excel workbook creation with full cell styling |

### 4.2 Optional Packages

These packages are **not** listed in `requirements.txt` and are **not** required to run the primary pipeline (`rainfall_trend_analysis_v4.py`). Install them only when you need the specific scripts that use them.

| Package | Used by | Purpose | Install command |
|---------|---------|---------|----------------|
| `statsmodels` | `Comparative_4MMK.py` | Extended autocorrelation diagnostics and additional regression methods used in the standalone comparative analysis script | `pip install statsmodels>=0.13` |
| `geopandas` | `generate_q1_maps.py` | Reading shapefiles and performing CRS reprojection for Q1-quality geographic maps; not involved in any figure produced by `rainfall_trend_analysis_v4.py` | `pip install geopandas` |

---

## 5. Verification Test

### 5.1 Check that all primary dependencies import correctly

```bash
python3 -c "import numpy, pandas, scipy, matplotlib, openpyxl; print('All dependencies satisfied')"
```

Expected output:

```
All dependencies satisfied
```

If you see an `ImportError`, confirm that your virtual environment is active (`which python3` should point to `.venv/bin/python3`) and re-run `pip install -r requirements.txt`.

### 5.2 Check the pipeline entry point

```bash
python3 rainfall_trend_analysis_v4.py --help
```

The script does not implement a formal `--help` flag. Passing an unrecognised flag is silently ignored and the script falls back to the current directory as the data folder. Expected console output on a directory that contains no CSV:

```
════════════════════════════════════════════════════════════════════════════════
  Rainfall Trend Analysis  v4.0  — Q1 Publication Edition
  MK + MMK (H&R98) + PW-MK (Yue&Wang 2004) + TFPW-MK + Sen's Slope
  Field Significance: Walker (1914) + Livezey-Chen (1983) MC
  Output: 14 Figures (8 v3 + 6 new) + 9-sheet Excel + Research MD
════════════════════════════════════════════════════════════════════════════════
```

followed by an error reporting that no CSV was found. This confirms the script loads correctly and all `rta/` package imports succeed.

---

## 6. Quick Validation Run

To confirm a complete end-to-end installation against the reference dataset shipped with the repository:

```bash
python3 rainfall_trend_analysis_v4.py . --no-resume
```

- `.` points to the repository root, which contains `Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv` and `station_coordinates.csv`.
- `--no-resume` forces a full re-run, ignoring any existing checkpoint files in `checkpoints/`.

**Expected outputs** (written to the same folder as the CSV):

| Category | Count | File pattern |
|----------|-------|-------------|
| PNG figures (v3-compatible) | 8 | `Output_TrendV2_*_Fig[1-8]_*.png` |
| PNG figures (v4 new) | 6 | `Output_TrendV4_*_Fig[9-14]_*.png` |
| PNG figures (spatial, coordinate-dependent) | 4 | `Output_TrendV4_*_Fig_Spatial*.png` |
| Excel workbook | 1 | `Output_TrendV4_*_Results.xlsx` (9 sheets) |
| Markdown summary | 1 | `Output_TrendV4_*_Research_Summary.md` |

Total: 18 PNG figures, 1 Excel workbook (9 sheets), 1 Markdown summary. PDF copies of every figure are also written when `SAVE_PDF = True` (the default).

Runtime on the reference dataset (12 stations, 1981–2014, 4 methods × 3 scales) is approximately 1–3 minutes on a modern laptop.

---

## 7. Common Installation Errors

| Error message | Cause | Fix |
|---------------|-------|-----|
| `UserWarning: Matplotlib is currently using … which is a non-GUI backend` | Matplotlib attempts to use an interactive backend on a headless system | No action needed — the script explicitly calls `matplotlib.use("Agg")` before any imports. If the warning appears anyway, set the environment variable `MPLBACKEND=Agg` before running: `export MPLBACKEND=Agg` |
| `ModuleNotFoundError: No module named 'openpyxl'` | `openpyxl` was not installed, or the wrong Python environment is active | Run `pip install openpyxl>=3.0` inside the active virtual environment. Confirm with `which python3`. |
| `ImportError: cannot import name 'norm' from 'scipy.stats'` or similar | Scipy version is too old | Run `pip install --upgrade "scipy>=1.7"` |
| `FileNotFoundError: [Errno 2] No such file or directory: '*.shp'` | `generate_q1_maps.py` cannot find a required shapefile | This error only affects `generate_q1_maps.py`, not the primary pipeline. Ensure the shapefile (e.g., `30_amarea_prachuap_khiri_khan.shp`) is present in the repository root. The primary pipeline (`rainfall_trend_analysis_v4.py`) does not read shapefiles and is unaffected. |
| `No CSV found in <folder>` | The specified data directory does not contain a qualifying daily rainfall CSV | Ensure the CSV filename does not start with `Output_` (that prefix is reserved for generated outputs). Place the raw data CSV directly in the folder passed to the script. |
| `ModuleNotFoundError: No module named 'rta'` | Script is run from outside the repository root | Run the script from the repository root directory where the `rta/` package folder is located: `cd /path/to/rainfall-trend-analysis && python3 rainfall_trend_analysis_v4.py .` |
