# Rainfall Trend Analysis — Prachuap Khiri Khan Basin

**Version:** v4.0 | **Period:** 1981–2014 | **Stations:** 12 | **Region:** Western Thailand

Publication-quality hydroclimatological trend analysis for the Phetchaburi–Prachuap
Khiri Khan River Basin. Implements four trend methods (Standard MK, Modified MK,
PW-MK, TFPW-MK), field significance testing, and true WGS84 geographic spatial maps.

---

## Workflow

```
CSV input
  └─ QC (missing flags → NaN, IQR outlier detection, gap interpolation)
       └─ Aggregation (Annual / Wet May–Oct / Dry Nov–Apr hydrological year)
            └─ Autocorrelation assessment (lag-1, two-tailed test)
                 ├─ Standard MK (Mann 1945; Kendall 1975)
                 ├─ Modified MK — Hamed & Rao 1998 (AC-corrected variance)
                 ├─ PW-MK — Prewhitening (Yue & Wang 2004)
                 └─ TFPW-MK — Trend-Free Prewhitening (Yue et al. 2002)
                      └─ Sen's Slope + 95% CI (Gilbert 1987)
                           └─ Field Significance
                           │    ├─ Walker (1914) binomial test
                           │    └─ Livezey-Chen (1983) Monte Carlo
                           └─ Spatial Maps (WGS84 geographic, 5 figures)
                                └─ Excel (9 sheets) + Publication Figures (28 PNG/PDF)
```

---

## Quick Start

```bash
# Full pipeline with checkpoint/resume
python rainfall_trend_analysis_v4.py /path/to/data/folder

# Legacy single-file pipeline (backward compatible)
python rainfall_trend_analysis_v3.py /path/to/data/folder

# Skip checkpoint prompt
python rainfall_trend_analysis_v4.py /path/to/data/folder --no-resume

# Skip PDF generation
python rainfall_trend_analysis_v4.py /path/to/data/folder --no-pdf
```

The pipeline auto-discovers the first `.csv` in the folder (not prefixed `Output_`)
and writes all outputs to that same folder.

---

## Input Format

| Column | Description |
|--------|-------------|
| `YEAR` | 4-digit year |
| `MONTH` | 1–12 |
| `DAY` | 1–31 |
| `<station_id>` | Daily rainfall (mm), one column per gauge |

Missing-value flags recognised: `-99`, `-999`, `-9999`, `-9.99e+20`, `9.99e+20`, `1e+20`

**Optional:** Place `station_coordinates.csv` (columns: `Station`, `Lat`, `Lon`) in
the same folder to enable WGS84 geographic spatial maps. Without it, all other
outputs are generated normally.

---

## Outputs

### Figures (600 DPI PNG + PDF)

| Figure | Content |
|--------|---------|
| Fig 1 | Annual rainfall time series with MMK trend line and 95% CI |
| Fig 2 | Wet / Dry season time series (regional + per-station slopes) |
| Fig 3 | Sen's slope bar chart — Annual / Wet / Dry (error bars = 95% CI) |
| Fig 4 | Standard MK vs Modified MK comparison (Z scatter, p scatter, ΔZ, agreement) |
| Fig 5 | Significance heatmap — Z-statistic matrix (stations × scales × methods) |
| Fig 6 | Autocorrelation diagnostics (lag-1 per station + regional ACF) |
| Fig 7 | Monthly rainfall climatology (per station + regional mean) |
| Fig 8 | Spatial trend summary — index-based bubble / slope heatmap |
| Fig 9 | Taylor diagram (station vs regional reference) |
| Fig 10 | Z-statistic comparison matrix (4 methods) |
| Fig 11 | Method comparison scatter (MK / MMK / PW / TFPW) |
| Fig 12 | ACF diagnostics — per-station lag-1 to lag-10 panels |
| Fig 13 | Field significance — Walker and LC-MC p-values by scale |
| Fig 14 | Geographic MMK Sen's slope maps (Annual / Wet / Dry) |
| Fig SpatialStation | Station network map with compass, scale bar, labels |
| Fig SpatialMethods | 4×3 geographic grid: method × scale bubble maps |
| Fig SpatialFieldSig | Geographic \|Z\| magnitude maps + field significance bar chart |
| Fig SpatialFull | 7-panel comprehensive spatial overview |

### Tables
- **Excel workbook** (9 sheets): Standard MK · Modified MK · PW-MK · TFPW-MK ·
  4-Method Comparison · Field Significance · Sen's Slope · Descriptive Statistics ·
  Dry-Season Validation
