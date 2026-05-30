# MANUSCRIPT PACKAGE CHECKLIST

**Manuscript title:** Comparative Evaluation of Mann-Kendall Trend Detection Methods for Monsoon Rainfall — Phetchaburi–Prachuap Khiri Khan River Basin, Thailand, 1981–2014

---

## STATUS CHECKLIST

| Item | Status |
|------|--------|
| Manuscript templates populated (`Results_Template.md`, `Discussion_Template.md`) | DONE |
| All figures QA approved | DONE (`FIGURE_QA_REPORT.md`) |
| All tables traceable to committed workbooks | DONE |
| TIFF figures for journal submission | PENDING — regenerate locally; see M-3 in `TECHNICAL_DEBT_REGISTER.md` |
| Journal cover letter draft | NOT STARTED |
| Author contribution statements | NOT STARTED |
| Conflict of interest statement | NOT STARTED |
| Data availability statement | NOT STARTED |
| Ethics statement | NOT STARTED |

---

## §3 STUDY AREA AND DATA

**Data source:** `Observed_Rain_daily_198101_201412_Prachuap_Khiri_Khan.csv`

| Element | Item | Notes |
|---------|------|-------|
| Figure | FigSP1 — `Fig_SpatialStation.png/.pdf` | Station network map |
| Tables | None | Narrative description only |

---

## §4 RESULTS

### §4.1 Descriptive Statistics and Climatology

| Element | Item | Source |
|---------|------|--------|
| Figure | Fig07 — `Fig7_MonthlyClimatology.png/.pdf` | Monthly mean rainfall climatology |
| Figure | Fig01 — `Fig1_AnnualTimeSeries.png/.pdf` | Annual rainfall time series per station |
| Figure | Fig02 — `Fig2_WetDryTimeSeries.png/.pdf` | Regional and per-station wet/dry season time series |
| Table | Descriptive Statistics (S5 sheet) | `Output_TrendV4_..._Results.xlsx`, sheet S5 |

### §4.2 Autocorrelation and MMK Correction

| Element | Item | Source |
|---------|------|--------|
| Figure | Fig06 — `Fig6_Autocorrelation.png/.pdf` | Lag-1 autocorrelation per station, regional ACF |
| Figure | Fig12 — `Fig12_ACF_Diagnostics.png/.pdf` | Per-station ACF lags 1–10 |
| Figure | FigC06 — `Figure_06_CorrectionFactor_Distribution.png/.pdf/.svg` | CF distribution per station |
| Figure | FigC07 — `Figure_07_nEff_Distribution.png/.pdf/.svg` | n_eff vs actual N |
| Table | Table_M3 — `Table_M3_Correction_Factor_Impact.csv/.xlsx` | CF impact per station (n_eff, CF, ΔZ) |
| Table | Table_M6 — `Table_M6_Top_AC_Affected_Stations.csv/.xlsx` | Top autocorrelation-affected stations |
| Workbook | `Output_TrendV4_..._Results.xlsx`, sheet S2 | Modified MK sheet for CF/n_eff |

### §4.3 Detected Trends by Method

| Element | Item | Source |
|---------|------|--------|
| Figure | Fig03 — `Fig3_SenSlope_AllScales.png/.pdf` | Sen's slope bar chart all scales |
| Figure | Fig05 — `Fig5_Significance_Heatmap.png/.pdf` | Z-statistic heatmap MK and MMK |
| Figure | FigC01 — `Figure_01_Agreement_Heatmap.png/.pdf/.svg` | Agreement heatmap all methods × 36 combinations |
| Figure | FigC09 — `Figure_09_Significance_Transition_Matrix.png/.pdf/.svg` | MK→alternative transition matrices |
| Table | Table_M1 — `Table_M1_Method_Agreement.csv/.xlsx` | Method agreement matrix (MK vs each alternative, 36 combinations) |
| Table | Table_M2 — `Table_M2_Significance_Transitions.csv/.xlsx` | Significance transitions MK→MMK/PW/TFPW |
| Workbook | `Trend_Method_Comparison_Master.xlsx` | 36×37 Master DB (all methods all stations) |
| Workbook | `Output_TrendV4_..._Results.xlsx`, sheet S7 | 4-Method Comparison |

### §4.4 Method Comparison

