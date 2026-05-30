# Release Manifest — v1.0
**Repository:** `s0815547799-lab/rainfall-trend-analysis`  
**Release:** v1.0.0  
**Commit:** `ede43b2f199a702ba56312ef8f5a533cf9c402ee`  
**Branch:** `claude/hydroclimatology-claude-md-kudre`  
**Manifest date:** 2026-05-29

---

## Release Identity

| Attribute | Value |
|---|---|
| Release tag | `v1.0.0` (local annotated tag; remote tag push blocked by host policy) |
| Commit hash | `ede43b2f199a702ba56312ef8f5a533cf9c402ee` |
| Branch | `claude/hydroclimatology-claude-md-kudre` |
| Python version | 3.11.15 |
| Platform | Linux 6.18.5 |

---

## Software Environment

| Package | Version | Role |
|---|---|---|
| Python | 3.11.15 | Runtime |
| numpy | 2.4.6 | Array operations, statistical utilities |
| pandas | 3.0.3 | Data loading, aggregation, DataFrame I/O |
| scipy | 1.17.1 | Statistical distributions (`scipy.stats`) |
| matplotlib | 3.10.9 | Figure generation (backend: Agg) |
| openpyxl | 3.1.5 | Excel workbook creation and reading |

Full install: `pip install -r requirements.txt`

---

## Raw Inputs

| File | Format | Rows | Description |
|---|---|---|---|
| `Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv` | CSV | ~12,419 | Daily rainfall, 12 stations, 1981–2014 |
| `station_coordinates.csv` | CSV | 128 | WGS84 coordinates, 128 stations |

---

## Primary Pipeline Scripts

| Script | Version | Description |
|---|---|---|
| `rainfall_trend_analysis_v4.py` | v4.0 | Main pipeline (MK/MMK/PW/TFPW + spatial figures + Excel + MD) |
| `rainfall_trend_analysis_v3.py` | v3.0 | Legacy single-file pipeline (MK/MMK + 8 figures) |
| `rainfall_trend_analysis_v5.py` | v5.0 | Undocumented experimental version (excluded from primary pipeline) |

### rta/ Package Modules

| Module | Description |
|---|---|
| `rta/__init__.py` | Package entry point |
| `rta/config.py` | Shared constants (DPI, colours, thresholds) |
| `rta/aggregation.py` | Temporal aggregation (annual/wet/dry/monthly) |
| `rta/autocorr.py` | Autocorrelation computation |
| `rta/batch.py` | Multi-station batch execution |
| `rta/checkpoint.py` | 6-step pickle checkpoint/resume system |
| `rta/excel_output.py` | 9-sheet Excel workbook writer |
| `rta/field_sig.py` | Field significance (Walker 1914 + LC 1983) |
| `rta/field_significance.py` | Field significance re-export |
| `rta/pw.py` | Prewhitening MK (Yue & Wang 2004) |
| `rta/tfpw.py` | Trend-Free Prewhitening MK (Yue et al. 2002) |
| `rta/spatial.py` | Coordinate loading and validation |
| `rta/spatial_maps.py` | Geographic figure top-level re-export |
| `rta/trend_comparison_analysis.py` | Master DB assembly (H-2 fix applied) |
| `rta/figures/spatial.py` | Fig8 index-based spatial summary |
| `rta/figures/spatial_maps.py` | Geographic spatial figure functions |
| `rta/figures/acf_plots.py` | ACF diagnostic figures |
| `rta/figures/bars.py` | Sen's slope bar charts |
| `rta/figures/climatology.py` | Monthly climatology figures |
| `rta/figures/comparison.py` | MK vs MMK comparison figures |
| `rta/figures/field_sig_plot.py` | Field significance figures |
| `rta/figures/heatmaps.py` | Z-statistic heatmap figures |
| `rta/figures/helpers.py` | Shared figure utilities |
| `rta/figures/method_comparison.py` | 4-method comparison figures |
| `rta/figures/taylor_diagram.py` | Taylor diagram figure |
| `rta/figures/timeseries.py` | Time series figures (Fig1, Fig2) |
| `rta/figures/z_comparison.py` | Z-comparison matrix figure |
| `rta/trend_tests/__init__.py` | Trend test package entry |

