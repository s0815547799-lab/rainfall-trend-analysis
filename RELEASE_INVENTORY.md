# RELEASE INVENTORY

**Project:** Rainfall Trend Analysis — Phetchaburi–Prachuap Khiri Khan River Basin, Western Thailand (1981–2014)
**Release:** v1.0.0
**Commit:** 471bdc3
**Branch:** claude/hydroclimatology-claude-md-kudre

---

## A. PUBLICATION FIGURES (38 total)

### Primary Pipeline Figures (18 figures)

Location: `results/archive_figures/primary_pipeline/`

| ID | Filename | Format | Source Script | Description | Manuscript Section |
|----|----------|--------|---------------|-------------|-------------------|
| Fig01 | `Fig1_AnnualTimeSeries.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | Annual rainfall time series per station with MMK trend | §4.1 Results |
| Fig02 | `Fig2_WetDryTimeSeries.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | Regional and per-station wet/dry season time series | §4.1 Results |
| Fig03 | `Fig3_SenSlope_AllScales.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | Sen's slope bar chart all scales | §4.3 Results |
| Fig04 | `Fig4_MK_vs_MMK_Comparison.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | MK vs MMK Z-scatter, p-scatter, ΔZ, agreement heatmap | §4.4 Results |
| Fig05 | `Fig5_Significance_Heatmap.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | Z-statistic heatmap MK and MMK | §4.3 Results |
| Fig06 | `Fig6_Autocorrelation.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | Lag-1 autocorrelation per station, regional ACF | §4.2 Results |
| Fig07 | `Fig7_MonthlyClimatology.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | Monthly mean rainfall climatology | §4.1 Results |
| Fig08 | `Fig8_SpatialTrend_Summary.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | Index-based spatial trend summary 4-panel | §4.6 Results |
| Fig09 | `Fig9_TaylorDiagram.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | Taylor diagram station vs regional reference | Supplement |
| Fig10 | `Fig10_ZComparisonMatrix.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | Z-statistic heatmap 4 methods | §4.4 Results |
| Fig11 | `Fig11_MethodComparison.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | Z-scatter 3 alternative methods vs MK | §4.4 Results |
| Fig12 | `Fig12_ACF_Diagnostics.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | Per-station ACF lags 1–10 | Supplement |
| Fig13 | `Fig13_FieldSignificance.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | Field significance fraction bar + summary table | §4.5 Results |
| Fig14 | `Fig14_SpatialMaps.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | Geographic MMK Sen's slope maps Annual/Wet/Dry | §4.6 Results |
| FigSP1 | `Fig_SpatialStation.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | Station network map | §3 Study Area |
| FigSP2 | `Fig_SpatialMethods.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | 4×3 geographic grid 4 methods × 3 scales | §4.6 Results |
| FigSP3 | `Fig_SpatialFieldSig.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | \|Z\| magnitude maps + Walker/LC-MC bar | §4.5 Results |
| FigSP4 | `Fig_SpatialFull.png/.pdf` | PNG+PDF | `rainfall_trend_analysis_v4.py` | Comprehensive 7-panel spatial overview | §4.6 Results |

### Comparison Figures (10 figures)

Location: `results/archive_figures/comparison_figures/`
Source script: `generate_trend_comparison_analysis.py` (all figures in this section)

| ID | Filename | Format | Description | Manuscript Section |
|----|----------|--------|-------------|-------------------|
| FigC01 | `Figure_01_Agreement_Heatmap.png/.pdf/.svg` | PNG+PDF+SVG | Agreement heatmap all methods × 36 combinations | §4.4 Results |
| FigC02 | `Figure_02_MK_vs_MMK_Scatter.png/.pdf/.svg` | PNG+PDF+SVG | Z-scatter MK vs MMK annotated | §4.4 Results |
| FigC03 | `Figure_03_MK_vs_PW_Scatter.png/.pdf/.svg` | PNG+PDF+SVG | Z-scatter MK vs PW-MK | §4.4 Results |
| FigC04 | `Figure_04_MK_vs_TFPW_Scatter.png/.pdf/.svg` | PNG+PDF+SVG | Z-scatter MK vs TFPW-MK | §4.4 Results |
| FigC05 | `Figure_05_DeltaZ_Boxplots.png/.pdf/.svg` | PNG+PDF+SVG | ΔZ distribution boxplots by scale | §4.4 Results |
| FigC06 | `Figure_06_CorrectionFactor_Distribution.png/.pdf/.svg` | PNG+PDF+SVG | CF distribution per station | §4.2 Results |
| FigC07 | `Figure_07_nEff_Distribution.png/.pdf/.svg` | PNG+PDF+SVG | n_eff vs actual N | §4.2 Results |
| FigC08 | `Figure_08_Field_Significance_Comparison.png/.pdf/.svg` | PNG+PDF+SVG | Field significance N significant by method | §4.5 Results |
| FigC09 | `Figure_09_Significance_Transition_Matrix.png/.pdf/.svg` | PNG+PDF+SVG | MK→alternative transition matrices | §4.3 Results |
| FigC10 | `Figure_10_Method_Ranking_Summary.png/.pdf/.svg` | PNG+PDF+SVG | Method ranking summary 4 panels | §4.4 Results |

---

## B. MANUSCRIPT TABLES (7 tables)

Location: `results/final_N33_v5/Trend_Method_Comparison/Tables/`
Format: CSV + XLSX for each table.

| Table ID | Filename | Description | Manuscript Section |
|----------|----------|-------------|-------------------|
| Table_M1 | `Table_M1_Method_Agreement.csv/.xlsx` | Method agreement matrix (MK vs each alternative, 36 combinations) | §4.3 Results |
| Table_M2 | `Table_M2_Significance_Transitions.csv/.xlsx` | Significance transitions MK→MMK/PW/TFPW | §4.3 Results |
| Table_M3 | `Table_M3_Correction_Factor_Impact.csv/.xlsx` | CF impact per station (n_eff, CF, ΔZ) | §4.2 Results |
| Table_M4 | `Table_M4_Station_Disagreement_Inventory.csv/.xlsx` | Stations where method choice changes conclusion | §5.5 Discussion |
| Table_M5 | `Table_M5_Field_Significance_Comparison.csv/.xlsx` | Walker and LC-MC p-values by scale | §4.5 Results |
| Table_M6 | `Table_M6_Top_AC_Affected_Stations.csv/.xlsx` | Top autocorrelation-affected stations | §4.2 Results |
| Table_M7 | `Table_M7_Method_Ranking_Summary.csv/.xlsx` | Method ranking by sensitivity and agreement | §5.5 Discussion |

---

## C. EXCEL WORKBOOKS (27 total)

### Primary Results Workbook (1 workbook)

| ID | Filename | Location | Sheet Contents | Notes |
|----|----------|----------|----------------|-------|
| WB1 | `Output_TrendV4_..._Results.xlsx` | `results/final_N33/excel/` | S1 Standard MK; S2 Modified MK (H&R98); S3 MK vs MMK Comparison; S4 Sen's Slope; S5 Descriptive Statistics; S6 Methods & References; S7 4-Method Comparison; S8 Field Significance; S9 Dry Season Validation | Primary source |

### Trend Method Comparison Workbooks (8 workbooks)

Location: `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/`

| Filename | Description |
|----------|-------------|
| `Trend_Method_Comparison_Master.xlsx` | 36×37 Master DB (all methods all stations) |
| `Trend_Method_Comparison_All_vs_MK.xlsx` | All alternative methods vs MK |
| `Trend_Method_Comparison_Tables.xlsx` | Formatted manuscript tables |
| `Disagreement_Stations.xlsx` | Station-level disagreement analysis |
| `Final_Methodological_Assessment.xlsx` | Final methodological assessment |
| `Reviewer_Summary.xlsx` | Reviewer-oriented summary |
| `SenSlope_Comparison.xlsx` | Sen's slope method comparison |
| `TFPW_Audit.xlsx` | TFPW-MK audit |

### Method-Level Workbooks (7 workbooks)

| Filename | Location |
|----------|----------|
| `MK_Analysis.xlsx` | `Excel/MK_Analysis/` |
| `MMK_Analysis.xlsx` | `Excel/MMK_Analysis/` |
| `MMK_vs_MK_Comparison.xlsx` | `Excel/MMK_Analysis/` |
| `PW_MK_Analysis.xlsx` | `Excel/PW_MK_Analysis/` |
| `PW_MK_vs_MK_Comparison.xlsx` | `Excel/PW_MK_Analysis/` |
| `TFPW_MK_Analysis.xlsx` | `Excel/TFPW_MK_Analysis/` |
| `TFPW_MK_vs_MK_Comparison.xlsx` | `Excel/TFPW_MK_Analysis/` |

### Table Workbooks (7 workbooks)

Location: `Tables/`

| Filename |
|----------|
| `Table_M1_Method_Agreement.xlsx` |
| `Table_M2_Significance_Transitions.xlsx` |
| `Table_M3_Correction_Factor_Impact.xlsx` |
| `Table_M4_Station_Disagreement_Inventory.xlsx` |
| `Table_M5_Field_Significance_Comparison.xlsx` |
| `Table_M6_Top_AC_Affected_Stations.xlsx` |
| `Table_M7_Method_Ranking_Summary.xlsx` |

### Other Workbooks (4 workbooks)

| Filename | Location | Description |
|----------|----------|-------------|
| `Trend_Method_Comparison_Q1.xlsx` | `results/final_N33_v5/` | Q1 journal comparison |
| `Interpolation_Comparison.xlsx` | `results/final_N33_v5/validation/` | Interpolation comparison |
| `LOOCV.xlsx` | `results/final_N33_v5/validation/` | Leave-one-out cross-validation |
| `Workbook_Inventory_Report.xlsx` | `results/` | Workbook inventory |

---

## D. MANUSCRIPT TEMPLATES (2 files)

Location: `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Synthesis/`

| Filename | Status | Manuscript Section |
|----------|--------|--------------------|
| `Results_Template.md` | All placeholders filled | §4 Results |
| `Discussion_Template.md` | All placeholders filled | §5 Discussion |

---

## E. RELEASE AND CERTIFICATION DOCUMENTS

| Filename | Location | Description |
|----------|----------|-------------|
| `RELEASE_CERTIFICATION_v1.0.md` | Root | RELEASE APPROVED WITH TECHNICAL DEBT |
| `RELEASE_MANIFEST.md` | Root | Full inventory at commit 471bdc3 |
| `FINAL_RELEASE_AUDIT.md` | Root | Post-remediation audit (0 blocking, 0 high) |
| `FIGURE_QA_REPORT.md` | Root | All 38 figures PASS |
| `RELEASE_v1.0/README.md` | `RELEASE_v1.0/` | Release package overview |

---

## F. VALIDATION DOCUMENTS

| Filename | Location | Description |
|----------|----------|-------------|
| `PIPELINE_VALIDATION_REPORT.md` | Root | End-to-end pipeline execution validation |
| `REPRODUCIBILITY_FINAL_CHECK.md` | Root | Clean-environment reproducibility verification |
| `REPRODUCIBILITY_AUDIT.md` | Root | Full reproducibility audit |

---

## G. AUDIT DOCUMENTS

| Filename | Location | Description |
|----------|----------|-------------|
| `RELEASE_READINESS_REPORT.md` | Root | Pre-remediation issue identification (H-1/H-2/H-3) |
| `DISCUSSION_TEMPLATE_VALIDATION.md` | Root | H-3 placeholder resolution evidence |

---

## H. DOCUMENTATION

| Filename | Location | Description |
|----------|----------|-------------|
| `DATA_DICTIONARY.md` | Root | Field-level documentation for all pipeline outputs |
| `FIGURE_INVENTORY.md` | Root | Complete 38-figure archive inventory |
| `TECHNICAL_DEBT_REGISTER.md` | Root | 9 open items classified |
| `CLAUDE.md` | Root | Project instructions and workflow reference |
| `CHANGELOG.md` | Root | Version history |

---

## I. RAW INPUTS

| Filename | Location | Description |
|----------|----------|-------------|
| `Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv` | Root | Primary daily rainfall data, 12 stations 1981–2014 |
| `station_coordinates.csv` | Root | WGS84 coordinates, 128 stations |

---

## J. ARCHIVE METADATA

Location: `results/archive_figures/`

| Filename | Description |
|----------|-------------|
| `checksums.sha256` | 66 SHA-256 entries, all verified OK |
| `figure_manifest.csv` | 66-row figure manifest |
| `FIGURE_ARCHIVE_REPORT.md` | Archive provenance report |