- **Research Summary** (Markdown): paper-ready results narrative

---

## Statistical Methods

| Method | Reference | AC correction |
|--------|-----------|---------------|
| Standard MK | Mann (1945); Kendall (1975) | None |
| Modified MK | Hamed & Rao (1998) *J. Hydrol.* 204:182–196 | Variance inflation via ranked-series AC |
| PW-MK | Yue & Wang (2004) *Water Resour. Res.* 40:W08307 | Prewhitening of series before MK |
| TFPW-MK | Yue et al. (2002) | Trend removal before AC estimation |
| Sen's Slope | Sen (1968) *JASA* 63:1379; Gilbert (1987) | — |
| Field significance | Walker (1914); Livezey & Chen (1983) | — |

---

## Reproducibility

### Python Environment

| Component | Version |
|-----------|---------|
| Python | 3.11.15 |
| numpy | 2.4.6 |
| pandas | 3.0.3 |
| scipy | 1.17.1 |
| matplotlib | 3.10.9 |
| openpyxl | 3.1.5 |

```bash
pip install numpy==2.4.6 pandas==3.0.3 scipy==1.17.1 matplotlib==3.10.9 openpyxl==3.1.5
```

### Execution Steps

```bash
# 1. Clone repository
git clone https://github.com/s0815547799-lab/rainfall-trend-analysis.git
cd rainfall-trend-analysis

# 2. Install dependencies
pip install numpy pandas scipy matplotlib openpyxl

# 3. Place input files in a working directory, e.g. ./data/
#    Required: daily rainfall CSV (YEAR, MONTH, DAY, <station> columns)
#    Optional: station_coordinates.csv (Station, Lat, Lon)

# 4. Run v4 pipeline
python rainfall_trend_analysis_v4.py ./data

# 5. Outputs written to ./data/
#    Output_TrendV2_*  — Figs 1–8 (v3-compatible)
#    Output_TrendV4_*  — Figs 9–14e, Excel, Markdown

# 6. On re-run, resume from checkpoint (saves ~5 min computation)
python rainfall_trend_analysis_v4.py ./data
# Answer [Y] at the resume prompt to skip Steps 1–6
```

### Checkpoint System

The v4 pipeline saves computation state to `checkpoints/` after each of 6 steps:

| Step | File | Content |
|------|------|---------|
| 1 | `ckpt_01_qc.pkl` | QC'd dataframe, station list, period |
| 2 | `ckpt_02_aggregation.pkl` | Annual/wet/dry aggregates, dry-season validation |
| 3 | `ckpt_03_acf.pkl` | Lag-1 autocorrelation results |
| 4 | `ckpt_04_trends.pkl` | Full 4-method trend results DataFrame |
| 5 | `ckpt_05_comparison.pkl` | MK vs MMK + 4-method comparison tables |
| 6 | `ckpt_06_field_sig.pkl` | Field significance results |

Use `--no-resume` to force a fresh run and overwrite all checkpoints.

---

## Project Structure

```
rainfall-trend-analysis/
├── rainfall_trend_analysis_v3.py   # Legacy single-file pipeline (18 figures)
├── rainfall_trend_analysis_v4.py   # Modular pipeline (28 figures, 9-sheet Excel)
├── rta/                            # Analysis package
│   ├── config.py                   # Constants, colour palette, savefig
│   ├── io.py                       # CSV I/O, QC, load_coords
│   ├── aggregation.py              # Temporal aggregation
│   ├── autocorr.py                 # Autocorrelation
│   ├── trend_tests.py              # MK, MMK, Sen's slope
│   ├── pw.py                       # Prewhitening MK
│   ├── tfpw.py                     # Trend-Free Prewhitening MK
│   ├── batch.py                    # Batch execution
│   ├── field_sig.py                # Field significance (v4)
│   ├── checkpoint.py               # Checkpoint/resume
│   ├── spatial.py                  # Coordinate loading
│   ├── spatial_maps.py             # Spatial figure exports
│   ├── excel_output.py             # Excel writer
│   ├── markdown.py                 # Markdown summary writer
│   └── figures/                   # Figure modules (14 files)
├── station_coordinates.csv         # WGS84 station coordinates (128 stations)
├── CLAUDE.md                       # Full technical specification
├── CHANGELOG.md                    # Version history
└── README.md                       # This file
```

---

## License

MIT — see [LICENSE](LICENSE)