---

## Post-Processing Scripts

| Script | Description |
|---|---|
| `generate_trend_comparison_analysis.py` | Generates Master DB + all comparison outputs from WB1 |
| `generate_all_vs_mk_workbook.py` | All-vs-MK comparison workbook |
| `generate_tfpw_audit.py` | TFPW audit workbook |
| `generate_reviewer_summary.py` | Reviewer summary workbook |
| `generate_final_validation.py` | Final validation workbook |
| `generate_trend_comparison.py` | Trend comparison (legacy) |
| `generate_q1_maps.py` | Q1-quality spatial maps (requires shapefile — M-1 open debt) |
| `Comparative_4MMK.py` | Extended comparative analysis (requires statsmodels — M-2 open debt) |
| `calval_split.py` | Cal/val split utility (requires inputs absent from repo — L-5 out of scope) |

---

## Execution Order

```
1. python3 rainfall_trend_analysis_v4.py <data_dir> --no-resume
      → 18 PNG figures + 1 Excel (9 sheets) + Research Summary MD

2. python3 generate_trend_comparison_analysis.py
      → Trend_Method_Comparison_Master.xlsx (36×37 Master DB)
      → 10 comparison figures (PNG + PDF + SVG)
      → 7 manuscript tables (CSV + XLSX)
      → Manuscript templates (Results_Template.md, Discussion_Template.md)

3. python3 generate_all_vs_mk_workbook.py
4. python3 generate_tfpw_audit.py
5. python3 generate_reviewer_summary.py
6. python3 generate_final_validation.py
      → Supplementary workbooks and validation files
```

---

## Published Results (27 Excel Workbooks)

### Primary Results Workbook (WB1)

| Workbook | Path | Sheets |
|---|---|---|
| `Output_TrendV4_..._Results.xlsx` | `results/final_N33/excel/` | 9 (S1–S9) |

### Trend Method Comparison Workbooks

| Workbook | Path |
|---|---|
| `Trend_Method_Comparison_Master.xlsx` | `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/` |
| `Trend_Method_Comparison_All_vs_MK.xlsx` | same |
| `Trend_Method_Comparison_Tables.xlsx` | same |
| `Disagreement_Stations.xlsx` | same |
| `Final_Methodological_Assessment.xlsx` | same |
| `Reviewer_Summary.xlsx` | same |
| `SenSlope_Comparison.xlsx` | same |
| `TFPW_Audit.xlsx` | same |
| `MK_Analysis.xlsx` | `Excel/MK_Analysis/` |
| `MMK_Analysis.xlsx` | `Excel/MMK_Analysis/` |
| `MMK_vs_MK_Comparison.xlsx` | `Excel/MMK_Analysis/` |
| `PW_MK_Analysis.xlsx` | `Excel/PW_MK_Analysis/` |
| `PW_MK_vs_MK_Comparison.xlsx` | `Excel/PW_MK_Analysis/` |
| `TFPW_MK_Analysis.xlsx` | `Excel/TFPW_MK_Analysis/` |
| `TFPW_MK_vs_MK_Comparison.xlsx` | `Excel/TFPW_MK_Analysis/` |
| `Table_M1_Method_Agreement.xlsx` | `Tables/` |
| `Table_M2_Significance_Transitions.xlsx` | `Tables/` |
| `Table_M3_Correction_Factor_Impact.xlsx` | `Tables/` |
| `Table_M4_Station_Disagreement_Inventory.xlsx` | `Tables/` |
| `Table_M5_Field_Significance_Comparison.xlsx` | `Tables/` |
| `Table_M6_Top_AC_Affected_Stations.xlsx` | `Tables/` |
| `Table_M7_Method_Ranking_Summary.xlsx` | `Tables/` |
| `Trend_Method_Comparison_Q1.xlsx` | `results/final_N33_v5/` |
| `Interpolation_Comparison.xlsx` | `results/final_N33_v5/validation/` |
| `LOOCV.xlsx` | `results/final_N33_v5/validation/` |
| `Workbook_Inventory_Report.xlsx` | `results/` |

