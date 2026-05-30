# Download Instructions
**Package:** `prachuap_v1.0_runnable.zip`  
**Release:** v1.0.0 — Prachuap Khiri Khan Rainfall Trend Analysis

---

## ZIP File Location

```
Repository root:
  prachuap_v1.0_runnable.zip   (337 KB compressed / 1.5 MB uncompressed)

Absolute path in this environment:
  /home/user/rainfall-trend-analysis/prachuap_v1.0_runnable.zip
```

---

## Download via Git

The ZIP is committed to the repository on branch `claude/hydroclimatology-claude-md-kudre`:

```bash
git clone https://github.com/s0815547799-lab/rainfall-trend-analysis.git
cd rainfall-trend-analysis
git checkout claude/hydroclimatology-claude-md-kudre
```

The file `prachuap_v1.0_runnable.zip` is at the repository root.

---

## Extract the Package

```bash
unzip prachuap_v1.0_runnable.zip
cd prachuap_v1.0_runnable
```

---

## Install Dependencies

**Option A — pip:**
```bash
pip install -r requirements.txt
```

Packages installed: `numpy`, `pandas`, `scipy`, `matplotlib`, `openpyxl`  
Tested on Python 3.11.15. Compatible with Python 3.9+.

**Option B — conda:**
```bash
conda env create -f environment.yml
conda activate prachuap-trend
```

---

## Execute the Pipeline

Run all commands from inside `prachuap_v1.0_runnable/`:

```bash
# Step 1 — Primary pipeline (~5–15 min)
python rainfall_trend_analysis_v4.py data/ --no-resume

# Step 2 — Method comparison master workbook + figures
python generate_trend_comparison_analysis.py

# Step 3 — All-vs-MK workbook
python generate_all_vs_mk_workbook.py

# Step 4 — TFPW audit workbook
python generate_tfpw_audit.py

# Step 5 — Reviewer summary workbook
python generate_reviewer_summary.py

# Step 6 — Final validation workbooks
python generate_final_validation.py
```

After Step 1, outputs appear in `data/`. After Steps 2–6, outputs appear in `results/`.

---

## Verify the Run

Open `data/Output_TrendV4_*_Results.xlsx`, sheet `S8 Field Significance`. Confirm:

| Scale | Walker p | Significant? |
|---|---|---|
| Annual | 0.460 | No |
| Wet Season | 0.118 | No |
| Dry Season | **0.020** | **Yes** |

Open sheet `S7 4-Method Comparison` and count rows where the `*_sig` column contains `*` or `**`:

| Method | Expected significant rows |
|---|---|
| MK_sig | 6 |
| MMK_sig | 4 |
| PW_sig | 3 |
| TFPW_sig | 7 |

---

## Package Contents Summary

```
prachuap_v1.0_runnable/
├── README_RUN.md                   ← full run guide
├── requirements.txt
├── environment.yml
├── rainfall_trend_analysis_v4.py   ← primary pipeline (Step 1)
├── rainfall_trend_analysis_v5.py   ← optional Q1 spatial maps
├── generate_*.py (5 files)         ← post-processing (Steps 2–6)
├── data/
│   ├── Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv
│   └── station_coordinates.csv
├── rta/                            ← core analysis package (19 modules)
│   └── figures/                   ← figure modules (13 files)
└── rta_v5/                         ← optional spatial package (6 modules)
```

Total: **49 files**, **17,571 source lines**
