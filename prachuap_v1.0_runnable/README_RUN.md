# Rainfall Trend Analysis — Prachuap Khiri Khan
## Quick-Run Guide

**Release:** v1.0.0  
**Study area:** Phetchaburi–Prachuap Khiri Khan River Basin, Western Thailand  
**Period:** 1981–2014 (12 stations, 34 years)  
**Methods:** Standard MK, Modified MK (Hamed & Rao 1998), PW-MK (Yue & Wang 2004), TFPW-MK (Yue et al. 2002)

---

## 1. Requirements

- Python 3.9+ (tested on 3.11.15)
- pip packages: `numpy`, `pandas`, `scipy`, `matplotlib`, `openpyxl`

---

## 2. Install Dependencies

**Option A — pip (recommended):**
```bash
pip install -r requirements.txt
```

**Option B — conda:**
```bash
conda env create -f environment.yml
conda activate prachuap-trend
```

---

## 3. Input Files

Both input files are included in `data/`:

| File | Description |
|---|---|
| `data/Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv` | Daily rainfall, 12 stations, 1981–2014 |
| `data/station_coordinates.csv` | WGS84 coordinates for all stations |

---

## 4. Execution Order

Run each command from the package root directory (where `README_RUN.md` is located).

**Step 1 — Primary pipeline** (all trend tests, all figures, primary Excel workbook):
```bash
python rainfall_trend_analysis_v4.py data/ --no-resume
```

Expected output in `data/`:
- 18 PNG figures at 600 DPI
- 18 PDF figures
- `Output_TrendV4_*_Results.xlsx` (9-sheet workbook)
- `Output_TrendV4_*_Research_Summary.md`
- Spatial figures: `Fig_SpatialStation`, `Fig_SpatialMethods`, `Fig_SpatialFieldSig`, `Fig_SpatialFull`

Runtime: ~5–15 minutes (Monte Carlo field significance is the bottleneck).

**Step 2 — Method comparison master workbook + 10 comparison figures:**
```bash
python generate_trend_comparison_analysis.py
```

**Step 3 — All-vs-MK comparison workbook:**
```bash
python generate_all_vs_mk_workbook.py
```

**Step 4 — TFPW audit workbook:**
```bash
python generate_tfpw_audit.py
```

**Step 5 — Reviewer summary workbook:**
```bash
python generate_reviewer_summary.py
```

**Step 6 — Final validation workbook:**
```bash
python generate_final_validation.py
```

---

## 5. Expected Final Outputs

After all six steps:

| Output type | Count | Location |
|---|---|---|
| Publication figures (PNG) | 18 | `data/` |
| Publication figures (PDF) | 18 | `data/` |
| Spatial figures (PNG+PDF) | 8 | `data/` |
| Comparison figures (PNG+PDF+SVG) | 30 | `results/final_N33_v5/Trend_Method_Comparison/Figures/` |
| Primary Excel workbook (9 sheets) | 1 | `data/` |
| Method comparison workbooks | 8 | `results/final_N33_v5/Trend_Method_Comparison/Excel/` |
| Manuscript tables (CSV + XLSX) | 14 | `results/final_N33_v5/Trend_Method_Comparison/Tables/` |
| Additional analysis workbooks | 4 | `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/` |

---

## 6. Validation — Key Statistics to Verify

Open `Output_TrendV4_*_Results.xlsx` and confirm:

| Sheet | Metric | Expected value |
|---|---|---|
| Standard MK | Rows with p < 0.05 | **6** of 36 |
| Modified MK (H&R98) | Rows with p < 0.05 | **4** of 36 |
| PW-MK | Rows with p < 0.05 | **3** of 36 |
| TFPW-MK | Rows with p < 0.05 | **7** of 36 |
| Modified MK (H&R98) | Max Correction Factor | **2.7251** (S3, Wet) |
| Modified MK (H&R98) | Min n_eff | **12.48** years (S3, Wet) |
| Field Significance | Dry Season Walker p | **0.020** (significant) |
| Field Significance | Dry Season LC-MC p | **0.016** (significant) |

---

## 7. Checkpoint / Resume

The pipeline saves 6 checkpoints after each major step. If interrupted, resume from the last checkpoint by omitting `--no-resume`:

```bash
python rainfall_trend_analysis_v4.py data/
```

To force a full rerun from raw data:
```bash
python rainfall_trend_analysis_v4.py data/ --no-resume
```

Checkpoints are stored in `data/checkpoints/`.

---

## 8. Package Structure

```
prachuap_v1.0_runnable/
├── README_RUN.md                          ← this file
├── requirements.txt                       ← pip dependencies
├── environment.yml                        ← conda environment
├── rainfall_trend_analysis_v4.py          ← primary pipeline
├── rainfall_trend_analysis_v5.py          ← optional: Q1 spatial maps
├── generate_trend_comparison_analysis.py  ← post-processing step 2
├── generate_all_vs_mk_workbook.py         ← post-processing step 3
├── generate_tfpw_audit.py                 ← post-processing step 4
├── generate_reviewer_summary.py           ← post-processing step 5
├── generate_final_validation.py           ← post-processing step 6
├── data/
│   ├── Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv
│   └── station_coordinates.csv
├── rta/                                   ← core analysis package
│   ├── config.py                          ← constants (palette, DPI, seasons)
│   ├── io.py                              ← CSV/coordinate discovery & QC
│   ├── aggregation.py                     ← annual/wet/dry aggregation
│   ├── autocorr.py                        ← lag-k autocorrelation
│   ├── trend_tests.py                     ← Standard MK + Sen's slope
│   ├── batch.py                           ← MK/MMK/PW/TFPW batch runner
│   ├── pw.py                              ← Prewhitening MK
│   ├── tfpw.py                            ← Trend-Free Prewhitening MK
│   ├── field_sig.py                       ← Walker + Livezey-Chen MC
│   ├── field_significance.py              ← extended field significance
│   ├── checkpoint.py                      ← pickle checkpoint/resume
│   ├── excel_output.py                    ← 9-sheet Excel writer
│   ├── markdown.py                        ← research summary writer
│   ├── spatial.py                         ← coordinate loading/validation
│   ├── spatial_maps.py                    ← spatial function re-exports
│   ├── trend_comparison_analysis.py       ← method comparison engine
│   ├── trend_method_comparison.py         ← comparison figures engine
│   └── figures/
│       ├── timeseries.py                  ← Fig1, Fig2
│       ├── bars.py                        ← Fig3
│       ├── comparison.py                  ← Fig4
│       ├── heatmaps.py                    ← Fig5
│       ├── acf_plots.py                   ← Fig6, Fig12
│       ├── climatology.py                 ← Fig7
│       ├── spatial.py                     ← Fig8
│       ├── taylor.py                      ← Fig9
│       ├── method_comparison.py           ← Fig10, Fig11
│       ├── field_sig_plot.py              ← Fig13
│       ├── spatial_maps.py                ← Fig14, Fig_Spatial*
│       └── helpers.py                     ← shared utilities
└── rta_v5/                                ← optional: Q1 spatial package
    ├── spatial_interpolation_v5.py
    ├── spatial_publication_q1_v5.py
    ├── spatial_layout_v5.py
    ├── spatial_export_v5.py
    └── spatial_validation_v5.py
```