**Total: 27 workbooks — all open successfully (0 failures).**

---

## Published Figures (66 archived files)

### Group 1 — Primary Pipeline (`results/archive_figures/primary_pipeline/`)

18 PNG + 18 PDF = 36 files  
Figures: Fig01–Fig14, FigSP1–FigSP4  
Generated by: `rainfall_trend_analysis_v4.py`

### Group 2 — Trend Method Comparison (`results/archive_figures/comparison_figures/`)

10 PNG + 10 PDF + 10 SVG = 30 files  
Figures: FigC01–FigC10  
Generated by: `generate_trend_comparison_analysis.py`

**Archive total: 66 files with SHA-256 checksums (`results/archive_figures/checksums.sha256`)**

Full inventory: `FIGURE_INVENTORY.md`

---

## Manuscript Outputs

| File | Location | Status |
|---|---|---|
| `Results_Template.md` | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Synthesis/` | ✅ All placeholders filled |
| `Discussion_Template.md` | same | ✅ All placeholders filled |
| 7 CSV manuscript tables | `results/final_N33_v5/Trend_Method_Comparison/Tables/` | ✅ Complete |

---

## Documentation Files (Release v1.0)

| Document | Description |
|---|---|
| `CLAUDE.md` | Project instructions and workflow reference |
| `README.md` | Repository title and version note |
| `CHANGELOG.md` | Version history |
| `DATA_DICTIONARY.md` | Field-level documentation for all pipeline outputs |
| `FIGURE_INVENTORY.md` | Complete figure archive inventory |
| `TECHNICAL_DEBT_REGISTER.md` | Classified open issues (M-1 to M-4, L-1 to L-5) |
| `RELEASE_CERTIFICATION_v1.0.md` | Final release decision |
| `RELEASE_MANIFEST.md` | This document |
| `REPRODUCIBILITY_FINAL_CHECK.md` | Clean-environment verification |
| `FINAL_RELEASE_AUDIT.md` | Post-remediation audit (0 blocking, 0 high) |
| `RELEASE_READINESS_REPORT.md` | Pre-remediation issue identification |
| `REPRODUCIBILITY_AUDIT.md` | Full reproducibility audit |
| `PIPELINE_VALIDATION_REPORT.md` | End-to-end validation |
| `DISCUSSION_TEMPLATE_VALIDATION.md` | H-3 remediation evidence |
| `results/archive_figures/FIGURE_ARCHIVE_REPORT.md` | Figure archive provenance |

---

## RELEASE_v1.0/ Package Structure

```
RELEASE_v1.0/
├── README.md           — Release overview and quick reproduction guide
├── code/               — Reference to primary scripts (see repo root)
├── data/               — Reference to raw inputs (see repo root)
├── results/            — Reference to published results (see results/)
├── figures/            — Reference to figure archive (see results/archive_figures/)
└── docs/               — Reference to audit documents (see repo root)
```

---

## Remediation History

| Commit | Changes | Issue(s) |
|---|---|---|
| `ede43b2` | H-1: 66 figures archived; H-2: CF/n_eff from S2; H-3: all placeholders filled | H-1, H-2, H-3 |
| `243db96` | RELEASE_READINESS_REPORT.md | Pre-audit |
| `f6544d7` | PIPELINE_VALIDATION_REPORT.md | Validation |
| `cd1921d` | requirements.txt + hardcoded path removal | Reproducibility |
| `e486461` | REPRODUCIBILITY_AUDIT.md | Audit |

---

*Manifest generated at release freeze. All counts verified against committed files.*