| Element | Item | Source |
|---------|------|--------|
| Figure | Fig04 — `Fig4_MK_vs_MMK_Comparison.png/.pdf` | MK vs MMK Z-scatter, p-scatter, ΔZ, agreement heatmap |
| Figure | Fig10 — `Fig10_ZComparisonMatrix.png/.pdf` | Z-statistic heatmap 4 methods |
| Figure | Fig11 — `Fig11_MethodComparison.png/.pdf` | Z-scatter 3 alternative methods vs MK |
| Figure | FigC02 — `Figure_02_MK_vs_MMK_Scatter.png/.pdf/.svg` | Z-scatter MK vs MMK annotated |
| Figure | FigC03 — `Figure_03_MK_vs_PW_Scatter.png/.pdf/.svg` | Z-scatter MK vs PW-MK |
| Figure | FigC04 — `Figure_04_MK_vs_TFPW_Scatter.png/.pdf/.svg` | Z-scatter MK vs TFPW-MK |
| Figure | FigC05 — `Figure_05_DeltaZ_Boxplots.png/.pdf/.svg` | ΔZ distribution boxplots by scale |
| Figure | FigC10 — `Figure_10_Method_Ranking_Summary.png/.pdf/.svg` | Method ranking summary 4 panels |
| Table | Table_M7 — `Table_M7_Method_Ranking_Summary.csv/.xlsx` | Method ranking by sensitivity and agreement (cited in §5.5) |
| Workbook | `Trend_Method_Comparison_Master.xlsx` | 36×37 Master DB |

### §4.5 Field Significance

| Element | Item | Source |
|---------|------|--------|
| Figure | Fig13 — `Fig13_FieldSignificance.png/.pdf` | Field significance fraction bar + summary table |
| Figure | FigSP3 — `Fig_SpatialFieldSig.png/.pdf` | \|Z\| magnitude maps + Walker/LC-MC bar |
| Figure | FigC08 — `Figure_08_Field_Significance_Comparison.png/.pdf/.svg` | Field significance N significant by method |
| Table | Table_M5 — `Table_M5_Field_Significance_Comparison.csv/.xlsx` | Walker and LC-MC p-values by scale |
| Workbook | `Output_TrendV4_..._Results.xlsx`, sheet S8 | Field Significance |

### §4.6 Spatial Distribution of Trends

| Element | Item | Source |
|---------|------|--------|
| Figure | Fig08 — `Fig8_SpatialTrend_Summary.png/.pdf` | Index-based spatial trend summary 4-panel |
| Figure | Fig14 — `Fig14_SpatialMaps.png/.pdf` | Geographic MMK Sen's slope maps Annual/Wet/Dry |
| Figure | FigSP2 — `Fig_SpatialMethods.png/.pdf` | 4×3 geographic grid 4 methods × 3 scales |
| Figure | FigSP4 — `Fig_SpatialFull.png/.pdf` | Comprehensive 7-panel spatial overview |
| Workbook | `Trend_Method_Comparison_Master.xlsx` | 36×37 Master DB |
| Workbook | `Output_TrendV4_..._Results.xlsx`, sheet S7 | 4-Method Comparison |

---

## §5 DISCUSSION

### §5.1 Why Method Choice Matters

| Element | Item | Source |
|---------|------|--------|
| Figure | Fig06 — `Fig6_Autocorrelation.png/.pdf` | Autocorrelation context |
| Figure | FigC06 — `Figure_06_CorrectionFactor_Distribution.png/.pdf/.svg` | CF distribution |
| Table | Table_M3 — `Table_M3_Correction_Factor_Impact.csv/.xlsx` | CF impact |
| Template | `Discussion_Template.md` §5.1 | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Synthesis/` |

### §5.2 MMK vs PW-MK

| Element | Item | Source |
|---------|------|--------|
| Figure | Fig04 — `Fig4_MK_vs_MMK_Comparison.png/.pdf` | MK vs MMK comparison |
| Figure | FigC02 — `Figure_02_MK_vs_MMK_Scatter.png/.pdf/.svg` | Z-scatter MK vs MMK |
| Figure | FigC03 — `Figure_03_MK_vs_PW_Scatter.png/.pdf/.svg` | Z-scatter MK vs PW-MK |
| Template | `Discussion_Template.md` §5.2 | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Synthesis/` |

### §5.3 TFPW-MK Liberal Bias

| Element | Item | Source |
|---------|------|--------|
| Figure | FigC04 — `Figure_04_MK_vs_TFPW_Scatter.png/.pdf/.svg` | Z-scatter MK vs TFPW-MK |
| Figure | FigC09 — `Figure_09_Significance_Transition_Matrix.png/.pdf/.svg` | Significance transition matrix |
| Template | `Discussion_Template.md` §5.3 | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Synthesis/` |

### §5.4 Scale-Specific Sensitivity

| Element | Item | Source |
|---------|------|--------|
| Figure | Fig05 — `Fig5_Significance_Heatmap.png/.pdf` | Z-statistic heatmap |
| Figure | FigC01 — `Figure_01_Agreement_Heatmap.png/.pdf/.svg` | Agreement heatmap |
| Template | `Discussion_Template.md` §5.4 | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Synthesis/` |

