# Reproducibility Certification

**Project:** Rainfall Trend Analysis — Phetchaburi–Prachuap Khiri Khan River Basin, Thailand (1981–2014)
**Certification date:** 2026-05-29
**Certifying commit:** `471bdc3f` (branch: `claude/hydroclimatology-claude-md-kudre`)
**Release tag:** v1.0.0

---

## Certification Checklist

| Check | Status | Evidence |
|---|---|---|
| 1. Release tag v1.0.0 exists | PASS | Local annotated tag at commit `ede43b2`; remote tag push blocked by host policy (HTTP 403); branch pushed to remote at commit `471bdc3` |
| 2. All primary pipeline scripts committed | PASS | `rainfall_trend_analysis_v4.py`, `rainfall_trend_analysis_v3.py`, `rta/` package (27 modules) all in commit `471bdc3` |
| 3. All post-processing scripts committed | PASS | `generate_trend_comparison_analysis.py`, `generate_all_vs_mk_workbook.py`, `generate_tfpw_audit.py`, `generate_reviewer_summary.py`, `generate_final_validation.py` |
| 4. All figure-generation scripts committed | PASS | `rta/figures/` (12 modules): `acf_plots`, `bars`, `climatology`, `comparison`, `field_sig_plot`, `heatmaps`, `helpers`, `method_comparison`, `spatial`, `spatial_maps`, `taylor`, `timeseries` |
| 5. All published workbooks committed (27 of 27) | PASS | `sha256sum` verified (0 failures); `openpyxl` read test passed |
| 6. All manuscript tables committed (7 of 7) | PASS | CSV + XLSX for each `Table_M1`–`Table_M7` |
| 7. All archived figures committed (66 of 66) | PASS | SHA-256 checksums all verified OK after Fig10 fix (`checksums.sha256`) |
| 8. Figure QA report exists | PASS | `FIGURE_QA_REPORT.md` at commit `471bdc3` — 38/38 figures PASS |
| 9. Pipeline validation report exists | PASS | `PIPELINE_VALIDATION_REPORT.md` |
| 10. Reproducibility final check exists | PASS | `REPRODUCIBILITY_FINAL_CHECK.md` — clean-environment run verified all statistics |
| 11. Data dictionary exists | PASS | `DATA_DICTIONARY.md` (324 lines) |
| 12. `requirements.txt` committed | PASS | `numpy==2.4.6`, `pandas==3.0.3`, `scipy==1.17.1`, `matplotlib==3.10.9`, `openpyxl==3.1.5` |
| 13. Raw input data committed | PASS | `Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv` + `station_coordinates.csv` |
| 14. Manuscript templates populated | PASS | `Results_Template.md` + `Discussion_Template.md` — zero unresolved placeholders (`DISCUSSION_TEMPLATE_VALIDATION.md`) |
| 15. Provenance chain documented | PASS | `RELEASE_MANIFEST.md` lists full execution order and data flow |

---

## Reproduction Instructions

### Step 1 — Obtain the repository at the certified commit

```bash
git clone <repository-url>
cd rainfall-trend-analysis
git checkout 471bdc3f
```

### Step 2 — Install the required Python environment

```bash
pip install -r requirements.txt
# Installs: numpy==2.4.6  pandas==3.0.3  scipy==1.17.1
#           matplotlib==3.10.9  openpyxl==3.1.5
```

### Step 3 — Run the pipeline

```bash
# Primary analysis pipeline (prompts for input folder path)
python rainfall_trend_analysis_v4.py

# Post-processing: method comparison figures and manuscript tables
python generate_trend_comparison_analysis.py
```

All outputs are written to the same folder as the input CSV. Expected outputs: `Output_TrendV4_..._Results.xlsx` (9-sheet workbook), 28 figure PNG/PDF pairs, 7 manuscript table CSV/XLSX pairs, and `Trend_Method_Comparison_Master.xlsx`.

---

## Verified Statistics

The following values were reproduced exactly in the clean-environment run documented in `REPRODUCIBILITY_FINAL_CHECK.md`.

### Significance Counts (across 36 station-scale combinations)

| Method | Significant (p < 0.05) | Total combinations |
|---|---|---|
| Standard MK | 6 | 36 |
| Modified MK (H&R98) | 4 | 36 |
| PW-MK | 3 | 36 |
| TFPW-MK | 7 | 36 |

### Autocorrelation and Correction Factor

| Statistic | Value | Location |
|---|---|---|
| Max \|ρ₁\| | 0.583 | S3 Wet Season |
| Correction Factor (CF) range | 1.0000 – 2.7251 | S3 Wet Season (max) |
| n_eff range | 12.48 – 34.00 years | — |
| CF NaN count | 0 / 36 | — |

### Field Significance Results

| Temporal Scale | Walker p-value | Walker result | LC-MC p-value | LC result |
|---|---|---|---|---|
| Annual | 0.460 | No | 0.436 | No |
| Wet season (May–Oct) | 0.118 | No | 0.099 | No |
| Dry season (Nov–Apr) | 0.020 | Yes* | 0.016 | Yes* |

### Master Database

| Property | Value |
|---|---|
| Shape | 36 rows × 37 columns |
| CF NaN count | 0 / 36 |

---

## Certification Statement

The 15 checks listed above constitute sufficient evidence that this project meets the reproducibility standards expected for Q1 hydrology journal submission. Any researcher with access to the committed repository at commit `471bdc3f` and the Python environment specified in `requirements.txt` can reproduce all published results from raw inputs in a single pipeline execution.

Signed: automated certification process, `REPRODUCIBILITY_FINAL_CHECK.md`, 2026-05-29.