### §5.5 Recommendation

| Element | Item | Source |
|---------|------|--------|
| Table | Table_M4 — `Table_M4_Station_Disagreement_Inventory.csv/.xlsx` | Stations with method-dependent conclusions |
| Table | Table_M7 — `Table_M7_Method_Ranking_Summary.csv/.xlsx` | Method ranking summary |
| Template | `Discussion_Template.md` §5.5 | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Synthesis/` |

---

## §6 PRACTICAL IMPLICATIONS

| Element | Item | Notes |
|---------|------|-------|
| Table | Table_M4 — `Table_M4_Station_Disagreement_Inventory.csv/.xlsx` | Which stations have method-dependent conclusions |
| Table | Table_M5 — `Table_M5_Field_Significance_Comparison.csv/.xlsx` | Dry season field significance |
| Workbook | `Output_TrendV4_..._Results.xlsx`, sheet S8 | Field Significance |

---

## §7 LIMITATIONS

| Limitation | Evidence | Reference |
|------------|----------|-----------|
| Shapefile absent; no Q1 journal-standard maps auto-generated | `TECHNICAL_DEBT_REGISTER.md` item M-1 | — |
| `calval_split.py` absent; no cross-validation of spatial interpolation | `TECHNICAL_DEBT_REGISTER.md` item L-5 | — |

---

## SUPPLEMENTARY MATERIALS

### Additional Workbooks

| Filename | Description |
|----------|-------------|
| `Trend_Method_Comparison_Master.xlsx` | 36×37 Master DB |
| `Table_M1_Method_Agreement.xlsx` | Method agreement |
| `Table_M2_Significance_Transitions.xlsx` | Significance transitions |
| `Table_M3_Correction_Factor_Impact.xlsx` | CF impact |
| `Table_M4_Station_Disagreement_Inventory.xlsx` | Station disagreement |
| `Table_M5_Field_Significance_Comparison.xlsx` | Field significance |
| `Table_M6_Top_AC_Affected_Stations.xlsx` | Top AC-affected stations |
| `Table_M7_Method_Ranking_Summary.xlsx` | Method ranking |
| `MK_Analysis.xlsx` | MK method-level analysis |
| `MMK_Analysis.xlsx` | MMK method-level analysis |
| `MMK_vs_MK_Comparison.xlsx` | MMK vs MK comparison |
| `PW_MK_Analysis.xlsx` | PW-MK method-level analysis |
| `PW_MK_vs_MK_Comparison.xlsx` | PW-MK vs MK comparison |
| `TFPW_MK_Analysis.xlsx` | TFPW-MK method-level analysis |
| `TFPW_MK_vs_MK_Comparison.xlsx` | TFPW-MK vs MK comparison |

### Additional Figures

| Figure | Description |
|--------|-------------|
| Fig09 — `Fig9_TaylorDiagram.png/.pdf` | Taylor diagram station vs regional reference |
| Fig12 — `Fig12_ACF_Diagnostics.png/.pdf` | Per-station ACF diagnostics lags 1–10 |
| FigC02 — `Figure_02_MK_vs_MMK_Scatter.png/.pdf/.svg` | Z-scatter MK vs MMK annotated |
| FigC03 — `Figure_03_MK_vs_PW_Scatter.png/.pdf/.svg` | Z-scatter MK vs PW-MK |
| FigC04 — `Figure_04_MK_vs_TFPW_Scatter.png/.pdf/.svg` | Z-scatter MK vs TFPW-MK |
| FigC05 — `Figure_05_DeltaZ_Boxplots.png/.pdf/.svg` | ΔZ distribution boxplots by scale |
| FigC06 — `Figure_06_CorrectionFactor_Distribution.png/.pdf/.svg` | CF distribution per station |
| FigC07 — `Figure_07_nEff_Distribution.png/.pdf/.svg` | n_eff vs actual N |
| FigC08 — `Figure_08_Field_Significance_Comparison.png/.pdf/.svg` | Field significance N significant by method |
| FigC09 — `Figure_09_Significance_Transition_Matrix.png/.pdf/.svg` | MK→alternative transition matrices |
| FigC10 — `Figure_10_Method_Ranking_Summary.png/.pdf/.svg` | Method ranking summary 4 panels |

### Validation and QA Reports

| Filename | Description |
|----------|-------------|
| `PIPELINE_VALIDATION_REPORT.md` | End-to-end pipeline execution validation |
| `REPRODUCIBILITY_FINAL_CHECK.md` | Clean-environment reproducibility verification |
| `FIGURE_QA_REPORT.md` | All 38 figures PASS |

### Data Documentation

| Filename | Description |
|----------|-------------|
| `DATA_DICTIONARY.md` | Field-level documentation for all pipeline outputs |
